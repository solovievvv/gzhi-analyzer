#!/bin/bash
set -e
echo "=== Сборка macOS .dmg ==="

echo "[1/4] Устанавливаем зависимости..."
pip install pyinstaller openpyxl

echo "[2/4] Устанавливаем create-dmg..."
brew install create-dmg

echo "[3/4] Собираем .app..."
pyinstaller expense_analyzer.spec --clean

echo "[4/4] Упаковываем в .dmg..."
create-dmg \
  --volname "Анализ дебита и кредита" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "AnalyzDebitCredit.app" 175 190 \
  --hide-extension "AnalyzDebitCredit.app" \
  --app-drop-link 425 190 \
  "dist/AnalyzDebitCredit.dmg" \
  "dist/AnalyzDebitCredit.app" || true

echo ""
echo "Готово! Файл: dist/AnalyzDebitCredit.dmg"
