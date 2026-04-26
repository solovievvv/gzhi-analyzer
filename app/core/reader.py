"""
Чтение xlsx и вычисление дебита/кредита по листам.
"""
from typing import Optional
import openpyxl

from app.core.models import SheetResult, AnalysisResult
from app.core.filters import is_deposit_transfer


# ── Поиск заголовков ─────────────────────────────────────────────────────────

def find_debit_credit_columns(sheet) -> tuple[Optional[int], Optional[int], Optional[int]]:
    """
    Возвращает (header_row, debit_col, credit_col) — всё 1-based.
    Берём ПОСЛЕДНЮЮ строку где есть оба заголовка: сначала идут итоговые
    таблицы, потом детальные — нам нужна детальная.
    """
    best = (None, None, None)
    for row in sheet.iter_rows():
        d_col = c_col = None
        for cell in row:
            if not (cell.value and isinstance(cell.value, str)):
                continue
            v = cell.value.lower()
            if ("дебит" in v or "дебет" in v) and d_col is None:
                d_col = cell.column
            if "кредит" in v and c_col is None:
                c_col = cell.column
        if d_col and c_col:
            best = (row[0].row, d_col, c_col)
    return best


# ── Вспомогательные функции ───────────────────────────────────────────────────

def is_column_numbering_row(debit_raw, credit_raw) -> bool:
    """Пропускаем строку нумерации столбцов (напр. '13', '14')."""
    def small_int(v) -> bool:
        if isinstance(v, (int, float)):
            return float(v).is_integer() and 1 <= v <= 50
        if isinstance(v, str):
            s = v.strip()
            return s.isdigit() and 1 <= int(s) <= 50
        return False
    return small_int(debit_raw) and small_int(credit_raw)


def is_label(value) -> bool:
    """True если в числовой колонке стоит текстовая метка (Итого, Всего…)."""
    if value is None or isinstance(value, (int, float)):
        return False
    if not isinstance(value, str):
        return False
    s = value.strip()
    if not s or s in ("-", "—"):
        return False
    cleaned = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    if "-" in cleaned:
        parts = cleaned.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return False
    try:
        float(cleaned)
        return False
    except ValueError:
        return True


def to_float(value) -> Optional[float]:
    """Конвертация значения ячейки в float с поддержкой всех форматов."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s in ("-", "—"):
            return None
        # Банковский формат: "858742-03" → 858742.03
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return float(f"{parts[0]}.{parts[1]}")
            return None
        cleaned = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def get_description(sheet, row_idx: int, start_col: int) -> str:
    """Собирает текст пояснения из всех ячеек правее колонок дебит/кредит."""
    parts = []
    for col in range(start_col, sheet.max_column + 1):
        val = sheet.cell(row=row_idx, column=col).value
        if val is not None and isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return " ".join(parts)


# ── Обработка листа и файла ───────────────────────────────────────────────────

def process_sheet(sheet) -> SheetResult:
    result = SheetResult(sheet_name=sheet.title)

    header_row, debit_col, credit_col = find_debit_credit_columns(sheet)
    if header_row is None:
        result.error = "Столбцы 'Дебит' и 'Кредит' не найдены"
        return result

    desc_start_col = max(debit_col, credit_col) + 1
    data_start = header_row + 1

    # Пропустить строку нумерации столбцов если она есть
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

        result.debit += d or 0.0
        result.credit += c or 0.0

    return result


def process_file(filepath: str) -> AnalysisResult:
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
    except Exception as e:
        raise RuntimeError(f"Не удалось открыть файл: {e}")

    result = AnalysisResult(filepath=filepath)
    for name in wb.sheetnames:
        result.sheets.append(process_sheet(wb[name]))
    return result
