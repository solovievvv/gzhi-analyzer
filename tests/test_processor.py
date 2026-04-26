"""
Тесты логики обработки xlsx.
Запуск из корня проекта: python -m pytest tests/ -v
  или: python tests/test_processor.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import openpyxl
import tempfile

from app.core.reader import process_file
from app.core.filters import is_deposit_transfer, is_interest

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
results = []


def make_wb(setup_fn):
    wb = openpyxl.Workbook()
    setup_fn(wb)
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    wb.save(tmp.name)
    return tmp.name

def check(name, filepath, sheet_idx, expected_debit, expected_credit,
          expected_excluded=None, expect_error=False):
    import traceback
    try:
        r = process_file(filepath)
        s = r.sheets[sheet_idx]
        if expect_error:
            ok = s.error is not None
            msg = f"error={s.error!r}"
        else:
            ok = abs(s.debit - expected_debit) < 0.01 and abs(s.credit - expected_credit) < 0.01
            if expected_excluded is not None:
                ok = ok and s.excluded_rows == expected_excluded
            msg = f"debit={s.debit:.2f} credit={s.credit:.2f} excl={s.excluded_rows} err={s.error}"
    except Exception as e:
        ok = False
        msg = f"EXCEPTION: {e}\n{traceback.format_exc()}"
    finally:
        try: os.unlink(filepath)
        except: pass

    results.append(ok)
    print(f"  {PASS if ok else FAIL} [{name}]")
    if not ok:
        print(f"         expected: D={expected_debit} C={expected_credit}")
        print(f"         got:      {msg}")


# ── Тесты фильтров ────────────────────────────────────────────────────────────

def test_filters():
    cases = [
        ("Перечисление средств во вклад",           True),
        ("Возврат депозита по договору 123",         True),
        ("Перечисление во вклад (депозит)",          True),
        ("Уплачены проценты по договору вклада",     False),
        ("Выплата %% по депозиту за период",         False),
        ("Выплата процентов по депозиту",            False),
        ("Начислены проценты по вкладу",             False),
        ("Оплата услуг ЖКХ",                        False),
        ("Пополнение р/счёта",                       False),
        ("",                                         False),
    ]
    all_ok = True
    for desc, expected in cases:
        got = is_deposit_transfer(desc)
        ok = got == expected
        all_ok = all_ok and ok
        if not ok:
            print(f"    FILTER FAIL: {desc!r} → got {got}, want {expected}")
    results.append(all_ok)
    print(f"  {PASS if all_ok else FAIL} [filters: is_deposit_transfer]")


# ── Тесты чтения xlsx ─────────────────────────────────────────────────────────

def t01(wb):
    ws = wb.active
    ws.append(["По дебиту счёта", "По кредиту счёта", "Назначение"])
    ws.append([1000, 0, "Оплата"]);  ws.append([0, 500, "Приход"]); ws.append([200, 0, "Аренда"])
check("01 базовый", make_wb(t01), 0, 1200, 500)

def t02(wb):
    ws = wb.active
    for _ in range(4): ws.append(["шапка"])
    ws.append(["По дебиту", "По кредиту", "Назначение"])
    ws.append([300, 0, "Платёж"]); ws.append([0, 150, "Возврат"])
check("02 заголовки с 5-й строки", make_wb(t02), 0, 300, 150)

def t03(wb):
    ws = wb.active
    for col, v in enumerate(["Банк","Дата","Документ","Плательщик","Получатель","По дебиту","По кредиту","Примечание"], 1):
        ws.cell(1, col, v)
    ws.cell(2,6,750); ws.cell(2,8,"Расход"); ws.cell(3,7,400); ws.cell(3,8,"Приход")
check("03 столбцы сдвинуты вправо", make_wb(t03), 0, 750, 400)

def t04(wb):
    ws = wb.active
    ws.append(["По дебету", "По кредиту"])
    ws.append(["1 234,56", None]); ws.append([None, "789,00"])
check("04 числа-строки русская локаль", make_wb(t04), 0, 1234.56, 789.00)

def t05(wb):
    ws = wb.active
    ws.append(["По дебиту", "По кредиту"])
    ws.append(["100000-50", None]); ws.append([None, "50000-25"])
check("05 формат '123456-78'", make_wb(t05), 0, 100000.50, 50000.25)

def t06(wb):
    ws = wb.active
    ws.append(["Таблица 1"]); ws.append(["Дебет","Кредит"]); ws.append([9999, 8888]); ws.append([None,None])
    ws.append(["Таблица 2"]); ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([100, None, "Расход"]); ws.append([None, 200, "Доход"])
check("06 Таблица1+Таблица2 берём последний заголовок", make_wb(t06), 0, 100, 200)

def t07(wb):
    ws = wb.active
    ws.append(["По дебиту","По кредиту","Примечание"])
    ws.append([13, 14, 15]); ws.append([500, None, "Расход"]); ws.append([None, 300, "Доход"])
check("07 строка нумерации пропускается", make_wb(t07), 0, 500, 300)

def t08(wb):
    ws = wb.active
    ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([1000, None, "Перечисление средств во вклад"])
    ws.append([None, 500, "Поступление"]); ws.append([200, None, "Расход"])
check("08 исключение вклад", make_wb(t08), 0, 200, 500, expected_excluded=1)

def t09(wb):
    ws = wb.active
    ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([5000, None, "Перечисление средств во вклад (депозит)"])
    ws.append([None, 5000, "Возврат депозита по договору 123"])
    ws.append([None, 300, "Поступление"])
check("09 вклад+депозит оба исключаются", make_wb(t09), 0, 0, 300, expected_excluded=2)

def t10(wb):
    ws = wb.active
    ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([None, 1000, "Уплачены проценты по договору банковского вклада"])
    ws.append([None, 500,  "Выплата %% по вкладу за период"])
    ws.append([None, 200,  "Начислены проценты по депозиту"])
    ws.append([None, 800,  "Выплата процентов по депозиту 123"])
check("10 проценты НЕ исключаются", make_wb(t10), 0, 0, 2500, expected_excluded=0)

def t11(wb):
    ws = wb.active; ws.append(["Дата","Сумма"]); ws.append(["01.01.24", 100])
check("11 нет дебит/кредит → ошибка", make_wb(t11), 0, 0, 0, expect_error=True)

def t12(wb):
    ws = wb.active; ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([100, None, ""]); ws.append([None,None,None]); ws.append([None,None,None])
    ws.append([200, None, ""]); ws.append([None,None,None]); ws.append([None, 400, ""])
check("12 пустые строки внутри данных", make_wb(t12), 0, 300, 400)

def t13():
    def setup(wb):
        ws1 = wb.active; ws1.title = "Счёт 1"
        ws1.append(["По дебиту","По кредиту"]); ws1.append([1000,0]); ws1.append([0,600])
        ws2 = wb.create_sheet("Счёт 2")
        for _ in range(3): ws2.append(["шапка"])
        ws2.append(["Дебет","Кредит"]); ws2.append([400,None]); ws2.append([None,200])
    path = make_wb(setup)
    r = process_file(path)
    os.unlink(path)
    s1, s2 = r.sheets[0], r.sheets[1]
    ok = abs(s1.debit-1000)<0.01 and abs(s1.credit-600)<0.01 and abs(s2.debit-400)<0.01 and abs(s2.credit-200)<0.01
    results.append(ok)
    print(f"  {PASS if ok else FAIL} [13 два листа с разной структурой]")
t13()

def t14(wb):
    ws = wb.active; ws.append(["сумма по дебету счёта","сумма по кредиту счёта"])
    ws.append([777, None]); ws.append([None, 333])
check("14 'по дебету' через е", make_wb(t14), 0, 777, 333)

def t15(wb):
    ws = wb.active; ws.append(["ПО ДЕБИТУ СЧЁТА","ПО КРЕДИТУ СЧЁТА"])
    ws.append([888, None]); ws.append([None, 444])
check("15 заголовок ВЕРХНИЙ РЕГИСТР", make_wb(t15), 0, 888, 444)

def t16(wb):
    ws = wb.active; ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([500, 0, "Расход"]); ws.append([0, 300, "Приход"])
check("16 явные нули в ячейках", make_wb(t16), 0, 500, 300)

def t17(wb):
    ws = wb.active; ws.append(["По дебиту","По кредиту","Назначение"])
    ws.append([100, None, "Платёж"]); ws.append([None, 200, "Доход"])
    ws.append(["Итого", 100, 200])
check("17 строка 'Итого' пропускается", make_wb(t17), 0, 100, 200)

test_filters()

# ── Итог ──────────────────────────────────────────────────────────────────────
total = len(results); passed = sum(results)
print(f"\n{'='*50}")
print(f"Результат: {passed}/{total} тестов пройдено")
if passed < total:
    print("\033[91mЕсть провалившиеся тесты!\033[0m")
else:
    print("\033[92mВсе тесты пройдены ✓\033[0m")
