"""
Таблица результатов с кнопками копирования дебита и кредита.

Копирование значения:
  - Клик на 📋 рядом с дебитом → копирует число дебита
  - Клик на 📋 рядом с кредитом → копирует число кредита
  - Формат: "1234567,89" (без пробелов, запятая как разделитель)
  - Иконка меняется на ✓, через COPY_REVERT_MS возвращается

Копирование всего вывода:
  - Кнопка «Копировать всё» → TSV → вставляется по ячейкам в Excel/Sheets
"""
import tkinter as tk
import tkinter.ttk as ttk

from app.ui import styles
from app.core.models import AnalysisResult, FolderResult

COPY_REVERT_MS = 2000
ICON_COPY    = "📋"
ICON_SUCCESS = "✓"


def _fmt(v: float) -> str:
    """Форматирование для отображения: '1 234 567,89'"""
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


def _fmt_copy(v: float) -> str:
    """Форматирование для копирования: '1234567,89'"""
    return f"{v:.2f}".replace(".", ",")


def _row_to_tsv(values: tuple, copy_cols: set[int]) -> str:
    """Строка таблицы → TSV, пропуская колонки с иконками копирования."""
    return "\t".join(
        str(v) for i, v in enumerate(values)
        if i not in copy_cols
    )


class ResultsTable(tk.Frame):
    """
    Treeview с колонками-кнопками копирования рядом с дебитом и кредитом.

    Структура колонок:
      name | debit | copy_d | credit | copy_c | diff | excluded | dedup | status
    """

    # Базовые колонки (без кнопок копирования)
    _COLS = (
        ("name",     "Название",        200, "w"),
        ("debit",    "Дебит",           120, "e"),
        ("copy_d",   "",                 36, "center"),
        ("credit",   "Кредит",          120, "e"),
        ("copy_c",   "",                 36, "center"),
        ("diff",     "Разница",         120, "e"),
        ("excluded", "Вклады",           70, "e"),
        ("dedup",    "Дубли",            60, "e"),
        ("status",   "Статус",          110, "w"),
    )

    # Индексы колонок с иконками (для пропуска в TSV)
    _COPY_D_IDX = 2
    _COPY_C_IDX = 4
    _COPY_COLS  = {_COPY_D_IDX, _COPY_C_IDX}

    # Индексы значений дебита и кредита (для копирования числа)
    _DEBIT_IDX  = 1
    _CREDIT_IDX = 3

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=styles.CARD, bd=0,
                         highlightthickness=1,
                         highlightbackground=styles.BORDER, **kwargs)
        self._revert_jobs: dict[str, dict[str, str]] = {}
        self._build()

    # ── Построение ────────────────────────────────────────────────────────────

    def _build(self):
        col_ids = tuple(c[0] for c in self._COLS)
        self.tree = ttk.Treeview(self, columns=col_ids,
                                 show="headings", style="Results.Treeview",
                                 selectmode="browse")

        for col_id, header, width, anchor in self._COLS:
            self.tree.heading(col_id, text=header)
            stretch = col_id not in ("copy_d", "copy_c")
            self.tree.column(col_id, width=width, minwidth=width if not stretch else 50,
                             anchor=anchor, stretch=stretch)

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

    # ── Вставка строк ─────────────────────────────────────────────────────────

    def _make_row(self, name, debit, credit, diff, excluded, dedup, status,
                  show_copy=True) -> tuple:
        """Собирает кортеж значений с иконками копирования."""
        icon = ICON_COPY if show_copy else ""
        return (name, debit, icon, credit, icon, diff, excluded, dedup, status)

    def _insert(self, parent, values: tuple, tags: tuple, open_=False) -> str:
        return self.tree.insert(parent, "end", values=values,
                                tags=tags, open=open_)

    # ── Наполнение: один файл ─────────────────────────────────────────────────

    def populate_file(self, result: AnalysisResult):
        self.clear()
        for i, sheet in enumerate(result.sheets):
            tag = "error" if sheet.error else ("alt" if i % 2 else "ok")
            if sheet.error:
                vals = self._make_row(
                    sheet.sheet_name, "—", "—", "—", "—", "—",
                    f"⚠ {sheet.error}", show_copy=False)
            else:
                vals = self._make_row(
                    sheet.sheet_name,
                    _fmt(sheet.debit), _fmt(sheet.credit),
                    _fmt(sheet.difference),
                    str(sheet.excluded_rows), "—", "✓ ОК")
            self._insert("", vals, (tag,))

        self._insert("", self._make_row(
            "ИТОГО",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference), "", "", "",
        ), ("total",))

    # ── Наполнение: папка ─────────────────────────────────────────────────────

    def populate_folder(self, result: FolderResult):
        self.clear()
        for file_result in result.files:
            dedup_count = file_result.deduplicated_count
            dedup_label = str(dedup_count) if dedup_count else "—"

            # Статус строго программно: посчитано / ошибка чтения / нет операций,
            # а для посчитанных — результат сверки с оборотом банка из файла.
            st = file_result.status
            if st == "ok":
                d_s = _fmt(file_result.total_debit)
                c_s = _fmt(file_result.total_credit)
                diff_s = _fmt(file_result.total_difference)
                rec = file_result.reconciled
                if rec is True:
                    status = "✓ сверено с банком"
                    file_tag = "dedup_warn" if dedup_count else "file_row"
                elif rec is False:
                    status = "⚠ не сошлось — проверить"
                    file_tag = "dedup_warn"   # оранжевый — привлечь внимание
                else:
                    status = "✓ посчитано"
                    file_tag = "dedup_warn" if dedup_count else "file_row"
            else:
                # Ошибка чтения или нет операций — сумм нет, показываем прочерки.
                icon = {"read_error": "✗", "no_data": "—"}[st]
                status = f"{icon} {file_result.status_label}"
                d_s = c_s = diff_s = "—"
                file_tag = "error" if st == "read_error" else "sheet_row"

            node = self._insert("", self._make_row(
                f"📄 {file_result.filename}",
                d_s, c_s, diff_s,
                "", dedup_label, status,
                show_copy=(st == "ok"),
            ), (file_tag,), open_=False)

            # Файловая ошибка чтения (файл не открылся) — показываем причину.
            if file_result.error:
                self._insert(node, self._make_row(
                    f"  └ ⚠ {file_result.error}",
                    "—", "—", "—", "—", "—", "", show_copy=False,
                ), ("error",))

            for sheet in file_result.sheets:
                tag = "error" if sheet.error else "sheet_row"
                if sheet.error:
                    s_vals = self._make_row(
                        f"  └ {sheet.sheet_name}",
                        "—", "—", "—", "—", "—",
                        f"⚠ {sheet.error}", show_copy=False)
                else:
                    s_vals = self._make_row(
                        f"  └ {sheet.sheet_name}",
                        _fmt(sheet.debit), _fmt(sheet.credit),
                        _fmt(sheet.difference),
                        str(sheet.excluded_rows), "—", "")
                self._insert(node, s_vals, (tag,))

            if file_result.deduplicated:
                dup_node = self._insert(node, self._make_row(
                    f"  └ ⚠ Исключено дублей: {dedup_count}",
                    "", "", "", "", "", "", show_copy=False,
                ), ("dedup_warn",))
                for dr in file_result.deduplicated:
                    d_str = str(dr.row.date) if dr.row.date else "б/д"
                    self._insert(dup_node, self._make_row(
                        f"    • {d_str}  уже в: {dr.original_file}",
                        _fmt(dr.row.debit) if dr.row.debit else "—",
                        _fmt(dr.row.credit) if dr.row.credit else "—",
                        "", "", "", "", show_copy=False,
                    ), ("dedup_warn",))

        self._insert("", self._make_row(
            "ИТОГО ПО ПАПКЕ (без дублей)",
            _fmt(result.total_debit), _fmt(result.total_credit),
            _fmt(result.total_difference),
            "", str(result.total_deduplicated) if result.total_deduplicated else "—", "",
        ), ("total",))

    def clear(self):
        for jobs in self._revert_jobs.values():
            for job in jobs.values():
                try:
                    self.tree.after_cancel(job)
                except Exception:
                    pass
        self._revert_jobs.clear()
        self.tree.delete(*self.tree.get_children())

    # ── Обработка кликов ──────────────────────────────────────────────────────

    def _on_click(self, event: tk.Event):
        col = self.tree.identify_column(event.x)   # "#1", "#2", …
        row = self.tree.identify_row(event.y)
        if not row:
            return

        col_num = int(col.lstrip("#")) - 1          # 0-based

        if col_num == self._COPY_D_IDX:
            self._copy_value(row, self._DEBIT_IDX, "d")
        elif col_num == self._COPY_C_IDX:
            self._copy_value(row, self._CREDIT_IDX, "c")

    def _copy_value(self, item_id: str, value_idx: int, key: str):
        """
        Копирует числовое значение из value_idx в буфер.
        key: 'd' для дебита, 'c' для кредита — разделяет таймеры.
        """
        values = list(self.tree.item(item_id, "values"))
        raw = values[value_idx]

        # Пропускаем нечисловые ячейки
        if not raw or raw in ("—", ""):
            return

        # Преобразуем отображаемый формат обратно в число для копирования:
        # "1 234 567,89" → "1234567,89"
        number_str = raw.replace(" ", "").replace("\xa0", "")
        # Уже с запятой как разделителем — оставляем как есть
        self._clipboard_set(number_str)

        # Меняем иконку рядом с нужным столбцом
        icon_idx = self._COPY_D_IDX if key == "d" else self._COPY_C_IDX
        values[icon_idx] = ICON_SUCCESS
        self.tree.item(item_id, values=values)

        # Отменяем старый таймер для этой ячейки
        jobs = self._revert_jobs.setdefault(item_id, {})
        if key in jobs:
            try:
                self.tree.after_cancel(jobs[key])
            except Exception:
                pass

        job = self.tree.after(
            COPY_REVERT_MS,
            lambda: self._revert_icon(item_id, icon_idx, key)
        )
        jobs[key] = job

    def _revert_icon(self, item_id: str, icon_idx: int, key: str):
        try:
            values = list(self.tree.item(item_id, "values"))
            values[icon_idx] = ICON_COPY
            self.tree.item(item_id, values=values)
        except tk.TclError:
            pass
        self._revert_jobs.get(item_id, {}).pop(key, None)

    def _clipboard_set(self, text: str):
        self.tree.clipboard_clear()
        self.tree.clipboard_append(text)
        self.tree.update()

    # ── TSV для «Копировать всё» ──────────────────────────────────────────────

    def get_all_as_tsv(self) -> str:
        """Вся таблица как TSV без колонок-иконок."""
        headers = [c[1] for i, c in enumerate(self._COLS)
                   if i not in self._COPY_COLS]
        lines = ["\t".join(headers)]

        def collect(item):
            values = self.tree.item(item, "values")
            if values:
                lines.append(_row_to_tsv(values, self._COPY_COLS))
            for child in self.tree.get_children(item):
                collect(child)

        for item in self.tree.get_children():
            collect(item)

        return "\n".join(lines)
