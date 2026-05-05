"""
Чтение xlsx и извлечение транзакций по листам.
"""
from typing import Optional
import openpyxl

from app.core.models import (
    TransactionRow, SheetResult, AnalysisResult, FolderResult
)
from app.core.filters import is_deposit_transfer
from app.core.date_parser import parse_date
from app.core.deduplicator import deduplicate_folder


# ── Поиск заголовков ─────────────────────────────────────────────────────────

def find_columns(sheet) -> tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    Возвращает (header_row, date_col, debit_col, credit_col).
    Среди кандидатов выбираем таблицу с наибольшим числом строк
    с валидными финансовыми значениями (0..10^12).
    Это отсеивает сводные таблицы и таблицы где в дебит/кредит попали даты.
    """
    candidates = []
    for row in sheet.iter_rows():
        d_col = c_col = None
        for cell in row:
            if not (cell.value and isinstance(cell.value, str)):
                continue
            v = cell.value.lower()
            if ('дебит' in v or 'дебет' in v) and d_col is None:
                d_col = cell.column
            if 'кредит' in v and c_col is None:
                c_col = cell.column
        if d_col and c_col:
            candidates.append((row[0].row, d_col, c_col))

    if not candidates:
        return None, None, None, None

    best_hrow, best_debit, best_credit = _pick_best_candidate(sheet, candidates)

    date_col = _find_date_col_in_window(sheet, best_hrow, window=3)
    if date_col is None:
        date_col = _find_date_col_by_content(sheet, best_hrow, best_debit, best_credit)

    return best_hrow, date_col, best_debit, best_credit


def _is_valid_amount(value) -> bool:
    """True если значение похоже на реальную финансовую сумму (0..10^12)."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return 0 <= abs(value) <= 1e12
    if isinstance(value, str):
        v = to_float(value)
        if v is not None:
            return 0 <= abs(v) <= 1e12
    return False


def _pick_best_candidate(sheet, candidates: list) -> tuple:
    """
    Из кандидатов выбирает тот, под которым максимум строк
    с валидными финансовыми значениями.
    Таблицы где в дебит/кредит попали даты (3e+19) или коды — отсеиваются.
    """
    best = candidates[0]
    best_count = 0

    for hrow, d_col, c_col in candidates:
        count = 0
        for r in range(hrow + 1, sheet.max_row + 1):
            v_d = sheet.cell(row=r, column=d_col).value
            v_c = sheet.cell(row=r, column=c_col).value
            if _is_valid_amount(v_d) or _is_valid_amount(v_c):
                count += 1
            elif v_d is None and v_c is None and count > 0:
                empty_streak = sum(
                    1 for rr in range(r, min(r + 5, sheet.max_row + 1))
                    if sheet.cell(row=rr, column=d_col).value is None
                    and sheet.cell(row=rr, column=c_col).value is None
                )
                if empty_streak >= 5:
                    break
        if count > best_count:
            best_count = count
            best = (hrow, d_col, c_col)

    return best


def _find_date_col_in_window(sheet, header_row: int, window: int) -> Optional[int]:
    start = max(1, header_row - window)
    end = min(sheet.max_row, header_row + window)
    for r in range(start, end + 1):
        for cell in sheet[r]:
            if cell.value and isinstance(cell.value, str):
                if 'дата' in cell.value.lower():
                    return cell.column
    return None


def _find_date_col_by_content(sheet, header_row: int,
                               debit_col: int, credit_col: int) -> Optional[int]:
    data_start = header_row + 1
    data_end = min(sheet.max_row, header_row + 35)
    left_bound = min(debit_col, credit_col)

    date_counts: dict[int, int] = {}
    total_counts: dict[int, int] = {}

    for r in range(data_start, data_end + 1):
        for c in range(1, left_bound):
            val = sheet.cell(row=r, column=c).value
            if val is None:
                continue
            total_counts[c] = total_counts.get(c, 0) + 1
            if parse_date(val) is not None:
                date_counts[c] = date_counts.get(c, 0) + 1

    best_col = None
    best_ratio = 0.5

    for col, count in date_counts.items():
        total = total_counts.get(col, 0)
        if total == 0:
            continue
        ratio = count / total
        if ratio > best_ratio:
            best_ratio = ratio
            best_col = col

    return best_col


