"""
Самопроверка (реконсиляция): сверка вычисленного оборота операций с
задекларированным итогом банка ВНУТРИ самого файла.

Это объективная проверка — сравнение своего итога с итогом банка из того же
документа, без домыслов о «правильности». Если оборот банка в файле найден и не
сходится с расчётом — это сигнал «проверить вручную», а не молча-неверная цифра.

Сравнивается RAW-оборот (сумма операций ДО исключения вкладов), т.к. банковский
оборот тоже включает переводы во вклад. Так проверяется корректность ЧТЕНИЯ
(правильные ли столбцы/строки), а бизнес-правило исключения вкладов — отдельно.
"""
import re

from app.core.reader import to_float

# «Оборот», «Итого оборотов», «Оборот за период» — но не «остаток».
_OBOROT_RE   = re.compile(r"оборот", re.IGNORECASE)
_SUM_DEB_RE  = re.compile(r"сумма\s+по\s+деб\w*\s+сч[её]т", re.IGNORECASE)
_SUM_CRED_RE = re.compile(r"сумма\s+по\s+кред\w*\s+сч[её]т", re.IGNORECASE)

TOLERANCE = 1.0  # копеечные расхождения округления допускаем


def _left_label(sheet, row_idx: int, bound: int) -> str:
    parts = []
    for c in range(1, max(1, bound)):
        v = sheet.cell(row=row_idx, column=c).value
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    return " ".join(parts)


def find_declared_turnover(sheet, debit_col, credit_col):
    """
    (declared_debit, declared_credit) — задекларированный банком оборот из файла,
    либо (None, None) если не найден.
    Способ 1: строка «Оборот»/«Итого оборотов» — значения в колонках дебит/кредит.
    Способ 2: сводная таблица «Сумма по дебету/кредиту счёта» — значение под ней.
    """
    if not debit_col or not credit_col:
        return None, None
    bound = min(debit_col, credit_col)

    # Способ 1 — строка-оборот.
    for row in sheet.iter_rows():
        r = row[0].row
        lab = _left_label(sheet, r, bound)
        if lab and _OBOROT_RE.search(lab) and "остаток" not in lab.lower():
            dd = to_float(sheet.cell(row=r, column=debit_col).value)
            dc = to_float(sheet.cell(row=r, column=credit_col).value)
            if dd is not None or dc is not None:
                return (dd or 0.0), (dc or 0.0)

    # Способ 2 — сводная таблица «Сумма по … счёта».
    dcol = ccol = hrow = None
    for row in sheet.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                if dcol is None and _SUM_DEB_RE.search(cell.value):
                    dcol, hrow = cell.column, cell.row
                if ccol is None and _SUM_CRED_RE.search(cell.value):
                    ccol = cell.column
        if dcol and ccol:
            break
    if dcol and ccol and hrow:
        for r in range(hrow + 1, min(hrow + 5, sheet.max_row + 1)):
            dd = to_float(sheet.cell(row=r, column=dcol).value)
            dc = to_float(sheet.cell(row=r, column=ccol).value)
            # пропускаем строку нумерации (1,2,3,4) — берём строку с реальными суммами
            if (dd is not None and abs(dd) > 50) or (dc is not None and abs(dc) > 50):
                return (dd or 0.0), (dc or 0.0)

    return None, None


def reconcile(raw_debit, raw_credit, declared_debit, declared_credit):
    """
    None  — сверить не с чем (оборот в файле не найден);
    True  — расчёт сходится с оборотом банка;
    False — не сходится (сигнал проверить вручную).
    """
    if declared_debit is None and declared_credit is None:
        return None
    okd = abs((raw_debit or 0.0) - (declared_debit or 0.0)) <= TOLERANCE
    okc = abs((raw_credit or 0.0) - (declared_credit or 0.0)) <= TOLERANCE
    return okd and okc
