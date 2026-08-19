"""
Лёгкий адаптер: 2D-список значений → объект с подмножеством API openpyxl-листа.

Нужен, чтобы таблицы из docx/pdf прогонять через ТУ ЖЕ логику reader.py
(find_columns, process_sheet, пропуск строк-итогов, выбор детальной таблицы,
фильтр вкладов) без её изменения и дублирования.

Реализовано ровно то подмножество API, что использует reader.py:
  .title, .max_row, .max_column, .iter_rows(), .cell(row=, column=).value, sheet[r]
Индексация 1-based, как в openpyxl. Пустые ячейки → None.
"""
from typing import Any, Iterator, List


class Cell:
    __slots__ = ("value", "row", "column")

    def __init__(self, value: Any, row: int, column: int):
        self.value = value
        self.row = row
        self.column = column


class GridSheet:
    def __init__(self, rows2d: List[List[Any]], title: str = "Sheet"):
        self.title = title
        self._rows: List[List[Any]] = [list(r) for r in rows2d]
        self._max_row = len(self._rows)
        self._max_col = max((len(r) for r in self._rows), default=0)

    @property
    def max_row(self) -> int:
        return self._max_row

    @property
    def max_column(self) -> int:
        return self._max_col

    def _val(self, r: int, c: int) -> Any:
        if 1 <= r <= self._max_row:
            row = self._rows[r - 1]
            if 1 <= c <= len(row):
                v = row[c - 1]
                return v if v != "" else None
        return None

    def cell(self, row: int, column: int) -> Cell:
        return Cell(self._val(row, column), row, column)

    def _row_cells(self, r: int) -> List[Cell]:
        return [Cell(self._val(r, c), r, c) for c in range(1, self._max_col + 1)]

    def __getitem__(self, r: int) -> List[Cell]:
        return self._row_cells(r)

    def iter_rows(self) -> Iterator[List[Cell]]:
        for r in range(1, self._max_row + 1):
            yield self._row_cells(r)
