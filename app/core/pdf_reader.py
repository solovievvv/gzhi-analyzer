"""
Чтение банковских выписок в формате PDF (текстовых, не сканов).

Внутри — та же выписка, что и в xlsx/docx. Таблица транзакций часто тянется
через несколько страниц: шапка (с «по дебету»/«по кредиту») только на первой,
дальше страницы-продолжения БЕЗ шапки, но с тем же числом столбцов.

Стратегия: извлечь все таблицы со всех страниц; найти детальную таблицу
(не сводную) с дебит/кредит; склеить её со всеми таблицами того же числа
столбцов (это и есть страницы-продолжения) в одну сетку и прогнать через
ту же логику reader.py (find_columns/process_sheet) — переиспользование, DRY.

Скан-PDF (без извлекаемых таблиц) → ошибка обработки (OCR вне охвата).
"""
from app.core.models import AnalysisResult, SheetResult
from app.core.grid import GridSheet
from app.core.reader import find_columns, process_sheet, is_summary_header


def _norm(rows) -> list:
    """Нормализует таблицу pdfplumber: None → '', обрезает пробелы."""
    out = []
    for r in rows:
        out.append([(c.strip() if isinstance(c, str) else ("" if c is None else str(c))) for c in r])
    return out


def parse_pdf_file(filepath: str) -> AnalysisResult:
    result = AnalysisResult(filepath=filepath)

    try:
        import pdfplumber
    except Exception as e:
        sr = SheetResult(sheet_name="pdf")
        sr.error = f"библиотека pdfplumber недоступна: {e}"
        result.sheets.append(sr)
        return result

    all_tables = []  # (ncols, rows2d)
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                for tb in (page.extract_tables() or []):
                    if not tb:
                        continue
                    rows = _norm(tb)
                    ncols = max((len(r) for r in rows), default=0)
                    if ncols:
                        all_tables.append((ncols, rows))
    except Exception as e:
        sr = SheetResult(sheet_name="pdf")
        sr.error = f"не удалось прочитать PDF: {e}"
        result.sheets.append(sr)
        return result

    # Детальная таблица (не сводная) с наибольшим числом строк — задаёт число
    # столбцов N, по которому опознаём страницы-продолжения.
    detail = None
    detail_rows = -1
    for ncols, rows in all_tables:
        gs = GridSheet(rows)
        hrow, _dt, dcol, ccol = find_columns(gs)
        if dcol is None:
            continue
        d_text = str(gs.cell(row=hrow, column=dcol).value or "")
        c_text = str(gs.cell(row=hrow, column=ccol).value or "")
        if is_summary_header(d_text, c_text):
            continue
        if len(rows) > detail_rows:
            detail_rows = len(rows)
            detail = (ncols, rows)

    if detail is None:
        sr = SheetResult(sheet_name="pdf")
        sr.error = "таблица с колонками 'дебит'/'кредит' не найдена (возможно скан — нужен OCR)"
        result.sheets.append(sr)
        return result

    target_cols = detail[0]
    combined = []
    for ncols, rows in all_tables:
        if ncols == target_cols:      # детальная + страницы-продолжения
            combined.extend(rows)

    result.sheets.append(process_sheet(GridSheet(combined, title="pdf")))
    return result
