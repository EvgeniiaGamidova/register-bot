import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

STORE_PATH = Path(__file__).resolve().parent / "request_meta.json"
STORE_LOCK = threading.Lock()


def _read_store() -> dict[str, Any]:
    if not STORE_PATH.exists():
        return {"requests": {}, "last_request_by_user": {}}

    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"requests": {}, "last_request_by_user": {}}


def _write_store(data: dict[str, Any]) -> None:
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=STORE_PATH.parent,
        prefix=f"{STORE_PATH.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(serialized)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_path = Path(temp_file.name)

    os.replace(temp_path, STORE_PATH)

    try:
        directory_fd = os.open(STORE_PATH.parent, os.O_RDONLY)
    except OSError:
        return

    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def save_request_meta(request_id: str, creator_user_id: int, group_message_id: int | None) -> None:
    with STORE_LOCK:
        data = _read_store()
        data["requests"][request_id] = {
            "creator_user_id": creator_user_id,
            "group_message_id": group_message_id,
        }
        data["last_request_by_user"][str(creator_user_id)] = request_id
        _write_store(data)


def get_request_meta(request_id: str) -> dict[str, Any] | None:
    data = _read_store()
    return data["requests"].get(request_id)


def get_last_request_id_for_user(user_id: int) -> str | None:
    data = _read_store()
    return data["last_request_by_user"].get(str(user_id))
