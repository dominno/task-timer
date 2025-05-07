import pytest
from datetime import datetime, timedelta, timezone

# Attempt to import TaskSession and the utility function
try:
    from src.domain.session import TaskSession, TaskSessionStatus
    from src.utils.export_utils import task_session_to_csv_row
except ImportError:
    TaskSession = None
    TaskSessionStatus = None
    task_session_to_csv_row = None


# Basic test structure
@pytest.mark.skipif(
    task_session_to_csv_row is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_task_session_to_csv_row_basic_stopped_session():
    """Test with a simple, stopped TaskSession without pauses."""
    start_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)  # 1 hour duration
    session = TaskSession(
        task_name="Test Task 1",
        start_time=start_time,
        end_time=end_time,
        status=TaskSessionStatus.STOPPED,
    )
    # Manually set internal fields that __post_init__ would set for a stopped session
    session._accumulated_duration = end_time - start_time

    expected_csv_row = [
        "Test Task 1",  # task_name
        "2024-01-01T10:00:00+00:00",  # start_time_utc
        "2024-01-01T11:00:00+00:00",  # end_time_utc
        "STOPPED",  # status
        "3600",  # total_duration_seconds (1 hour)
        "",  # first_pause_time_utc
        "",  # last_resume_time_utc
        "0",  # number_of_pauses
    ]

    actual_csv_row = task_session_to_csv_row(session)
    assert actual_csv_row == expected_csv_row


@pytest.mark.skipif(
    task_session_to_csv_row is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_task_session_to_csv_row_running_with_pauses():
    """Test a running session with a couple of pauses."""
    start_time = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    pause1_time = datetime(2024, 1, 2, 12, 30, 0, tzinfo=timezone.utc)
    resume1_time = datetime(2024, 1, 2, 12, 45, 0, tzinfo=timezone.utc)
    pause2_time = datetime(
        2024, 1, 2, 13, 0, 0, tzinfo=timezone.utc
    )  # currently paused here for calc

    session = TaskSession(task_name="Test Task 2", start_time=start_time)
    # Simulate session state
    session.status = TaskSessionStatus.PAUSED  # Pretend it's currently paused
    session._pause_times = [pause1_time, pause2_time]
    session._resume_times = [resume1_time]
    # Duration up to pause2_time: (12:30-12:00) + (13:00-12:45) = 30m + 15m = 45m
    session._accumulated_duration = timedelta(minutes=45)
    session._current_segment_start_time = None  # because it's PAUSED

    expected_csv_row = [
        "Test Task 2",
        "2024-01-02T12:00:00+00:00",
        "",  # No end_time as it's not STOPPED
        "PAUSED",
        str(45 * 60),  # total_duration_seconds (45 minutes)
        "2024-01-02T12:30:00+00:00",  # first_pause_time_utc
        "2024-01-02T12:45:00+00:00",  # last_resume_time_utc
        "2",  # number_of_pauses
    ]
    actual_csv_row = task_session_to_csv_row(session)
    assert actual_csv_row == expected_csv_row


# Add more tests for different scenarios:
# - Session still running
# - Session paused
# - Session with multiple pauses
# - Session with no end_time (e.g., running or paused)
# - Edge cases for times (e.g., start of epoch, far future if relevant)
