from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class TransactionRow:
    """Одна строка транзакции из таблицы."""
    date: Optional[date]
    debit: float
    credit: float
    description: str
    row_idx: int  # номер строки в xlsx (для отладки)


@dataclass
class DeduplicatedRow:
    """Строка, которая была исключена как дубликат."""
    row: TransactionRow
    source_file: str     # файл где дубликат
    original_file: str   # файл где строка уже была учтена


@dataclass
class SheetResult:
    """Результат обработки одного листа."""
    sheet_name: str
    transactions: list[TransactionRow] = field(default_factory=list)
    excluded_rows: int = 0      # исключено по правилу вклад/депозит
    skipped_rows: int = 0
    error: Optional[str] = None

    # Самопроверка: сумма операций ДО исключения вкладов (raw) и задекларированный
    # банком оборот из файла. reconciled: True/False/None (сошлось/нет/нет сверки).
    raw_debit: float = 0.0
    raw_credit: float = 0.0
    declared_debit: Optional[float] = None
    declared_credit: Optional[float] = None
    reconciled: Optional[bool] = None

    @property
    def debit(self) -> float:
        return sum(t.debit for t in self.transactions)

    @property
    def credit(self) -> float:
        return sum(t.credit for t in self.transactions)

    @property
    def difference(self) -> float:
        return self.debit - self.credit


@dataclass
class AnalysisResult:
    """Результат обработки одного файла (xlsx/xls/xml/docx/pdf)."""
    filepath: str
    sheets: list[SheetResult] = field(default_factory=list)

    # Файловая ошибка чтения (файл не открылся). Отличается от ошибки листа
    # (открылся, но столбцы дебит/кредит не найдены).
    error: Optional[str] = None

    # Дубликаты найденные при обработке папки (заполняется дедупликатором)
    deduplicated: list[DeduplicatedRow] = field(default_factory=list)

    @property
    def filename(self) -> str:
        import os
        return os.path.basename(self.filepath)

    @property
    def status(self) -> str:
        """'ok' — посчитано; 'read_error' — файл не открылся;
        'no_data' — открылся, но дебит/кредит не найдены (не выписка/нет операций)."""
        if self.error:
            return "read_error"
        if self.sheets and all(s.error for s in self.sheets):
            return "no_data"
        return "ok"

    @property
    def status_label(self) -> str:
        return {
            "ok": "посчитано",
            "read_error": "ошибка чтения",
            "no_data": "нет операций",
        }[self.status]

    @property
    def reconciled(self) -> Optional[bool]:
        """Сверка с оборотом банка по файлу: False если хоть один лист не сошёлся;
        True если хоть один сошёлся и несошедшихся нет; None если сверять не с чем."""
        flags = [s.reconciled for s in self.sheets if not s.error]
        if any(f is False for f in flags):
            return False
        if any(f is True for f in flags):
            return True
        return None

    @property
    def reconcile_label(self) -> str:
        return {True: "✓ сверено с банком",
                False: "⚠ не сошлось — проверить",
                None: "— нет сверки"}[self.reconciled]

    @property
    def total_debit(self) -> float:
        return sum(s.debit for s in self.sheets if not s.error)

    @property
    def total_credit(self) -> float:
        return sum(s.credit for s in self.sheets if not s.error)

    @property
    def total_difference(self) -> float:
        return self.total_debit - self.total_credit

    @property
    def has_errors(self) -> bool:
        return self.error is not None or any(s.error for s in self.sheets)

    @property
    def deduplicated_count(self) -> int:
        return len(self.deduplicated)


@dataclass
class FolderResult:
    """Результат обработки папки с xlsx-файлами."""
    folderpath: str
    files: list[AnalysisResult] = field(default_factory=list)

    # Итоги БЕЗ дедупликации — фиксируются в process_folder ДО мутации
    # транзакций дедупликатором. Свойства total_* ниже — итоги С дедупликацией.
    raw_debit: Optional[float] = None
    raw_credit: Optional[float] = None

    @property
    def total_debit(self) -> float:
        return sum(f.total_debit for f in self.files)

    @property
    def total_credit(self) -> float:
        return sum(f.total_credit for f in self.files)

    @property
    def total_difference(self) -> float:
        return self.total_debit - self.total_credit

    @property
    def total_deduplicated(self) -> int:
        return sum(f.deduplicated_count for f in self.files)

    # ── Итоги без дедупликации (для прозрачности показываем оба) ───────────────

    @property
    def raw_total_debit(self) -> float:
        return self.raw_debit if self.raw_debit is not None else self.total_debit

    @property
    def raw_total_credit(self) -> float:
        return self.raw_credit if self.raw_credit is not None else self.total_credit

    @property
    def raw_total_difference(self) -> float:
        return self.raw_total_debit - self.raw_total_credit
