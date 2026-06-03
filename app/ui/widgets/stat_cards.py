import tkinter as tk
from app.ui import styles
from app.ui.widgets.results_table import ICON_COPY, ICON_SUCCESS, COPY_REVERT_MS


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def _fmt_copy(v: float) -> str:
    return f"{v:.2f}".replace(".", ",")


class StatCards(tk.Frame):
    """Три карточки: Дебит / Кредит / Разница с кнопками копирования."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.BG, **kwargs)
        self._values: dict[str, float] = {}
        self._copy_vars: dict[str, tk.StringVar] = {}
        self._revert_jobs: dict[str, str] = {}
        self._value_labels: dict[str, tk.Label] = {}
        self._build()

    def _build(self):
        for i, title in enumerate(("Дебит", "Кредит", "Разница")):
            card = tk.Frame(self, bg=styles.CARD, bd=0,
                            highlightthickness=1,
                            highlightbackground=styles.BORDER)
            card.grid(row=0, column=i, sticky="ew",
                      padx=(0 if i == 0 else 8, 0))
            self.columnconfigure(i, weight=1)

            inner = tk.Frame(card, bg=styles.CARD, padx=14, pady=10)
            inner.pack(fill="both")

            # Заголовок карточки + кнопка копирования
            header_row = tk.Frame(inner, bg=styles.CARD)
            header_row.pack(fill="x")

            tk.Label(header_row, text=title, bg=styles.CARD,
                     fg=styles.MUTED, font=("Segoe UI", 9)).pack(side="left")

            copy_var = tk.StringVar(value=ICON_COPY)
            self._copy_vars[title] = copy_var

            copy_btn = tk.Label(header_row, textvariable=copy_var,
                                bg=styles.CARD, fg=styles.MUTED,
                                font=("Segoe UI", 9), cursor="hand2",
                                padx=4)
            copy_btn.pack(side="right")
            copy_btn.bind("<Button-1>", lambda e, t=title: self._copy(t))

            # Значение
            val_lbl = tk.Label(inner, text="—", bg=styles.CARD,
                               fg=styles.TEXT,
                               font=("Segoe UI", 16, "bold"))
            val_lbl.pack(anchor="w", pady=(2, 0))
            self._value_labels[title] = val_lbl

    def update(self, debit: float, credit: float, difference: float):
        self._values = {"Дебит": debit, "Кредит": credit, "Разница": difference}
        self._value_labels["Дебит"].config(text=_fmt(debit))
        self._value_labels["Кредит"].config(text=_fmt(credit))
        self._value_labels["Разница"].config(
            text=_fmt(difference),
            fg=styles.GREEN if difference >= 0 else styles.RED,
        )

    def reset(self):
        self._values = {}
        for lbl in self._value_labels.values():
            lbl.config(text="—", fg=styles.TEXT)
        for var in self._copy_vars.values():
            var.set(ICON_COPY)

    def _copy(self, title: str):
        if title not in self._values:
            return

        number_str = _fmt_copy(self._values[title])
        self.clipboard_clear()
        self.clipboard_append(number_str)
        tk.Frame.update(self)  # flush clipboard, не вызывать наш update()

        self._copy_vars[title].set(ICON_SUCCESS)

        if title in self._revert_jobs:
            try:
                self.after_cancel(self._revert_jobs[title])
            except Exception:
                pass

        job = self.after(COPY_REVERT_MS,
                         lambda t=title: self._copy_vars[t].set(ICON_COPY))
        self._revert_jobs[title] = job
