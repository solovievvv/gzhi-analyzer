from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SheetResult:
    sheet_name: str
    debit: float = 0.0
    credit: float = 0.0
    excluded_rows: int = 0
    skipped_rows: int = 0
    error: Optional[str] = None

    @property
    def difference(self) -> float:
        return self.debit - self.credit


@dataclass
class AnalysisResult:
    filepath: str
    sheets: list[SheetResult] = field(default_factory=list)

    @property
    def total_debit(self) -> float:
        return sum(s.debit for s in self.sheets if not s.error)

    @property
    def total_credit(self) -> float:
        return sum(s.credit for s in self.sheets if not s.error)

    @property
    def total_difference(self) -> float:
        return self.total_debit - self.total_credit
