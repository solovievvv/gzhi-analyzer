"""
Таблица результатов с поддержкой копирования строк и всего вывода.

Копирование строки:
  - Клик на колонку 📋 → строка копируется в буфер → иконка меняется на ✓
  - Через COPY_REVERT_MS миллисекунд иконка возвращается в 📋

Копирование всего вывода:
  - Кнопка «Копировать всё» → TSV (tab-separated) → вставляется по ячейкам
    в Excel / Google Sheets
"""
import tkinter as tk
import tkinter.ttk as ttk
from typing import Optional

from app.ui import styles
from app.core.models import AnalysisResult, FolderResult

# Через сколько мс иконка копирования возвращается обратно
COPY_REVERT_MS = 2000

ICON_COPY    = "📋"
ICON_SUCCESS = "✓"


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def _row_to_tsv(values: tuple) -> str:
    """Одна строка таблицы → строка TSV (без колонки иконки)."""
    return "\t".join(str(v) for v in values[:-1])  # последняя — иконка


class ResultsTable(tk.Frame):
    """
    Treeview с двумя режимами (файл / папка) и копированием.

    Архитектура копирования:
      - _copy_col_id: идентификатор колонки с иконкой
      - _revert_jobs: dict[item_id -> after_job] чтобы отменять старые таймеры
      - _on_click: роутер — если клик по колонке 📋 → copy_row, иначе expand
    """

    _BASE_COLS    = ("name",     "debit",  "credit", "diff",    "excluded", "dedup",   "status")
    _BASE_HEADERS = ("Название", "Дебит",  "Кредит", "Разница", "Вклады",   "Дубли",   "Статус")
    _BASE_WIDTHS  = (200,         130,      130,       130,       80,         70,        110)

    _COPY_COL    = "copy_btn"
    _COPY_HEADER = ""
    _COPY_WIDTH  = 36

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.CARD, bd=0,
                         highlightthickness=1,
                         highlightbackground=styles.BORDER, **kwargs)
        self._revert_jobs: dict[str, str] = {}  # item_id → after job id
        self._build()

    # ── Построение ────────────────────────────────────────────────────────────

    def _build(self):
        all_cols    = self._BASE_COLS + (self._COPY_COL,)
        all_headers = self._BASE_HEADERS + (self._COPY_HEADER,)
        all_widths  = self._BASE_WIDTHS + (self._COPY_WIDTH,)

        self.tree = ttk.Treeview(self, columns=all_cols,
                                 show="headings", style="Results.Treeview",
                                 selectmode="browse")

        for col, hdr, w in zip(all_cols, all_headers, all_widths):
            self.tree.heading(col, text=hdr)
            if col == self._COPY_COL:
                self.tree.column(col, width=w, minwidth=w,
                                 anchor="center", stretch=False)
            else:
                anchor = "w" if col in ("name", "status") else "e"
                self.tree.column(col, width=w, minwidth=50, anchor=anchor)

        self._setup_tags()

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self._on_click)

    def _setup_tags(self):
        self.tree.tag_configure("alt",        background=styles.ROW_ALT)
        self.tree.tag_configure("ok",         foreground=styles.TEXT)
        self.tree.tag_configure("error",      foreground=styles.RED)
        self.tree.tag_configure("total",      background="#EEF2FF",
                                font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("file_row",   background="#F0F4FF",
                                font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("sheet_row",  foreground=styles.MUTED)
        self.tree.tag_configure("dedup_warn", foreground="#B45309")

    # ── Наполнение ────────────────────────────────────────────────────────────

    def _insert(self, parent, values: tuple, tags: tuple,
                open_: bool = False) -> str:
        """Вставляет строку с иконкой копирования в последней ячейке."""
        return self.tree.insert(
            parent, "end",
            values=values + (ICON_COPY,),
            tags=tags,
            open=open_,
        )

    def populate_file(self, result: AnalysisResult):
        self.clear()
        for i, sheet in enumerate(result.sheets):
            tag = "error" if sheet.error else ("alt" if i % 2 else "ok")
            if sheet.error:
                vals = (sheet.sheet_name, "—", "—", "—", "—", "—", f"⚠ {sheet.error}")
            else:
                vals = (sheet.sheet_name,
                        _fmt(sheet.debit), _fmt(sheet.credit),
                        _fmt(sheet.difference),
                        str(sheet.excluded_rows), "—", "✓ ОК")
            self._insert("", vals, (tag,))

        self._insert("", (
            "ИТОГО",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference), "", "", "",
        ), ("total",))

    def populate_folder(self, result: FolderResult):
        self.clear()
        for i, file_result in enumerate(result.files):
            dedup_count = file_result.deduplicated_count
            dedup_label = str(dedup_count) if dedup_count else "—"
            status = "⚠ Есть ошибки" if file_result.has_errors else "✓ ОК"
            file_tag = "dedup_warn" if dedup_count else "file_row"

            node = self._insert("", (
                f"📄 {file_result.filename}",
                _fmt(file_result.total_debit),
                _fmt(file_result.total_credit),
                _fmt(file_result.total_difference),
                "", dedup_label, status,
            ), (file_tag,), open_=False)

            for sheet in file_result.sheets:
                sheet_tag = "error" if sheet.error else "sheet_row"
                if sheet.error:
                    s_vals = (f"  └ {sheet.sheet_name}",
                              "—", "—", "—", "—", "—", f"⚠ {sheet.error}")
                else:
                    s_vals = (f"  └ {sheet.sheet_name}",
                              _fmt(sheet.debit), _fmt(sheet.credit),
                              _fmt(sheet.difference),
                              str(sheet.excluded_rows), "—", "")
                self._insert(node, s_vals, (sheet_tag,))

            if file_result.deduplicated:
                dup_node = self._insert(node, (
                    f"  └ ⚠ Исключено дублей: {dedup_count}",
                    "", "", "", "", "", "",
                ), ("dedup_warn",))
                for dr in file_result.deduplicated:
                    d_str = str(dr.row.date) if dr.row.date else "б/д"
                    self._insert(dup_node, (
                        f"    • {d_str}  уже в: {dr.original_file}",
                        _fmt(dr.row.debit) if dr.row.debit else "—",
                        _fmt(dr.row.credit) if dr.row.credit else "—",
                        "", "", "", "",
                    ), ("dedup_warn",))

        self._insert("", (
            "ИТОГО ПО ПАПКЕ (без дублей)",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference),
            "", str(result.total_deduplicated) if result.total_deduplicated else "—", "",
        ), ("total",))

    def clear(self):
        # Отменяем все pending таймеры
        for job in self._revert_jobs.values():
            self.tree.after_cancel(job)
        self._revert_jobs.clear()
        self.tree.delete(*self.tree.get_children())

    # ── Копирование строки ────────────────────────────────────────────────────

    def _on_click(self, event: tk.Event):
        """Роутер кликов: копирование по иконке, остальное — стандартное."""
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row:
            return
        # Колонки нумеруются #1, #2… — копирование в последней
        total_cols = len(self._BASE_COLS) + 1
        if col == f"#{total_cols}":
            self._copy_row(row)

    def _copy_row(self, item_id: str):
        """Копирует строку в буфер, показывает ✓, через COPY_REVERT_MS возвращает 📋."""
        values = self.tree.item(item_id, "values")
        if not values:
            return

        tsv = _row_to_tsv(values)
        self._clipboard_set(tsv)

        # Меняем иконку на ✓
        new_vals = list(values)
        new_vals[-1] = ICON_SUCCESS
        self.tree.item(item_id, values=new_vals)

        # Отменяем старый таймер если был
        if item_id in self._revert_jobs:
            self.tree.after_cancel(self._revert_jobs[item_id])

        # Планируем возврат иконки
        job = self.tree.after(COPY_REVERT_MS, lambda: self._revert_icon(item_id))
        self._revert_jobs[item_id] = job

    def _revert_icon(self, item_id: str):
        """Возвращает иконку 📋 после таймера."""
        try:
            values = list(self.tree.item(item_id, "values"))
            values[-1] = ICON_COPY
            self.tree.item(item_id, values=values)
        except tk.TclError:
            pass  # строка уже удалена (clear был вызван)
        self._revert_jobs.pop(item_id, None)

    def _clipboard_set(self, text: str):
        self.tree.clipboard_clear()
        self.tree.clipboard_append(text)
        self.tree.update()

    # ── TSV для «Копировать всё» ──────────────────────────────────────────────

    def get_all_as_tsv(self) -> str:
        """
        Возвращает всё содержимое таблицы как TSV.
        Заголовок + строки верхнего уровня (без дочерних деталей).
        Вставляется по ячейкам в Excel / Google Sheets.
        """
        header = "\t".join(self._BASE_HEADERS)
        lines = [header]

        def collect(item):
            values = self.tree.item(item, "values")
            if values:
                lines.append(_row_to_tsv(values))
            for child in self.tree.get_children(item):
                collect(child)

        for item in self.tree.get_children():
            collect(item)

        return "\n".join(lines)
