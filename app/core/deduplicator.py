"""
Дедупликация транзакций при обработке нескольких файлов.

Ключ уникальности: (date, round(debit, 2), round(credit, 2))
- Строки без даты никогда не дедуплицируются
- Побеждает первый файл по порядку обработки (алфавитный порядок)
- Все исключённые дубликаты сохраняются в AnalysisResult.deduplicated
  для последующей проверки
"""
from typing import Optional
from datetime import date

from app.core.models import (
    AnalysisResult, FolderResult, TransactionRow, DeduplicatedRow
)


def _make_key(t: TransactionRow) -> Optional[tuple]:
    """
    Ключ дедупликации. None если дата отсутствует —
    такие строки всегда сохраняются.
    """
    if t.date is None:
        return None
    return (t.date, round(t.debit, 2), round(t.credit, 2))


def deduplicate_folder(folder_result: FolderResult) -> FolderResult:
    """
    Проходит по всем файлам в папке и убирает дублирующиеся строки.
    Модифицирует объекты AnalysisResult на месте:
      - из SheetResult.transactions убираются дубликаты
      - в AnalysisResult.deduplicated добавляются исключённые строки

    Порядок файлов важен: первый файл имеет приоритет.
    """
    seen: dict[tuple, str] = {}  # key → filename первого вхождения

    for file_result in folder_result.files:
        for sheet in file_result.sheets:
            if sheet.error:
                continue

            unique_transactions = []
            for t in sheet.transactions:
                key = _make_key(t)

                if key is None:
                    # Нет даты — берём всегда
                    unique_transactions.append(t)
                    continue

                if key not in seen:
                    # Первое вхождение — запоминаем и берём
                    seen[key] = file_result.filename
                    unique_transactions.append(t)
                else:
                    # Дубликат — исключаем и логируем
                    file_result.deduplicated.append(DeduplicatedRow(
                        row=t,
                        source_file=file_result.filename,
                        original_file=seen[key],
                    ))

            sheet.transactions = unique_transactions

    return folder_result
