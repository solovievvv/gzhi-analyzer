import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading

from app.ui import styles
from app.ui.widgets.file_picker import FilePicker
from app.ui.widgets.stat_cards import StatCards
from app.ui.widgets.results_table import ResultsTable
from app.core.reader import process_file


class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Анализ дебита и кредита")
        self.geometry("820x560")
        self.minsize(680, 480)
        self.configure(bg=styles.BG)
        styles.apply(self)
        self._build()

    def _build(self):
        pad = tk.Frame(self, bg=styles.BG, padx=20, pady=16)
        pad.pack(fill="both", expand=True)

        # Заголовок
        tk.Label(pad, text="Анализ дебита и кредита",
                 font=("Segoe UI", 13, "bold"),
                 bg=styles.BG, fg=styles.TEXT).pack(anchor="w")
        tk.Label(pad,
                 text="Загрузите Excel-файл — приложение найдёт столбцы и подсчитает итоги.",
                 bg=styles.BG, fg=styles.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 12))

        # Выбор файла
        self.file_picker = FilePicker(pad)
        self.file_picker.pack(fill="x", pady=(0, 12))

        # Кнопка + статус
        btn_row = tk.Frame(pad, bg=styles.BG)
        btn_row.pack(fill="x", pady=(0, 16))

        self.analyze_btn = ttk.Button(btn_row, text="Рассчитать",
                                      style="Accent.TButton",
                                      command=self._start)
        self.analyze_btn.pack(side="left")

        self._status_var = tk.StringVar()
        tk.Label(btn_row, textvariable=self._status_var,
                 bg=styles.BG, fg=styles.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=12)

        # Карточки
        self.stat_cards = StatCards(pad)
        self.stat_cards.pack(fill="x", pady=(0, 12))

        # Таблица
        self.table = ResultsTable(pad)
        self.table.pack(fill="both", expand=True)

    # ── Действия ──────────────────────────────────────────────────────────────

    def _start(self):
        path = self.file_picker.path
        if not path:
            messagebox.showwarning("Файл не выбран", "Укажите путь к Excel-файлу.")
            return
        self.analyze_btn.configure(state="disabled")
        self._status_var.set("Обработка…")
        self.table.clear()
        self.stat_cards.reset()
        threading.Thread(target=self._run, args=(path,), daemon=True).start()

    def _run(self, path: str):
        try:
            result = process_file(path)
            self.after(0, self._show, result)
        except Exception as e:
            self.after(0, self._error, str(e))

    def _show(self, result):
        self.table.populate(result)
        self.stat_cards.update(result.total_debit, result.total_credit, result.total_difference)
        self._status_var.set(f"Готово · {len(result.sheets)} листов обработано")
        self.analyze_btn.configure(state="normal")

    def _error(self, message: str):
        self._status_var.set("Ошибка при обработке файла")
        self.analyze_btn.configure(state="normal")
        messagebox.showerror("Ошибка", message)
