from typing import Optional

from sheets_client import get_history_sheet, get_sheet
from sheets_schema import (
    ASSIGNED_EMPLOYEE_COLUMN,
    CONTACT_INFO_COLUMN,
    CREATOR_COLUMN,
    HEADERS,
    HISTORY_HEADERS,
    NOTE_COLUMN,
    OBJECT_NAME_COLUMN,
    ADDRESS_COLUMN,
    DESCRIPTION_COLUMN,
    RequestRow,
    HistoryRow,
    STATUS_COLUMN,
    STATUS_NEW,
    TIME_COLUMN,
    URGENCY_COLUMN,
    EQUIPMENT_COLUMN,
)


def get_request_ids() -> list[str]:
    sheet = get_sheet()
    values = sheet.col_values(1)
    return [value.strip() for value in values[1:]]


def find_request_row(request_id: str) -> Optional[int]:
    normalized_request_id = request_id.strip()
    if not normalized_request_id:
        return None

    request_ids = get_request_ids()
    for index, value in enumerate(request_ids, start=2):
        if value == normalized_request_id:
            return index
    return None


def get_request_lookup_debug(request_id: str) -> str:
    normalized_request_id = request_id.strip()
    request_ids = get_request_ids()
    recent_request_ids = ", ".join(request_ids[-5:]) if request_ids else "пусто"
    return (
        f"Искали ID: {normalized_request_id}\n"
        f"Последние ID в таблице: {recent_request_ids}"
    )


def _parse_contact_info(contact_info: str) -> tuple[str, str]:
    parts = [part.strip() for part in contact_info.split("|", maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    if parts:
        return parts[0], ""
    return "", ""


def _build_request_row_dict(row_values: list[str], row_number: int) -> RequestRow:
    normalized_values = row_values + [""] * (len(HEADERS) - len(row_values))
    contact, phone = _parse_contact_info(normalized_values[CONTACT_INFO_COLUMN - 1].strip())
    return {
        "row_number": str(row_number),
        "id": normalized_values[0].strip(),
        "time": normalized_values[TIME_COLUMN - 1].strip(),
        "object_name": normalized_values[OBJECT_NAME_COLUMN - 1].strip(),
        "address": normalized_values[ADDRESS_COLUMN - 1].strip(),
        "description": normalized_values[DESCRIPTION_COLUMN - 1].strip(),
        "urgency": normalized_values[URGENCY_COLUMN - 1].strip(),
        "equipment": normalized_values[EQUIPMENT_COLUMN - 1].strip(),
        "contact": contact,
        "phone": phone,
        "contact_info": normalized_values[CONTACT_INFO_COLUMN - 1].strip(),
        "assigned_employee": normalized_values[ASSIGNED_EMPLOYEE_COLUMN - 1].strip(),
        "status": normalized_values[STATUS_COLUMN - 1].strip() or STATUS_NEW,
        "note": normalized_values[NOTE_COLUMN - 1].strip(),
        "creator": normalized_values[CREATOR_COLUMN - 1].strip(),
    }


def get_request_row(request_id: str) -> Optional[RequestRow]:
    sheet = get_sheet()
    row_number = find_request_row(request_id)
    if not row_number:
        return None

    row_values = sheet.row_values(row_number)
    return _build_request_row_dict(row_values, row_number)


def get_all_request_rows() -> list[RequestRow]:
    sheet = get_sheet()
    all_rows = sheet.get_all_values()
    request_rows: list[RequestRow] = []

    for row_number, row_values in enumerate(all_rows[1:], start=2):
        if not any(cell.strip() for cell in row_values):
            continue
        request_rows.append(_build_request_row_dict(row_values, row_number))

    return request_rows


def get_assigned_employee(request_id: str) -> Optional[str]:
    row = get_request_row(request_id)
    if not row:
        return None
    return row["assigned_employee"]


def get_request_history(request_id: str, limit: int = 10) -> list[HistoryRow]:
    history_sheet = get_history_sheet()
    all_rows = history_sheet.get_all_records()
    matched_rows = [row for row in all_rows if str(row.get("request_id", "")).strip() == request_id.strip()]
    recent_rows = matched_rows[-limit:]
    return [
        {
            "request_id": str(row.get("request_id", "")).strip(),
            "changed_at": str(row.get("changed_at", "")).strip(),
            "changed_by": str(row.get("changed_by", "")).strip(),
            "action": str(row.get("action", "")).strip(),
            "field_name": str(row.get("field_name", "")).strip(),
            "old_value": str(row.get("old_value", "")).strip(),
            "new_value": str(row.get("new_value", "")).strip(),
        }
        for row in recent_rows
    ]
