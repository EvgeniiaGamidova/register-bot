import os
from pathlib import Path

from env import load_env

load_env()

PROJECT_ROOT = Path(__file__).resolve().parent
SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY", "").strip()
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "").strip() or None
HISTORY_WORKSHEET_NAME = os.getenv("HISTORY_WORKSHEET_NAME", "history").strip() or "history"
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service-account.json").strip() or "service-account.json"

STATUS_NEW = "Новая"
STATUS_IN_PROGRESS = "В работе"
STATUS_ISSUE = "Есть проблема"
STATUS_COMPLETED = "Выполнено"
STATUS_CANCELED = "Отменена"

HEADERS = [
    "id",
    "Время",
    "Наименование объекта",
    "Адресс объекта",
    "Описание",
    "Срочность",
    "Вид оборудования",
    "Контактное лицо и телефон",
    "Назначеный сотрудник",
    "Статус",
    "Примечание",
    "Создатель заявки",
]

HISTORY_HEADERS = [
    "request_id",
    "changed_at",
    "changed_by",
    "action",
    "field_name",
    "old_value",
    "new_value",
]

RequestRow = dict[str, str]
HistoryRow = dict[str, str]

TIME_COLUMN = 2
OBJECT_NAME_COLUMN = 3
ADDRESS_COLUMN = 4
DESCRIPTION_COLUMN = 5
URGENCY_COLUMN = 6
EQUIPMENT_COLUMN = 7
CONTACT_INFO_COLUMN = 8
ASSIGNED_EMPLOYEE_COLUMN = 9
STATUS_COLUMN = 10
NOTE_COLUMN = 11
CREATOR_COLUMN = 12

STATUS_ROW_COLORS = {
    STATUS_NEW: {"red": 1.0, "green": 1.0, "blue": 1.0},
    STATUS_IN_PROGRESS: {"red": 1.0, "green": 0.953, "blue": 0.8},
    STATUS_ISSUE: {"red": 0.996, "green": 0.863, "blue": 0.659},
    STATUS_COMPLETED: {"red": 0.859, "green": 0.941, "blue": 0.859},
    STATUS_CANCELED: {"red": 0.918, "green": 0.6, "blue": 0.6},
}

FIELD_TO_COLUMN = {
    "object_name": OBJECT_NAME_COLUMN,
    "address": ADDRESS_COLUMN,
    "description": DESCRIPTION_COLUMN,
    "status": STATUS_COLUMN,
    "urgency": URGENCY_COLUMN,
    "equipment": EQUIPMENT_COLUMN,
}

EMPLOYEE_ACTIVITY_HEADERS = [
    "request_id",
    "logged_at",
    "action",
    "status",
    "object_name",
    "address",
]
