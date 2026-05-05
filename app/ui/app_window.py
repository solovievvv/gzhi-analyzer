import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import threading

from app.ui import styles
from app.ui.widgets.file_picker import FilePicker
from app.ui.widgets.stat_cards import StatCards
from app.ui.widgets.results_table import ResultsTable
from app.core.reader import process_file, process_folder


class AppWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Анализ дебита и кредита")
        self.geometry("860x600")
        self.minsize(700, 500)
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
                 text="Загрузите Excel-файл или папку — приложение найдёт столбцы и подсчитает итоги.",
                 bg=styles.BG, fg=styles.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 12))

        # Выбор файла / папки
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
            messagebox.showwarning("Не выбрано",
                                   "Укажите путь к файлу или папке.")
            return
        self.analyze_btn.configure(state="disabled")
        self._status_var.set("Обработка…")
        self.table.clear()
        self.stat_cards.reset()

        mode = self.file_picker.mode
        threading.Thread(target=self._run, args=(path, mode), daemon=True).start()

    def _run(self, path: str, mode: str):
        try:
            if mode == FilePicker.MODE_FILE:
                result = process_file(path)
                self.after(0, self._show_file, result)
            else:
                result = process_folder(path)
                self.after(0, self._show_folder, result)
        except Exception as e:
            self.after(0, self._error, str(e))

    def _show_file(self, result):
        self.table.populate_file(result)
        self.stat_cards.update(result.total_debit,
                               result.total_credit,
                               result.total_difference)
        n = len(result.sheets)
        self._status_var.set(f"Готово · {n} лист{'ов' if n != 1 else ''}")
        self.analyze_btn.configure(state="normal")

    def _show_folder(self, result):
        self.table.populate_folder(result)
        self.stat_cards.update(result.total_debit,
                               result.total_credit,
                               result.total_difference)
        n = len(result.files)
        self._status_var.set(f"Готово · {n} файл{'ов' if n % 10 != 1 or n % 100 == 11 else ''} обработано")
        self.analyze_btn.configure(state="normal")

    def _error(self, message: str):
        self._status_var.set("Ошибка при обработке")
        self.analyze_btn.configure(state="normal")
        messagebox.showerror("Ошибка", message)
