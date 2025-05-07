from typing import List, Optional, Any, Dict
from .base import StorageProvider, StorageWriteError
from src.domain.session import TaskSession, TaskSessionStatus  # Import Enum as well
import os  # For default file path construction
import json  # Will be needed soon
from datetime import datetime, timedelta, timezone
from dataclasses import asdict
import csv  # Added for export_to_csv method
from src.utils.export_utils import task_session_to_csv_row

# from ...domain.session import TaskSession # Adjust path as needed

DEFAULT_STORAGE_DIR = os.path.expanduser("~/.task_timer")
DEFAULT_RECORDS_FILE = "records.json"


def session_to_dict(session: TaskSession) -> Dict[str, Any]:
    """Converts a TaskSession object to a JSON-serializable dictionary."""
    data = asdict(
        session
    )  # Converts to dict, but timedeltas are still timedelta objects

    # Convert datetimes to ISO strings
    data["start_time"] = session.start_time.isoformat() if session.start_time else None
    if session.end_time:
        data["end_time"] = session.end_time.isoformat()
    else:
        data["end_time"] = None

    # Convert enum to its value
    data["status"] = session.status.value

    # Handle timedelta: _accumulated_duration
    # Store as seconds, remove original timedelta object from dict produced by asdict
    data["_accumulated_duration_seconds"] = (
        session._accumulated_duration.total_seconds()
    )
    if "_accumulated_duration" in data:  # The key from asdict(session)
        del data["_accumulated_duration"]  # Remove the timedelta object itself

    # _current_segment_start_time is already handled by converting to isoformat or None
    data["_current_segment_start_time"] = (
        session._current_segment_start_time.isoformat()
        if session._current_segment_start_time
        else None
    )

    # _pause_times and _resume_times are lists of datetimes, convert each to isoformat
    data["_pause_times"] = [pt.isoformat() for pt in session._pause_times]
    data["_resume_times"] = [rt.isoformat() for rt in session._resume_times]

    return data


