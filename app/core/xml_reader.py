"""
Чтение банковских выписок в формате SpreadsheetML XML (Ак Барс Банк и др.)

Формат: Excel XML (xmlns urn:schemas-microsoft-com:office:spreadsheet)
Кодировка: windows-1251

Структура документа:
  Row 1-2  — пустые / служебные
  Row 3    — название счёта и организации
  Row 4    — период выписки
  Row 5    — группы заголовков (Реквизиты документа, Сумма операции…)
  Row 6    — подзаголовки ("по дебету", "по кредиту", "Дата совершения операции"…)
  Row 7    — нумерация столбцов
  Row 8..N-1 — транзакции
  Row N    — итоговая строка ("Оборот за период")

Ключевое: пустые ячейки (<Cell/> без <Data>) присутствуют в XML
и должны учитываться при определении позиций столбцов.
"""

import re
import html
from typing import Optional
from datetime import datetime, date as DateType

from app.core.models import TransactionRow, SheetResult, AnalysisResult
from app.core.filters import is_deposit_transfer
from app.core.date_parser import parse_date


# ── Константы ─────────────────────────────────────────────────────────────────

ENCODING = "windows-1251"

_PERIOD_RE = re.compile(
    r"за период с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
    re.IGNORECASE,
)

_COL_DATE    = "дата совершения операции"
_COL_DEBIT   = "по дебету"
_COL_CREDIT  = "по кредиту"
_COL_PURPOSE = "назначение платежа"
_TOTAL_MARKER = "оборот за период"


# ── Низкоуровневый парсер: строки с реальными позициями ──────────────────────

_ROW_RE  = re.compile(r"<Row[^>]*>(.*?)</Row>", re.DOTALL)

# Cell с атрибутом ss:Index (явный пропуск столбцов)
_CELL_RE = re.compile(
    r"<Cell(?:[^>]*\bss:Index=\"(\d+)\")?[^>]*>"
    r"(?:<Data[^>]*>([^<]*)</Data>)?",
    re.DOTALL,
)


def _parse_rows(content: str) -> list[dict[int, str]]:
    """
    Разбирает SpreadsheetML XML и возвращает строки как словари
    {column_index_1based: value}.

    Пустые ячейки (<Cell/>) записываются как '' чтобы не сбивать позиции.
    Если у Cell есть ss:Index — делаем прыжок к этой позиции.
    """
    rows: list[dict[int, str]] = []

    for row_match in _ROW_RE.finditer(content):
        row_xml = row_match.group(1)
        row: dict[int, str] = {}
        col = 1  # SpreadsheetML нумерует с 1

        for cell_match in _CELL_RE.finditer(row_xml):
            idx_attr = cell_match.group(1)
            data_val = cell_match.group(2)

            if idx_attr:
                col = int(idx_attr)

            value = html.unescape(data_val).strip() if data_val else ""
            row[col] = value
            col += 1

        rows.append(row)

    return rows


def _row_values(row: dict[int, str]) -> list[str]:
    """Возвращает значения строки как список, отсортированный по позиции."""
    if not row:
        return []
    return [row.get(i, "") for i in range(1, max(row.keys()) + 1)]


# ── Определение структуры таблицы ────────────────────────────────────────────

class _TableSchema:
    """
    Хранит номера столбцов (1-based) для нужных полей.
    Определяется по строке подзаголовков (Row 6).
    """

    def __init__(self,
                 date_col: Optional[int],
                 debit_col: Optional[int],
                 credit_col: Optional[int],
                 purpose_col: Optional[int]):
        self.date_col    = date_col
        self.debit_col   = debit_col
        self.credit_col  = credit_col
        self.purpose_col = purpose_col

    @property
    def is_valid(self) -> bool:
        return self.debit_col is not None and self.credit_col is not None

    @classmethod
    def from_row(cls, row: dict[int, str]) -> "_TableSchema":
        """Определяет позиции столбцов по словарю {col: value}."""
        date_col = purpose_col = debit_col = credit_col = None
        for col, cell in row.items():
            v = cell.lower()
            if _COL_DATE    in v and date_col    is None: date_col    = col
            if _COL_DEBIT   in v and debit_col   is None: debit_col   = col
            if _COL_CREDIT  in v and credit_col  is None: credit_col  = col
            if _COL_PURPOSE in v and purpose_col is None: purpose_col = col
        return cls(date_col, debit_col, credit_col, purpose_col)


