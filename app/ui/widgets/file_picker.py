import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from app.ui import styles


class FilePicker(tk.Frame):
    """
    Карточка выбора источника данных.
    Режим переключается кнопками: Файл / Папка.
    """

    MODE_FILE   = "file"
    MODE_FOLDER = "folder"

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.CARD, bd=0,
                         highlightthickness=1,
                         highlightbackground=styles.BORDER, **kwargs)
        self.path_var = tk.StringVar()
        self._mode = self.MODE_FILE
        self._build()

    def _build(self):
        inner = tk.Frame(self, bg=styles.CARD, padx=12, pady=10)
        inner.pack(fill="x")

        # Переключатель режима
        toggle_row = tk.Frame(inner, bg=styles.CARD)
        toggle_row.pack(anchor="w", pady=(0, 8))

        tk.Label(toggle_row, text="Режим:", bg=styles.CARD,
                 fg=styles.MUTED, font=("Segoe UI", 8)).pack(side="left", padx=(0, 8))

        self._btn_file = self._mode_btn(toggle_row, "Один файл", self.MODE_FILE)
        self._btn_file.pack(side="left", padx=(0, 4))

        self._btn_folder = self._mode_btn(toggle_row, "Папка", self.MODE_FOLDER)
        self._btn_folder.pack(side="left")

        # Подпись
        self._label_var = tk.StringVar(value="Путь к файлу")
        tk.Label(inner, textvariable=self._label_var, bg=styles.CARD,
                 fg=styles.MUTED, font=("Segoe UI", 8)).pack(anchor="w")

        # Поле ввода + кнопка
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

        self._refresh_toggle()

    def _mode_btn(self, parent, text, mode) -> tk.Label:
        """Кнопка-таб для переключения режима."""
        lbl = tk.Label(parent, text=text, bg=styles.CARD,
                       fg=styles.MUTED, font=("Segoe UI", 9),
                       cursor="hand2", padx=10, pady=3,
                       relief="flat", bd=1)
        lbl.bind("<Button-1>", lambda e: self._set_mode(mode))
        return lbl

    def _set_mode(self, mode: str):
        self._mode = mode
        self.path_var.set("")
        self._refresh_toggle()

    def _refresh_toggle(self):
        if self._mode == self.MODE_FILE:
            self._btn_file.config(bg=styles.ACCENT, fg="white",
                                  relief="solid")
            self._btn_folder.config(bg=styles.CARD, fg=styles.MUTED,
                                    relief="flat")
            self._label_var.set("Путь к файлу")
        else:
            self._btn_folder.config(bg=styles.ACCENT, fg="white",
                                    relief="solid")
            self._btn_file.config(bg=styles.CARD, fg=styles.MUTED,
                                  relief="flat")
            self._label_var.set("Путь к папке")

    def _browse(self):
        if self._mode == self.MODE_FILE:
            path = filedialog.askopenfilename(
                title="Выберите Excel-файл",
                filetypes=[("Excel файлы", "*.xlsx *.xlsm"), ("Все файлы", "*.*")],
            )
        else:
            path = filedialog.askdirectory(title="Выберите папку с Excel-файлами")
        if path:
            self.path_var.set(path)

    @property
    def path(self) -> str:
        return self.path_var.get().strip()

    @property
    def mode(self) -> str:
        return self._mode
