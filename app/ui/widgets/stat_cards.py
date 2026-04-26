import tkinter as tk
from app.ui import styles


class StatCards(tk.Frame):
    """Три карточки: Дебит / Кредит / Разница."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.BG, **kwargs)
        self._labels: dict[str, tk.Label] = {}
        self._build()

    def _build(self):
        for i, title in enumerate(("Дебит", "Кредит", "Разница")):
            card = tk.Frame(self, bg=styles.CARD, bd=0,
                            highlightthickness=1,
                            highlightbackground=styles.BORDER)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
            self.columnconfigure(i, weight=1)

            inner = tk.Frame(card, bg=styles.CARD, padx=14, pady=10)
            inner.pack(fill="both")

            tk.Label(inner, text=title, bg=styles.CARD,
                     fg=styles.MUTED, font=("Segoe UI", 9)).pack(anchor="w")

            lbl = tk.Label(inner, text="—", bg=styles.CARD,
                           fg=styles.TEXT, font=("Segoe UI", 16, "bold"))
            lbl.pack(anchor="w", pady=(2, 0))
            self._labels[title] = lbl

    def update(self, debit: float, credit: float, difference: float):
        self._labels["Дебит"].config(text=_fmt(debit))
        self._labels["Кредит"].config(text=_fmt(credit))
        self._labels["Разница"].config(
            text=_fmt(difference),
            fg=styles.GREEN if difference >= 0 else styles.RED,
        )

    def reset(self):
        for lbl in self._labels.values():
            lbl.config(text="—", fg=styles.TEXT)


def _fmt(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")
