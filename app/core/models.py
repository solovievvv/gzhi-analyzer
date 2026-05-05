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
    """Результат обработки одного xlsx-файла."""
    filepath: str
    sheets: list[SheetResult] = field(default_factory=list)

    # Дубликаты найденные при обработке папки (заполняется дедупликатором)
    deduplicated: list[DeduplicatedRow] = field(default_factory=list)

    @property
    def filename(self) -> str:
        import os
        return os.path.basename(self.filepath)

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
        return any(s.error for s in self.sheets)

    @property
    def deduplicated_count(self) -> int:
        return len(self.deduplicated)


@dataclass
class FolderResult:
    """Результат обработки папки с xlsx-файлами."""
    folderpath: str
    files: list[AnalysisResult] = field(default_factory=list)

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
