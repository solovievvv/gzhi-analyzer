import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from app.ui import styles


class FilePicker(tk.Frame):
    """Карточка с полем ввода пути и кнопкой 'Обзор…'."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.CARD, bd=0,
                         highlightthickness=1,
                         highlightbackground=styles.BORDER, **kwargs)
        self.path_var = tk.StringVar()
        self._build()

    def _build(self):
        inner = tk.Frame(self, bg=styles.CARD, padx=12, pady=10)
        inner.pack(fill="x")

        tk.Label(inner, text="Путь к файлу", bg=styles.CARD,
                 fg=styles.MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        row = tk.Frame(inner, bg=styles.CARD)
        row.pack(fill="x", pady=(4, 0))

        tk.Entry(row, textvariable=self.path_var,
                 font=("Segoe UI", 10), relief="flat",
                 bg=styles.BG, fg=styles.TEXT, bd=0,
                 highlightthickness=1,
                 highlightbackground=styles.BORDER,
                 highlightcolor=styles.ACCENT
                 ).pack(side="left", fill="x", expand=True, ipady=5, ipadx=6)

        ttk.Button(row, text="Обзор…", style="Browse.TButton",
                   command=self._browse).pack(side="left", padx=(8, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Выберите Excel-файл",
            filetypes=[("Excel файлы", "*.xlsx *.xlsm"), ("Все файлы", "*.*")],
        )
        if path:
            self.path_var.set(path)

    @property
    def path(self) -> str:
        return self.path_var.get().strip()
