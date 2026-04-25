PHONE_FORMAT_HINT = "Введите корректный телефон в формате 89991234567, 9991234567 или +79991234567."
URGENCY_VALUES = {
    "срочно": "Срочно",
    "не срочно": "Не срочно",
    "то": "ТО",
}


def normalize_phone(phone: str) -> str | None:
    normalized = phone.strip()
    if not normalized:
        return None

    allowed_chars = set("0123456789+()- ")
    if any(char not in allowed_chars for char in normalized):
        return None

    digits = "".join(char for char in normalized if char.isdigit())
    if len(digits) == 10:
        digits = f"7{digits}"
    elif len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    elif len(digits) == 11 and digits.startswith("7"):
        pass
    else:
        return None

    return f"+{digits}"
