from typing import TypeAlias

RequestRow: TypeAlias = dict[str, str]

def build_request_text(data: dict[str, str], request_id: str, created_at: str, creator_display: str) -> str:
    text = (
        "Заявка\n"
        "--------------------\n"
        f"ID: {request_id}\n"
        f"Статус: {data['status']}\n"
        f"Время: {created_at}\n"
        "--------------------\n"
        f"Название объекта: {data['object_name']}\n"
        f"Адрес объекта: {data['address']}\n"
        f"Описание: {data['description']}\n"
        f"Срочность: {data['urgency']}\n"
        f"Вид оборудования: {data['equipment']}\n"
        "--------------------\n"
        f"Контакт: {data['contact']}\n"
        f"Телефон: {data['phone']}\n"
        f"Создатель заявки: {creator_display}"
    )
    if data.get("note"):
        text = f"{text}\n--------------------\nПримечание: {data['note']}"
    return text


def build_request_text_from_sheet_row(row: RequestRow) -> str:
    return build_request_text(
        data={
            "object_name": row["object_name"],
            "address": row["address"],
            "description": row["description"],
            "status": row["status"],
            "urgency": row["urgency"],
            "equipment": row["equipment"],
            "contact": row["contact"],
            "phone": row["phone"],
            "note": row["note"],
        },
        request_id=row["id"],
        created_at=row["time"],
        creator_display=row["creator"],
    )


def build_request_message(row: RequestRow) -> str:
    text = build_request_text_from_sheet_row(row)
    if row["assigned_employee"]:
        text = f"{text}\n\nИсполнитель: {row['assigned_employee']}"
    return text
