from datetime import datetime

from sheets_writes import append_history_row


def history_timestamp() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def append_history_entry(
    request_id: str,
    changed_by: str,
    action: str,
    field_name: str,
    old_value: str,
    new_value: str,
) -> None:
    append_history_row(
        [
            request_id,
            history_timestamp(),
            changed_by,
            action,
            field_name,
            old_value,
            new_value,
        ]
    )


def append_history_entries(entries: list[dict[str, str]]) -> None:
    for entry in entries:
        append_history_entry(**entry)