def dict_to_session(data: Dict[str, Any]) -> TaskSession:
    """Converts a dictionary (from JSON) back to a TaskSession object."""
    start_time_str = data.get("start_time")
    data["start_time"] = (
        datetime.fromisoformat(start_time_str) if start_time_str else None
    )  # noqa: E501
    end_time_str = data.get("end_time")
    data["end_time"] = datetime.fromisoformat(end_time_str) if end_time_str else None
    status_str = data.get(
        "status", TaskSessionStatus.STOPPED.value
    )  # Default if missing
    status = TaskSessionStatus(status_str)

    # Create session with core fields first
    session = TaskSession(
        task_name=data.get("task_name", "Unknown Task"),
        start_time=data["start_time"],
        end_time=data["end_time"],
        status=status,
    )

    # Restore internal state for duration calculation accuracy
    if (
        "_accumulated_duration_seconds" in data
        and data["_accumulated_duration_seconds"] is not None
    ):
        session._accumulated_duration = timedelta(
            seconds=data["_accumulated_duration_seconds"]
        )
    else:
        # Backwards compatibility or if somehow missing, try to recalculate if stopped
        if (
            status == TaskSessionStatus.STOPPED
            and session.start_time
            and session.end_time
        ):
            session._accumulated_duration = session.end_time - session.start_time
        else:
            session._accumulated_duration = timedelta(0)

    if "_current_segment_start_time" in data and data["_current_segment_start_time"]:
        try:
            # Ensure it's parsed as timezone-aware UTC
            css_time_str = data["_current_segment_start_time"]
            # Assuming isoformat includes timezone, if not, need to handle
            # naive parsing + UTC assumption
            parsed_css_time = datetime.fromisoformat(css_time_str)
            if parsed_css_time.tzinfo is None:
                session._current_segment_start_time = parsed_css_time.replace(
                    tzinfo=timezone.utc
                )
            else:
                session._current_segment_start_time = parsed_css_time.astimezone(
                    timezone.utc
                )
        except (TypeError, ValueError):
            session._current_segment_start_time = None  # or log error
    elif (
        status == TaskSessionStatus.STARTED
        and not session._current_segment_start_time
        and session.start_time
    ):
        # If it's started and current_segment_start_time wasn't in JSON (e.g. older
        # data) but it wasn't explicitly paused (which would clear it), set it to
        # start_time initially. This branch might be tricky if it was paused and
        # then the field was lost.
        # A robust way: if status is STARTED, and no _resume_times, it must be
        # start_time. If status is STARTED, and there are _resume_times, it should
        # be the last _resume_time if not None.
        # The __post_init__ logic already handles setting _current_segment_start_time
        # for new STARTED sessions. For loaded sessions, if status is STARTED and
        # _current_segment_start_time is None, it implies it was just resumed or
        # started.
        pass
        # Let __post_init__ and subsequent resume/pause calls manage this if it's
        # None and STARTED. Actually, __post_init__ logic for STARTED is if
        # self.status == TaskSessionStatus.STARTED:
        # self._current_segment_start_time = self.start_time
        # This could be wrong if it was paused and resumed.
        # Let's be explicit: if status is STARTED and _current_segment_start_time
        # is None in JSON, it means active from last resume or start.

    # Restore pause and resume times
    if "_pause_times" in data and data["_pause_times"]:
        processed_pause_times = []
        for pt_str in data["_pause_times"]:
            dt_obj = datetime.fromisoformat(pt_str)
            if dt_obj.tzinfo:
                processed_pause_times.append(dt_obj.astimezone(timezone.utc))
            else:
                processed_pause_times.append(dt_obj.replace(tzinfo=timezone.utc))
        session._pause_times = sorted(processed_pause_times)

    if "_resume_times" in data and data["_resume_times"]:
        processed_resume_times = []
        for rt_str in data["_resume_times"]:
            dt_obj = datetime.fromisoformat(rt_str)
            if dt_obj.tzinfo:
                processed_resume_times.append(dt_obj.astimezone(timezone.utc))
            else:
                processed_resume_times.append(dt_obj.replace(tzinfo=timezone.utc))
        session._resume_times = sorted(processed_resume_times)

    if (
        session.status == TaskSessionStatus.STARTED
        and not session._current_segment_start_time
    ):
        if session._resume_times:
            session._current_segment_start_time = session._resume_times[-1]
        else:
            session._current_segment_start_time = session.start_time
    elif session.status != TaskSessionStatus.STARTED:
        session._current_segment_start_time = None  # Should be None if not STARTED

    return session


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
        ):
            # print(f"Err loading/parsing JSON: {_}.") # Shortened further
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
            raise StorageWriteError(
                f"Failed to write sessions to {self.file_path}: {e}"
            ) from e

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

    def export_to_csv(self, target_path: str) -> None:
        """Exports all task sessions to a CSV file at the given path."""
        sessions = self._load_sessions_from_file()
        if not sessions:
            # print(f"No sessions to export to CSV at {target_path}")
            # Create an empty CSV with headers if no sessions? Or just do nothing?
            # For now, let's write a CSV with only headers if no sessions.
            pass  # Let it fall through to write headers

        header = [
            "task_name",
            "start_time_utc",
            "end_time_utc",
            "status",
            "total_duration_seconds",
            "first_pause_time_utc",
            "last_resume_time_utc",
            "number_of_pauses",
        ]

        try:
            with open(target_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                for session in sessions:
                    writer.writerow(task_session_to_csv_row(session))
        except IOError as e:
            # print(f"Error writing to CSV file {target_path}: {e}") # For debugging
            raise StorageWriteError(
                f"Failed to write sessions to CSV file {target_path}: {e}"
            ) from e

    def export_to_json(self, target_path: str) -> None:
        """Exports all task sessions to a JSON file at the given path."""
        sessions = self._load_sessions_from_file()
        # We can reuse _save_sessions_to_file by temporarily changing self.file_path,
        # or by creating a helper that _save_sessions_to_file also uses.
        # For simplicity, let's adapt the core logic of _save_sessions_to_file here.
        try:
            data_list = [session_to_dict(s) for s in sessions]
            with open(target_path, "w") as f:
                json.dump(data_list, f, indent=4)
        except IOError as e:
            raise StorageWriteError(
                f"Failed to write sessions to JSON file {target_path}: {e}"
            ) from e
