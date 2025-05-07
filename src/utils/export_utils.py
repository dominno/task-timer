# Utilities for data export functionality

from typing import List
from src.domain.session import TaskSession, TaskSessionStatus
from datetime import datetime, timezone


def task_session_to_csv_row(session: TaskSession) -> List[str]:
    """Converts a TaskSession object to a list of strings for CSV output."""

    start_time_utc_str = session.start_time.isoformat() if session.start_time else ""
    end_time_utc_str = session.end_time.isoformat() if session.end_time else ""

    # Use get_duration_at with current time for total duration including live segment if running
    # The .duration property now only returns _accumulated_duration
    now = datetime.now(timezone.utc)
    total_session_duration = session.get_duration_at(now)
    total_duration_seconds = str(int(total_session_duration.total_seconds()))

    status_str = session.status.value

    first_pause_str = ""
    if session._pause_times:
        first_pause_str = session._pause_times[0].isoformat()

    last_resume_str = ""
    if session._resume_times:
        last_resume_str = session._resume_times[-1].isoformat()

    num_pauses = str(len(session._pause_times))

    return [
        session.task_name or "",
        start_time_utc_str,
        end_time_utc_str,
        status_str,
        total_duration_seconds,
        first_pause_str,
        last_resume_str,
        num_pauses,
    ]


# Placeholder for other potential export utils
