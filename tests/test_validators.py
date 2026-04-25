import unittest

from validators import normalize_phone


class NormalizePhoneTests(unittest.TestCase):
    def test_accepts_number_with_plus_seven(self) -> None:
        self.assertEqual(normalize_phone("+79991234567"), "+79991234567")

    def test_converts_ten_digit_number(self) -> None:
        self.assertEqual(normalize_phone("9991234567"), "+79991234567")

    def test_converts_eight_prefix_to_plus_seven(self) -> None:
        self.assertEqual(normalize_phone("89991234567"), "+79991234567")

    def test_rejects_invalid_characters(self) -> None:
        self.assertIsNone(normalize_phone("7999-abc-4567"))

    def test_rejects_invalid_length(self) -> None:
        self.assertIsNone(normalize_phone("12345"))


if __name__ == "__main__":
    unittest.main()
