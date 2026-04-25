import unittest

from presenters import build_request_message


class PresenterTests(unittest.TestCase):
    def test_build_request_message_includes_assignee(self) -> None:
        row = {
            "id": "REQ-TEST",
            "time": "25.03.2026 12:00",
            "object_name": "Объект",
            "address": "Адрес",
            "description": "Описание",
            "status": "В работе",
            "urgency": "высокая",
            "equipment": "Котел",
            "contact": "Иван",
            "phone": "+79991234567",
            "note": "Проверить срочно",
            "creator": "Петр",
            "assigned_employee": "Сотрудник",
        }
        message = build_request_message(row)
        self.assertIn("REQ-TEST", message)
        self.assertIn("Исполнитель: Сотрудник", message)
        self.assertIn("Примечание: Проверить срочно", message)

if __name__ == "__main__":
    unittest.main()
