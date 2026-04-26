# Анализ дебита и кредита

Приложение для автоматического подсчёта дебита, кредита и разницы из банковских выписок Excel (.xlsx).

## Скачать

| Платформа | Ссылка |
|-----------|--------|
| 🪟 Windows | [Скачать .exe](https://github.com/solovievvv/gzhi-analyzer/releases/latest/download/AnalyzDebitCredit.exe) |
| 🍎 macOS   | [Скачать .dmg](https://github.com/solovievvv/gzhi-analyzer/releases/latest/download/AnalyzDebitCredit.dmg) |

> Всегда доступна последняя версия. Все [релизы](https://github.com/solovievvv/gzhi-analyzer/releases).

---

## Как пользоваться

**Windows** — скачай `.exe` и запусти. Установка не нужна.

**macOS** — скачай `.dmg`, открой, перетащи приложение в папку Applications.
При первом запуске: правой кнопкой на приложение → **Открыть** → **Открыть**.

---

## Логика расчёта

- Приложение автоматически находит столбцы «дебит» и «кредит» на каждом листе
- Анализируются все листы книги
- Строки с упоминанием **вклада** или **депозита** исключаются из расчёта
- Строки с **процентами** по вкладу/депозиту — остаются (это доход)

---

## Разработка

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS

pip install -r requirements.txt
python main.py
```

Тесты:
```bash
python tests/test_processor.py
```

## Обновление

```bash
git add .
git commit -m "описание изменений"
git push

# Новый релиз:
git tag v1.x.x
git push origin v1.x.x
```
