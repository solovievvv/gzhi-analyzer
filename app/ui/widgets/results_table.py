import tkinter as tk
import tkinter.ttk as ttk
from app.ui import styles
from app.core.models import AnalysisResult, FolderResult


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


class ResultsTable(tk.Frame):
    _COLS    = ("name",     "debit",  "credit", "diff",    "excluded", "dedup",   "status")
    _HEADERS = ("Название", "Дебит",  "Кредит", "Разница", "Вклады",   "Дубли",   "Статус")
    _WIDTHS  = (200,         130,      130,       130,       80,         70,        130)

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
            anchor = "w" if col in ("name", "status") else "e"
            self.tree.column(col, width=w, minwidth=50, anchor=anchor)

        self.tree.tag_configure("alt",       background=styles.ROW_ALT)
        self.tree.tag_configure("ok",        foreground=styles.TEXT)
        self.tree.tag_configure("error",     foreground=styles.RED)
        self.tree.tag_configure("total",     background="#EEF2FF",
                                font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("file_row",  background="#F0F4FF",
                                font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("sheet_row", foreground=styles.MUTED)
        self.tree.tag_configure("dedup_warn", foreground="#B45309")  # янтарный

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    # ── Режим одного файла ────────────────────────────────────────────────────

    def populate_file(self, result: AnalysisResult):
        self.clear()
        for i, sheet in enumerate(result.sheets):
            tag = "error" if sheet.error else ("alt" if i % 2 else "ok")
            if sheet.error:
                values = (sheet.sheet_name, "—", "—", "—", "—", "—", f"⚠ {sheet.error}")
            else:
                values = (
                    sheet.sheet_name,
                    _fmt(sheet.debit), _fmt(sheet.credit), _fmt(sheet.difference),
                    str(sheet.excluded_rows), "—", "✓ ОК",
                )
            self.tree.insert("", "end", values=values, tags=(tag,))

        self.tree.insert("", "end", tags=("total",), values=(
            "ИТОГО",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference), "", "", "",
        ))

    # ── Режим папки ───────────────────────────────────────────────────────────

    def populate_folder(self, result: FolderResult):
        self.clear()
        for i, file_result in enumerate(result.files):
            dedup_count = file_result.deduplicated_count
            dedup_label = str(dedup_count) if dedup_count else "—"
            status = "⚠ Есть ошибки" if file_result.has_errors else "✓ ОК"
            file_tag = "dedup_warn" if dedup_count else "file_row"

            file_node = self.tree.insert("", "end", tags=(file_tag,), values=(
                f"📄 {file_result.filename}",
                _fmt(file_result.total_debit),
                _fmt(file_result.total_credit),
                _fmt(file_result.total_difference),
                "",
                dedup_label,
                status,
            ), open=False)

            # Строки листов
            for sheet in file_result.sheets:
                sheet_tag = "error" if sheet.error else "sheet_row"
                if sheet.error:
                    s_values = (f"  └ {sheet.sheet_name}", "—", "—", "—",
                                "—", "—", f"⚠ {sheet.error}")
                else:
                    s_values = (
                        f"  └ {sheet.sheet_name}",
                        _fmt(sheet.debit), _fmt(sheet.credit),
                        _fmt(sheet.difference),
                        str(sheet.excluded_rows), "—", "",
                    )
                self.tree.insert(file_node, "end", values=s_values, tags=(sheet_tag,))

            # Список дубликатов внутри файла
            if file_result.deduplicated:
                dup_node = self.tree.insert(
                    file_node, "end",
                    values=(f"  └ ⚠ Исключено дублей: {dedup_count}",
                            "", "", "", "", "", ""),
                    tags=("dedup_warn",)
                )
                for dr in file_result.deduplicated:
                    d_str = str(dr.row.date) if dr.row.date else "б/д"
                    self.tree.insert(dup_node, "end", values=(
                        f"    • {d_str}  уже в: {dr.original_file}",
                        _fmt(dr.row.debit) if dr.row.debit else "—",
                        _fmt(dr.row.credit) if dr.row.credit else "—",
                        "", "", "", "",
                    ), tags=("dedup_warn",))

        self.tree.insert("", "end", tags=("total",), values=(
            "ИТОГО ПО ПАПКЕ (без дублей)",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference),
            "", str(result.total_deduplicated) if result.total_deduplicated else "—", "",
        ))

    def clear(self):
        self.tree.delete(*self.tree.get_children())
