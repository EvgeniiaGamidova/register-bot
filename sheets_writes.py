from gspread.utils import rowcol_to_a1

from sheets_client import get_employee_sheet, get_history_sheet, get_sheet, get_spreadsheet
from sheets_queries import get_request_row
from sheets_schema import (
    ASSIGNED_EMPLOYEE_COLUMN,
    CONTACT_INFO_COLUMN,
    EMPLOYEE_ACTIVITY_HEADERS,
    FIELD_TO_COLUMN,
    HEADERS,
    NOTE_COLUMN,
    STATUS_CANCELED,
    STATUS_COLUMN,
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    STATUS_NEW,
    STATUS_ROW_COLORS,
)


def append_request_row(row: list[str]) -> None:
    sheet = get_sheet()
    sheet.append_row(row, value_input_option="RAW")


def apply_status_color(request_id: str, status: str) -> bool:
    row = get_request_row(request_id)
    if not row:
        return False
    return apply_status_color_to_row(int(row["row_number"]), status)


def apply_status_color_to_row(row_number: int, status: str) -> bool:
    if row_number <= 1:
        return False

    sheet = get_sheet()
    spreadsheet = get_spreadsheet()
    background_color = STATUS_ROW_COLORS.get(status, STATUS_ROW_COLORS[STATUS_NEW])

    spreadsheet.batch_update(
        {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet.id,
                            "startRowIndex": row_number - 1,
                            "endRowIndex": row_number,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(HEADERS),
                        },
                        "cell": {"userEnteredFormat": {"backgroundColor": background_color}},
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                }
            ]
        }
    )
    return True


def append_history_row(row: list[str]) -> None:
    history_sheet = get_history_sheet()
    history_sheet.append_row(row, value_input_option="RAW")


def append_employee_activity(
    employee_name: str,
    *,
    request_id: str,
    logged_at: str,
    action: str,
    status: str,
    object_name: str,
    address: str,
) -> None:
    if not employee_name.strip() or action != "Завершил заявку" or status != STATUS_COMPLETED:
        return

    employee_sheet = get_employee_sheet(employee_name)
    employee_sheet.append_row(
        [request_id, logged_at, action, status, object_name, address],
        value_input_option="RAW",
    )


def _update_cell_and_verify(request_id: str, row_number: int, column: int, value: str, field_name: str) -> bool:
    sheet = get_sheet()
    sheet.update_cell(row_number, column, value)
    refreshed_row = get_request_row(request_id)
    return bool(refreshed_row and refreshed_row[field_name] == value)


def _update_row_range(row_number: int, start_column: int, values: list[str]) -> None:
    sheet = get_sheet()
    start_cell = rowcol_to_a1(row_number, start_column)
    end_cell = rowcol_to_a1(row_number, start_column + len(values) - 1)
    sheet.update(f"{start_cell}:{end_cell}", [values], value_input_option="RAW")


def _build_contact_info(contact: str, phone: str) -> str:
    return f"{contact} | {phone}".strip()


def _update_assignment_and_status(
    request_id: str,
    *,
    assigned_employee: str,
    status: str,
) -> bool:
    row = get_request_row(request_id)
    if not row:
        return False

    row_number = int(row["row_number"])
    _update_row_range(
        row_number=row_number,
        start_column=ASSIGNED_EMPLOYEE_COLUMN,
        values=[assigned_employee, status],
    )
    refreshed_row = get_request_row(request_id)
    return bool(
        refreshed_row
        and refreshed_row["assigned_employee"] == assigned_employee
        and refreshed_row["status"] == status
    )


def _update_status(request_id: str, status: str) -> bool:
    row = get_request_row(request_id)
    if not row:
        return False

    return _update_cell_and_verify(
        request_id=request_id,
        row_number=int(row["row_number"]),
        column=STATUS_COLUMN,
        value=status,
        field_name="status",
    )


def assign_request(request_id: str, employee_display: str) -> bool:
    row = get_request_row(request_id)
    if not row or row["assigned_employee"]:
        return False

    return _update_assignment_and_status(
        request_id,
        assigned_employee=employee_display,
        status=STATUS_IN_PROGRESS,
    )


def unassign_request(request_id: str) -> bool:
    return _update_assignment_and_status(
        request_id,
        assigned_employee="",
        status=STATUS_NEW,
    )


def mark_request_completed(request_id: str) -> bool:
    return _update_status(request_id, STATUS_COMPLETED)


def cancel_request(request_id: str) -> bool:
    return _update_assignment_and_status(
        request_id,
        assigned_employee="",
        status=STATUS_CANCELED,
    )


def update_request_field(request_id: str, field_name: str, value: str) -> bool:
    row = get_request_row(request_id)
    if not row:
        return False

    row_number = int(row["row_number"])

    if field_name in FIELD_TO_COLUMN:
        return _update_cell_and_verify(
            request_id=request_id,
            row_number=row_number,
            column=FIELD_TO_COLUMN[field_name],
            value=value,
            field_name=field_name,
        )
    if field_name == "contact":
        updated_contact_info = _build_contact_info(value, row["phone"])
        return _update_cell_and_verify(
            request_id=request_id,
            row_number=row_number,
            column=CONTACT_INFO_COLUMN,
            value=updated_contact_info,
            field_name="contact_info",
        )
    if field_name == "phone":
        updated_contact_info = _build_contact_info(row["contact"], value)
        return _update_cell_and_verify(
            request_id=request_id,
            row_number=row_number,
            column=CONTACT_INFO_COLUMN,
            value=updated_contact_info,
            field_name="contact_info",
        )

    return False


def update_request_note(request_id: str, note: str) -> bool:
    sheet = get_sheet()
    row = get_request_row(request_id)
    if not row:
        return False

    row_number = int(row["row_number"])
    sheet.update_cell(row_number, NOTE_COLUMN, note)

    refreshed_row = get_request_row(request_id)
    if not refreshed_row:
        return False
    return refreshed_row["note"] == note
