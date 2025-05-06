from typing import List, Optional, Any, Dict
from .base import StorageProvider, StorageWriteError
from src.domain.session import TaskSession, TaskSessionStatus  # Import Enum as well
import os  # For default file path construction
import json  # Will be needed soon
from datetime import datetime, timedelta
from dataclasses import asdict

# from ...domain.session import TaskSession # Adjust path as needed

DEFAULT_STORAGE_DIR = os.path.expanduser("~/.task_timer")
DEFAULT_RECORDS_FILE = "records.json"


def session_to_dict(session: TaskSession) -> Dict[str, Any]:
    """Converts a TaskSession object to a JSON-serializable dictionary."""
    data = asdict(session)
    data["start_time"] = session.start_time.isoformat() if session.start_time else None
    if session.end_time:
        data["end_time"] = session.end_time.isoformat()
    else:
        data["end_time"] = None  # Ensure it's explicitly None if not set
    data["status"] = session.status.value  # Store enum by its value
    # _duration_override is already a timedelta or None,
    # json default handler won't like timedelta
    if session._duration_override is not None:
        data["_duration_override"] = session._duration_override.total_seconds()
    return data


def dict_to_session(data: Dict[str, Any]) -> TaskSession:
    """Converts a dictionary (from JSON) back to a TaskSession object."""
    start_time_str = data.get("start_time")
    data["start_time"] = datetime.fromisoformat(start_time_str) if start_time_str else None  # noqa: E501
    end_time_str = data.get("end_time")
    data["end_time"] = datetime.fromisoformat(end_time_str) if end_time_str else None
    data["status"] = TaskSessionStatus(data["status"])  # Recreate enum from value
    duration_override_seconds = data.get("_duration_override")
    if duration_override_seconds is not None:
        data["_duration_override"] = timedelta(seconds=duration_override_seconds)
    else:
        data["_duration_override"] = None  # Ensure it's None if not present
    return TaskSession(**data)


class JsonStorage(StorageProvider):
    """JSON-based storage provider for task sessions."""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            os.makedirs(DEFAULT_STORAGE_DIR, exist_ok=True)
            self.file_path = os.path.join(DEFAULT_STORAGE_DIR, DEFAULT_RECORDS_FILE)
        else:
            self.file_path = file_path
        # Ensure file exists for loading, or to be created on first save
        # if not os.path.exists(self.file_path):
        #     with open(self.file_path, 'w') as f:
        #         json.dump([], f)

    def _load_sessions_from_file(self) -> List[TaskSession]:
        try:
            if (
                not os.path.exists(self.file_path)
                or os.path.getsize(self.file_path) == 0
            ):
                return []
            with open(self.file_path, "r") as f:
                data_list = json.load(f)
            return [dict_to_session(data) for data in data_list]
        except (
            json.JSONDecodeError,
            FileNotFoundError,
            IOError,
            TypeError,
            KeyError,
            ValueError,
        ) as _e:
            # print(f"Err loading/parsing JSON: {_e}.") # Shortened further
            # Consider more specific error handling or logging
            # For now, if file is corrupt or unreadable, treat as empty/start fresh
            return []

    def _save_sessions_to_file(self, sessions: List[TaskSession]):
        try:
            data_list = [session_to_dict(s) for s in sessions]
            with open(self.file_path, "w") as f:
                json.dump(data_list, f, indent=4)
        except IOError as e:
            # print(f"Error writing to JSON file: {e}") # For debugging
            raise StorageWriteError(f"Failed to write sessions to {self.file_path}: {e}") from e

    def save_task_session(self, session: TaskSession) -> None:
        sessions = self._load_sessions_from_file()
        # Simple append. If sessions could be updated by ID, logic would be different.
        sessions.append(session)
        self._save_sessions_to_file(sessions)

    def get_all_sessions(self) -> List[TaskSession]:
        return self._load_sessions_from_file()

    def clear(self) -> None:
        # print(f"Placeholder: Clearing JSON storage at {self.file_path}")
        self._save_sessions_to_file([])  # Save an empty list
