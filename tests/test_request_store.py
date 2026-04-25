import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import request_store


class RequestStoreTests(unittest.TestCase):
    def test_save_request_meta_preserves_json_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "request_meta.json"
            with patch.object(request_store, "STORE_PATH", store_path):
                request_store.save_request_meta("REQ-1", 100, 200)
                request_store.save_request_meta("REQ-2", 101, 201)

                data = json.loads(store_path.read_text(encoding="utf-8"))

        self.assertEqual(data["requests"]["REQ-1"]["creator_user_id"], 100)
        self.assertEqual(data["requests"]["REQ-2"]["group_message_id"], 201)
        self.assertEqual(data["last_request_by_user"]["100"], "REQ-1")
        self.assertEqual(data["last_request_by_user"]["101"], "REQ-2")

    def test_get_last_request_id_for_user_returns_latest_saved_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "request_meta.json"
            with patch.object(request_store, "STORE_PATH", store_path):
                request_store.save_request_meta("REQ-1", 555, 1)
                request_store.save_request_meta("REQ-2", 555, 2)
                last_request_id = request_store.get_last_request_id_for_user(555)

        self.assertEqual(last_request_id, "REQ-2")


if __name__ == "__main__":
    unittest.main()