# ── Вспомогательные функции ───────────────────────────────────────────────────

def is_column_numbering_row(debit_raw, credit_raw) -> bool:
    def small_int(v) -> bool:
        if isinstance(v, (int, float)):
            return float(v).is_integer() and 1 <= v <= 50
        if isinstance(v, str):
            s = v.strip()
            return s.isdigit() and 1 <= int(s) <= 50
        return False
    return small_int(debit_raw) and small_int(credit_raw)


def is_label(value) -> bool:
    if value is None or isinstance(value, (int, float)):
        return False
    if not isinstance(value, str):
        return False
    s = value.strip()
    if not s or s in ('-', '—'):
        return False
    cleaned = s.replace('\xa0', '').replace(' ', '').replace(',', '.')
    if '-' in cleaned:
        parts = cleaned.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return False
    try:
        float(cleaned)
        return False
    except ValueError:
        return True


def to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s in ('-', '—'):
            return None
        if '-' in s:
            parts = s.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return float(f"{parts[0]}.{parts[1]}")
            return None
        cleaned = s.replace('\xa0', '').replace(' ', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def get_description(sheet, row_idx: int, start_col: int) -> str:
    parts = []
    for col in range(start_col, sheet.max_column + 1):
        val = sheet.cell(row=row_idx, column=col).value
        if val is not None and isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return ' '.join(parts)


# ── Обработка листа ───────────────────────────────────────────────────────────

def process_sheet(sheet) -> SheetResult:
    result = SheetResult(sheet_name=sheet.title)

    header_row, date_col, debit_col, credit_col = find_columns(sheet)
    if header_row is None:
        result.error = "Столбцы 'Дебит' и 'Кредит' не найдены"
        return result

    desc_start_col = max(date_col or 0, debit_col, credit_col) + 1
    data_start = header_row + 1

    if is_column_numbering_row(
        sheet.cell(row=data_start, column=debit_col).value,
        sheet.cell(row=data_start, column=credit_col).value,
    ):
        data_start += 1

    for row_idx in range(data_start, sheet.max_row + 1):
        raw_d = sheet.cell(row=row_idx, column=debit_col).value
        raw_c = sheet.cell(row=row_idx, column=credit_col).value

        if is_label(raw_d) or is_label(raw_c):
            result.skipped_rows += 1
            continue

        d = to_float(raw_d)
        c = to_float(raw_c)

        if d is None and c is None:
            result.skipped_rows += 1
            continue

        description = get_description(sheet, row_idx, desc_start_col)
        if is_deposit_transfer(description):
            result.excluded_rows += 1
            continue

        tx_date = None
        if date_col:
            tx_date = parse_date(sheet.cell(row=row_idx, column=date_col).value)

        result.transactions.append(TransactionRow(
            date=tx_date,
            debit=d or 0.0,
            credit=c or 0.0,
            description=description,
            row_idx=row_idx,
        ))

    return result


# ── Обработка файла и папки ───────────────────────────────────────────────────

def process_file(filepath: str) -> AnalysisResult:
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
    except Exception as e:
        raise RuntimeError(f"Не удалось открыть файл: {e}")

    result = AnalysisResult(filepath=filepath)
    for name in wb.sheetnames:
        result.sheets.append(process_sheet(wb[name]))
    return result


def process_folder(folderpath: str) -> FolderResult:
    import os
    result = FolderResult(folderpath=folderpath)
    xlsx_files = sorted([
        os.path.join(folderpath, f)
        for f in os.listdir(folderpath)
        if f.lower().endswith(('.xlsx', '.xlsm')) and not f.startswith('~$')
    ])
    if not xlsx_files:
        raise RuntimeError("В папке не найдено файлов Excel (.xlsx, .xlsm)")
    for filepath in xlsx_files:
        result.files.append(process_file(filepath))
    deduplicate_folder(result)
    return result
