"""
Парсинг дат из ячеек Excel.
Поддерживаемые форматы:
  - datetime/date объекты (Excel native)
  - 'дд.мм.гг', 'дд.мм.гггг'
  - 'дд,мм,гг', 'дд,мм,гггг'
  - 'дд/мм/гг', 'дд/мм/гггг'
  - 'гггг-мм-дд'
  - С временем: 'дд.мм.гг чч:мм:сс', 'дд.мм.гггг чч:мм'
"""
import re
from datetime import date, datetime
from typing import Optional

# Форматы без времени
_DATE_FORMATS = [
    '%d.%m.%Y', '%d.%m.%y',
    '%d,%m,%Y', '%d,%m,%y',
    '%d/%m/%Y', '%d/%m/%y',
    '%Y-%m-%d',
    '%d-%m-%Y', '%d-%m-%y',
]

# Форматы со временем
_DATETIME_FORMATS = [
    '%d.%m.%Y %H:%M:%S', '%d.%m.%y %H:%M:%S',
    '%d.%m.%Y %H:%M',    '%d.%m.%y %H:%M',
    '%d,%m,%Y %H:%M:%S', '%d,%m,%y %H:%M:%S',
    '%d/%m/%Y %H:%M:%S', '%d/%m/%y %H:%M:%S',
    '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
]


def parse_date(value) -> Optional[date]:
    """
    Конвертирует значение ячейки в date.
    Возвращает None если не удалось распознать.
    """
    if value is None:
        return None

    # Уже date/datetime из openpyxl
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    s = value.strip()
    if not s:
        return None

    # Нормализуем: заменяем запятые и слеши между цифрами на точки
    # но не трогаем время (там двоеточия)
    # Сначала пробуем строку как есть
    for fmt in _DATETIME_FORMATS + _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass

    # Пробуем только первые 10 символов (отрезаем время если нестандартный разделитель)
    s10 = s[:10]
    for fmt in ['%d.%m.%Y', '%d,%m,%Y', '%Y-%m-%d', '%d/%m/%Y']:
        try:
            return datetime.strptime(s10, fmt).date()
        except ValueError:
            pass

    # Пробуем первые 8 символов (дд.мм.гг)
    s8 = s[:8]
    for fmt in ['%d.%m.%y', '%d,%m,%y', '%d/%m/%y']:
        try:
            return datetime.strptime(s8, fmt).date()
        except ValueError:
            pass

    return None
