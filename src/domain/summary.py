from datetime import datetime, timedelta, timezone
from typing import Callable, Tuple
from collections import defaultdict

# Import the actual TaskSession
from .session import TaskSession

# Constants for convenience
TIME_START_OF_DAY = datetime.min.time()  # 00:00:00
TIME_END_OF_DAY = datetime.max.time()  # 23:59:59.999999


def get_today_range() -> Tuple[datetime, datetime]:
    """Returns a tuple of (start_of_today, end_of_today) in UTC."""
    today_utc = datetime.now(timezone.utc).date()
    start_of_today = datetime.combine(today_utc, TIME_START_OF_DAY, tzinfo=timezone.utc)
    end_of_today = datetime.combine(today_utc, TIME_END_OF_DAY, tzinfo=timezone.utc)
    return start_of_today, end_of_today


def get_this_week_range() -> Tuple[datetime, datetime]:
    """Returns a tuple of (start_of_week, end_of_week) in UTC.
    Week starts on Monday and ends on Sunday.
    """
    today_utc_date = datetime.now(timezone.utc).date()
    start_of_week_date = today_utc_date - timedelta(
        days=today_utc_date.weekday()
    )  # Monday
    end_of_week_date = start_of_week_date + timedelta(days=6)  # Sunday

    start_of_week = datetime.combine(
        start_of_week_date, TIME_START_OF_DAY, tzinfo=timezone.utc
    )
    end_of_week = datetime.combine(
        end_of_week_date, TIME_END_OF_DAY, tzinfo=timezone.utc
    )
    return start_of_week, end_of_week


def get_this_month_range() -> Tuple[datetime, datetime]:
    """Returns a tuple of (start_of_month, end_of_month) in UTC."""
    today_utc_date = datetime.now(timezone.utc).date()
    start_of_month_date = today_utc_date.replace(day=1)

    # Calculate end of month
    next_month = start_of_month_date.replace(day=28) + timedelta(
        days=4
    )  # Go to next month safely
    end_of_month_date = next_month - timedelta(days=next_month.day)

    start_of_month = datetime.combine(
        start_of_month_date, TIME_START_OF_DAY, tzinfo=timezone.utc
    )
    end_of_month = datetime.combine(
        end_of_month_date, TIME_END_OF_DAY, tzinfo=timezone.utc
    )
    return start_of_month, end_of_month


def get_this_year_range() -> Tuple[datetime, datetime]:
    """Returns a tuple of (start_of_year, end_of_year) in UTC."""
    today_utc_date = datetime.now(timezone.utc).date()
    start_of_year_date = today_utc_date.replace(month=1, day=1)
    end_of_year_date = today_utc_date.replace(month=12, day=31)

    start_of_year = datetime.combine(
        start_of_year_date, TIME_START_OF_DAY, tzinfo=timezone.utc
    )
    end_of_year = datetime.combine(
        end_of_year_date, TIME_END_OF_DAY, tzinfo=timezone.utc
    )
    return start_of_year, end_of_year


# TODO: Implement these functions next:
def get_duration_within_period(
    session: TaskSession, period_start: datetime, period_end: datetime
) -> timedelta:
    """Calculates the total duration of a session's active segments within a given period."""
    total_duration_in_period = timedelta(0)
    active_segments = session.get_active_segments()

    for seg_start, seg_end in active_segments:
        # Ensure all datetimes are UTC for comparison, assuming period_start/end are UTC
        # Segments from get_active_segments should already be UTC

        overlap_start = max(seg_start, period_start)
        overlap_end = min(seg_end, period_end)

        if overlap_start < overlap_end:  # If there is an actual overlap
            total_duration_in_period += overlap_end - overlap_start

    return total_duration_in_period


def DATETIME_RANGE_HELPERS() -> dict[str, Callable[[], tuple[datetime, datetime]]]:
    return {
        "today": get_today_range,
        "this_week": get_this_week_range,
        "this_month": get_this_month_range,
        "this_year": get_this_year_range,
    }


def generate_summary_report(
    sessions: list[TaskSession], period_name: str
) -> dict[str, timedelta]:
    """
    Generates a summary report of total time spent per task_id within a given named period.

    Args:
        sessions: A list of TaskSession objects.
        period_name: The name of the period (e.g., "today", "this_week").

    Returns:
        A dictionary mapping task_id (str) to total duration (timedelta) spent on that task
        within the specified period.
        Returns an empty dictionary if the period_name is invalid.
    """
    range_helpers = DATETIME_RANGE_HELPERS()
    if period_name not in range_helpers:
        # Or raise an error, or log a warning, depending on desired behavior
        return {}

    period_start, period_end = range_helpers[period_name]()

    summary_data: dict[str, timedelta] = defaultdict(timedelta)

    for session in sessions:
        if not session.task_name:  # Changed from task_id to task_name
            continue
        duration_in_period = get_duration_within_period(
            session, period_start, period_end
        )
        if duration_in_period > timedelta(0):
            summary_data[
                session.task_name
            ] += duration_in_period  # Changed from task_id to task_name

    return dict(summary_data)  # Convert back to dict if using defaultdict internally


# def generate_summary_report(all_sessions: List[TaskSession], report_period_start: datetime, report_period_end: datetime) -> Dict[str, timedelta]:
#     pass
