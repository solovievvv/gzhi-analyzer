"""Цветовая палитра и настройка стилей ttk."""
import tkinter.ttk as ttk

BG     = "#F5F6FA"
CARD   = "#FFFFFF"
ACCENT = "#4A6CF7"
TEXT   = "#1E1E2E"
MUTED  = "#6B7280"
GREEN  = "#16A34A"
RED    = "#DC2626"
BORDER = "#E5E7EB"
ROW_ALT = "#F9FAFB"


def apply(root) -> None:
    """Применить все стили к корневому окну."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Header.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 13, "bold"))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))

    style.configure("Accent.TButton",
                    font=("Segoe UI", 10, "bold"), foreground="white",
                    background=ACCENT, relief="flat", padding=(16, 8))
    style.map("Accent.TButton",
              background=[("active", "#3B5CE4"), ("disabled", "#9CA3AF")],
              foreground=[("disabled", "#D1D5DB")])

    style.configure("Browse.TButton",
                    font=("Segoe UI", 9), foreground=TEXT,
                    background=CARD, relief="flat", padding=(10, 6))
    style.map("Browse.TButton", background=[("active", BORDER)])

    style.configure("Results.Treeview",
                    background=CARD, foreground=TEXT, font=("Segoe UI", 9),
                    rowheight=28, fieldbackground=CARD, relief="flat", borderwidth=0)
    style.configure("Results.Treeview.Heading",
                    background=BG, foreground=MUTED,
                    font=("Segoe UI", 9, "bold"), relief="flat", padding=(8, 6))
    style.map("Results.Treeview",
              background=[("selected", "#EEF2FF")],
              foreground=[("selected", TEXT)])
