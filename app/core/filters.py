"""
Логика фильтрации строк по пояснениям к операциям.
Отдельный модуль — легко добавлять новые правила.
"""

_DEPOSIT_KEYWORDS = ("вклад", "депозит")
_INTEREST_KEYWORDS = ("процент", "%%", "% по", "выплата %", "уплачены %", "начислен")


def is_interest(description: str) -> bool:
    """True если строка описывает начисление/выплату процентов (оставляем)."""
    desc = description.lower()
    return any(k in desc for k in _INTEREST_KEYWORDS)


def is_deposit_transfer(description: str) -> bool:
    """
    True если строку нужно исключить из расчёта:
    - упоминается вклад или депозит
    - НО это не проценты
    """
    if not description:
        return False
    desc = description.lower()
    if not any(k in desc for k in _DEPOSIT_KEYWORDS):
        return False
    return not is_interest(description)