def _find_schema(rows: list[dict[int, str]]) -> tuple[Optional["_TableSchema"], int]:
    """
    Ищет строку подзаголовков содержащую 'по дебету' И 'по кредиту'.
    Объединяет её с предыдущей строкой заголовков (Row 5) чтобы найти
    'Дата совершения операции' и 'Назначение платежа' которые могут быть
    только в верхней строке заголовка.
    """
    for i, row in enumerate(rows):
        row_text = " ".join(row.values()).lower()
        if _COL_DEBIT in row_text and _COL_CREDIT in row_text:
            # Объединяем с предыдущей строкой заголовков
            merged = dict(row)
            if i > 0:
                for col, val in rows[i - 1].items():
                    if col not in merged or not merged[col]:
                        merged[col] = val

            schema = _TableSchema.from_row(merged)
            data_start = i + 1
            # Пропускаем строку нумерации (1,2,3...)
            if data_start < len(rows):
                vals = [v for v in rows[data_start].values() if v]
                if vals and all(v.strip().isdigit() for v in vals):
                    data_start += 1
            return schema, data_start
    return None, 0


# ── Парсинг периода ───────────────────────────────────────────────────────────

def _extract_period(rows: list[dict[int, str]]) -> tuple[Optional[DateType], Optional[DateType]]:
    for row in rows[:6]:
        text = " ".join(row.values())
        m = _PERIOD_RE.search(text)
        if m:
            try:
                d_from = datetime.strptime(m.group(1), "%d.%m.%Y").date()
                d_to   = datetime.strptime(m.group(2), "%d.%m.%Y").date()
                return d_from, d_to
            except ValueError:
                pass
    return None, None


# ── Парсинг строки транзакции ─────────────────────────────────────────────────

def _is_total_row(row: dict[int, str]) -> bool:
    vals = list(row.values())
    return bool(vals) and _TOTAL_MARKER in vals[0].lower()


def _to_float(s: str) -> float:
    if not s:
        return 0.0
    cleaned = s.replace("\xa0", "").replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_transaction(row: dict[int, str],
                       schema: "_TableSchema") -> Optional[TransactionRow]:
    """Конвертирует строку в TransactionRow. None если нет финансовых данных."""
    get = lambda col: row.get(col, "") if col else ""

    debit  = _to_float(get(schema.debit_col))
    credit = _to_float(get(schema.credit_col))

    if debit == 0.0 and credit == 0.0:
        return None

    return TransactionRow(
        date=parse_date(get(schema.date_col)),
        debit=debit,
        credit=credit,
        description=get(schema.purpose_col),
        row_idx=0,
    )


# ── Публичный интерфейс ───────────────────────────────────────────────────────

def parse_xml_file(filepath: str) -> AnalysisResult:
    """
    Читает банковскую выписку в формате SpreadsheetML XML.
    Возвращает AnalysisResult совместимый с xlsx-ридером.
    """
    import os
    result = AnalysisResult(filepath=filepath)

    try:
        with open(filepath, "rb") as f:
            raw = f.read()
        content = raw.decode(ENCODING, errors="replace")
    except Exception as e:
        sheet = SheetResult(sheet_name="Sheet1")
        sheet.error = f"Не удалось прочитать файл: {e}"
        result.sheets.append(sheet)
        return result

    rows = _parse_rows(content)
    period_from, period_to = _extract_period(rows)
    sheet_name = str(period_from.year) if period_from else os.path.basename(filepath)

    sheet = SheetResult(sheet_name=sheet_name)

    schema, data_start = _find_schema(rows)
    if schema is None or not schema.is_valid:
        sheet.error = "Столбцы 'по дебету' и 'по кредиту' не найдены"
        result.sheets.append(sheet)
        return result

    for row in rows[data_start:]:
        if not row:
            continue
        if _is_total_row(row):
            break

        tx = _parse_transaction(row, schema)
        if tx is None:
            sheet.skipped_rows += 1
            continue

        if is_deposit_transfer(tx.description):
            sheet.excluded_rows += 1
            continue

        sheet.transactions.append(tx)

    result.sheets.append(sheet)
    return result
