# Анализ дебита и кредита

Десктопное приложение для подсчёта дебита, кредита и разницы из Excel-файлов (.xlsx).

---

## Запуск из исходников (разработка)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

---

## Сборка установщиков

### Автоматически через GitHub Actions (рекомендуется)

1. Залей код на GitHub в ветку `main`
2. Actions сам соберёт `.exe` и `.dmg`
3. Скачай готовые файлы во вкладке **Actions → последний run → Artifacts**

**Выпуск новой версии:**
```bash
git tag v1.0.1
git push origin v1.0.1
```
GitHub создаст Release и прикрепит к нему оба файла автоматически.

---

### Вручную на Windows → .exe

```bat
build_windows.bat
```
Результат: `dist\AnalyzDebitCredit.exe`

### Вручную на macOS → .dmg

```bash
chmod +x build_mac.sh
./build_mac.sh
```
Результат: `dist/AnalyzDebitCredit.dmg`

---

## Структура проекта

```
expense_analyzer/
├── main.py                     — GUI (tkinter)
├── processor.py                — логика чтения xlsx
├── requirements.txt            — зависимости для разработки
├── expense_analyzer.spec       — конфиг PyInstaller
├── build_windows.bat           — сборка на Windows
├── build_mac.sh                — сборка на macOS
├── test_processor.py           — тесты (17 кейсов)
└── .github/
    └── workflows/
        └── build.yml           — CI/CD: авто-сборка при push/тег
```

---

## Как обновить приложение

1. Внеси правки в `main.py` или `processor.py`
2. Прогони тесты: `python test_processor.py`
3. Залей на GitHub:
   ```bash
   git add .
   git commit -m "fix: описание изменений"
   git push
   ```
4. Actions пересобирает оба бинарника автоматически.
   Для публичного релиза: `git tag v1.x.x && git push origin v1.x.x`
