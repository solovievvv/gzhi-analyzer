import tkinter as tk
import tkinter.ttk as ttk
from app.ui import styles
from app.core.models import AnalysisResult


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


class ResultsTable(tk.Frame):
    """Таблица результатов по листам + строка ИТОГО."""

    _COLS = ("sheet", "debit", "credit", "diff", "excluded", "status")
    _HEADERS = ("Лист", "Дебит", "Кредит", "Разница", "Исключено строк", "Статус")
    _WIDTHS  = (130, 130, 130, 130, 120, 130)

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.CARD, bd=0,
                         highlightthickness=1,
                         highlightbackground=styles.BORDER, **kwargs)
        self._build()

    def _build(self):
        self.tree = ttk.Treeview(self, columns=self._COLS,
                                 show="headings", style="Results.Treeview",
                                 selectmode="browse")
        for col, hdr, w in zip(self._COLS, self._HEADERS, self._WIDTHS):
            self.tree.heading(col, text=hdr)
            anchor = "w" if col in ("sheet", "status") else "e"
            self.tree.column(col, width=w, minwidth=80, anchor=anchor)

        self.tree.tag_configure("alt",   background=styles.ROW_ALT)
        self.tree.tag_configure("ok",    foreground=styles.TEXT)
        self.tree.tag_configure("error", foreground=styles.RED)
        self.tree.tag_configure("total", background="#EEF2FF",
                                font=("Segoe UI", 9, "bold"))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def populate(self, result: AnalysisResult):
        self.tree.delete(*self.tree.get_children())

        for i, sheet in enumerate(result.sheets):
            tag = "error" if sheet.error else ("alt" if i % 2 else "ok")
            if sheet.error:
                values = (sheet.sheet_name, "—", "—", "—", "—", f"⚠ {sheet.error}")
            else:
                values = (
                    sheet.sheet_name,
                    _fmt(sheet.debit),
                    _fmt(sheet.credit),
                    _fmt(sheet.difference),
                    str(sheet.excluded_rows),
                    "✓ ОК",
                )
            self.tree.insert("", "end", values=values, tags=(tag,))

        self.tree.insert("", "end", tags=("total",), values=(
            "ИТОГО",
            _fmt(result.total_debit),
            _fmt(result.total_credit),
            _fmt(result.total_difference),
            "", "",
        ))

    def clear(self):
        self.tree.delete(*self.tree.get_children())
