@echo off
echo === Сборка Windows .exe ===

echo [1/3] Устанавливаем зависимости...
pip install pyinstaller openpyxl

echo [2/3] Собираем .exe...
pyinstaller expense_analyzer.spec --clean

echo [3/3] Готово!
echo Файл: dist\AnalyzDebitCredit.exe
pause
