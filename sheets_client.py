from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from sheets_schema import (
    EMPLOYEE_ACTIVITY_HEADERS,
    HEADERS,
    HISTORY_HEADERS,
    HISTORY_WORKSHEET_NAME,
    PROJECT_ROOT,
    SERVICE_ACCOUNT_FILE,
    SPREADSHEET_KEY,
    WORKSHEET_NAME,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_spreadsheet = None
_sheet = None
_history_sheet = None
_employee_sheets = {}


def _resolve_service_account_file() -> Path:
    credentials_path = Path(SERVICE_ACCOUNT_FILE).expanduser()
    if not credentials_path.is_absolute():
        credentials_path = PROJECT_ROOT / credentials_path
    return credentials_path


def get_spreadsheet():
    global _spreadsheet

    if _spreadsheet is not None:
        return _spreadsheet

    if not SPREADSHEET_KEY:
        raise RuntimeError("SPREADSHEET_KEY не найден. Укажите его в файле .env")

    credentials_path = _resolve_service_account_file()
    if not credentials_path.exists():
        raise FileNotFoundError(f"Файл сервисного аккаунта не найден: {credentials_path}")

    creds = Credentials.from_service_account_file(str(credentials_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    _spreadsheet = client.open_by_key(SPREADSHEET_KEY)
    return _spreadsheet


def ensure_headers() -> None:
    sheet = _sheet
    if sheet is None:
        return

    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.update("A1:L1", [HEADERS], value_input_option="RAW")


def ensure_history_headers() -> None:
    history_sheet = _history_sheet
    if history_sheet is None:
        return

    first_row = history_sheet.row_values(1)
    if first_row != HISTORY_HEADERS:
        history_sheet.update("A1:G1", [HISTORY_HEADERS], value_input_option="RAW")


def get_sheet():
    global _sheet

    if _sheet is not None:
        return _sheet

    spreadsheet = get_spreadsheet()
    _sheet = spreadsheet.worksheet(WORKSHEET_NAME) if WORKSHEET_NAME else spreadsheet.sheet1
    ensure_headers()
    return _sheet


def get_history_sheet():
    global _history_sheet

    if _history_sheet is not None:
        return _history_sheet

    spreadsheet = get_spreadsheet()
    try:
        _history_sheet = spreadsheet.worksheet(HISTORY_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        _history_sheet = spreadsheet.add_worksheet(title=HISTORY_WORKSHEET_NAME, rows=1000, cols=7)

    ensure_history_headers()
    return _history_sheet


def _sanitize_worksheet_title(title: str) -> str:
    sanitized = "".join("_" if char in "\\/?*[]:" else char for char in title).strip()
    sanitized = sanitized[:100].strip()
    return sanitized or "employee"


def get_employee_sheet(employee_name: str):
    title = _sanitize_worksheet_title(employee_name.strip())
    if title in _employee_sheets:
        return _employee_sheets[title]

    spreadsheet = get_spreadsheet()
    try:
        employee_sheet = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        employee_sheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(EMPLOYEE_ACTIVITY_HEADERS))

    first_row = employee_sheet.row_values(1)
    if first_row != EMPLOYEE_ACTIVITY_HEADERS:
        employee_sheet.update("A1:F1", [EMPLOYEE_ACTIVITY_HEADERS], value_input_option="RAW")

    _employee_sheets[title] = employee_sheet
    return employee_sheet
