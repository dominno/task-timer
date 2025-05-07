from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Import the actual TaskSession
from .session import TaskSession

# Constants for convenience
TIME_START_OF_DAY = datetime.min.time()  # 00:00:00
TIME_END_OF_DAY = datetime.max.time()  # 23:59:59.999999


def get_date_range_for_period(period_name: str) -> tuple[datetime, datetime]:
    """
    Returns the start and end datetimes for a given named period.
    All datetimes are timezone-aware (UTC).
    """
    now_utc = datetime.now(timezone.utc)

    if period_name == "today":
        start_of_day = datetime(
            now_utc.year, now_utc.month, now_utc.day, 0, 0, 0, 0, tzinfo=timezone.utc
        )
        end_of_day = datetime(
            now_utc.year,
            now_utc.month,
            now_utc.day,
            23,
            59,
            59,
            999999,
            tzinfo=timezone.utc,
        )
        return start_of_day, end_of_day
    elif period_name == "week":
        start_of_week_date = now_utc - timedelta(days=now_utc.weekday())  # Monday
        start_of_week = datetime(
            start_of_week_date.year,
            start_of_week_date.month,
            start_of_week_date.day,
            0,
            0,
            0,
            0,
            tzinfo=timezone.utc,
        )
        end_of_week_date = start_of_week_date + timedelta(days=6)  # Sunday
        end_of_week = datetime(
            end_of_week_date.year,
            end_of_week_date.month,
            end_of_week_date.day,
            23,
            59,
            59,
            999999,
            tzinfo=timezone.utc,
        )
        return start_of_week, end_of_week
    elif period_name == "month":
        start_of_month = datetime(
            now_utc.year, now_utc.month, 1, 0, 0, 0, 0, tzinfo=timezone.utc
        )
        # Calculate end of month robustly
        if now_utc.month == 12:
            end_of_month_day = datetime(now_utc.year, 12, 31)
        else:
            end_of_month_day = datetime(now_utc.year, now_utc.month + 1, 1) - timedelta(
                days=1
            )
        end_of_month = datetime(
            end_of_month_day.year,
            end_of_month_day.month,
            end_of_month_day.day,
            23,
            59,
            59,
            999999,
            tzinfo=timezone.utc,
        )
        return start_of_month, end_of_month
    elif period_name == "year":
        start_of_year = datetime(now_utc.year, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
        end_of_year = datetime(
            now_utc.year, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc
        )
        return start_of_year, end_of_year
    else:
        raise ValueError(f"Invalid period specified: {period_name}")


def get_duration_within_period(
    session: TaskSession, period_start: datetime, period_end: datetime
) -> timedelta:
    """Calculates the total duration of a session's active segments within a given period."""
    total_duration_in_period = timedelta(0)
    active_segments = session.get_active_segments()

    for seg_start, seg_end in active_segments:
        overlap_start = max(seg_start, period_start)
        overlap_end = min(seg_end, period_end)

        if overlap_start < overlap_end:
            total_duration_in_period += overlap_end - overlap_start

    return total_duration_in_period


def generate_summary_report(
    sessions: list[TaskSession], period_name: str
) -> dict[str, timedelta]:
    """
    Generates a summary report of total time spent per task_name within a given named period.

    Args:
        sessions: A list of TaskSession objects.
        period_name: The name of the period (e.g., "today", "week", "month", "year").

    Returns:
        A dictionary mapping task_name (str) to total duration (timedelta) spent on that task
        within the specified period.
        Raises ValueError if the period_name is invalid.
    """
    try:
        period_start, period_end = get_date_range_for_period(period_name)
    except ValueError:
        # Re-raise or handle as per desired application flow. For now, re-raise.
        # Or, to match previous behavior of returning empty dict for invalid period:
        # print(f"Warning: Invalid period_name '{period_name}' for summary report.")
        # return {}
        raise  # Re-raise the ValueError from get_date_range_for_period

    summary_data: dict[str, timedelta] = defaultdict(timedelta)

    for session in sessions:
        if not session.task_name:
            continue
        duration_in_period = get_duration_within_period(
            session, period_start, period_end
        )
        if duration_in_period > timedelta(0):
            summary_data[session.task_name] += duration_in_period

    return dict(summary_data)


#     pass
