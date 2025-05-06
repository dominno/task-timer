import pytest
from enum import Enum
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

# Attempt to import TaskSession and TaskSessionStatus
try:
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
        InvalidStateTransitionError,
    )
except ImportError:
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    InvalidStateTransitionError = None  # type: ignore

# Helper for creating consistent datetime objects for tests
FROZEN_TIME_STR = "2024-01-01T12:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.mark.skipif(
    TaskSessionStatus is None,
    reason="TaskSessionStatus not yet implemented or import failed",
)
def test_task_session_status_enum():
    """Tests the TaskSessionStatus Enum members."""
    assert hasattr(TaskSessionStatus, "STARTED"), "STARTED status missing"
    assert hasattr(TaskSessionStatus, "PAUSED"), "PAUSED status missing"
    assert hasattr(TaskSessionStatus, "STOPPED"), "STOPPED status missing"

    assert isinstance(TaskSessionStatus.STARTED, Enum)
    assert TaskSessionStatus.STARTED.value == "STARTED"
    assert TaskSessionStatus.PAUSED.value == "PAUSED"
    assert TaskSessionStatus.STOPPED.value == "STOPPED"


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or TaskSessionStatus is None,
    reason="TaskSession or Status not implemented/imported",
)
def test_task_session_creation_defaults():
    """Tests TaskSession creation with default values and initial state."""
    task_name = "Test Task"
    # start_time will be FROZEN_DATETIME due to freeze_time if not specified,
    # but TaskSession takes it as an argument, so we pass it explicitly.
    session = TaskSession(task_name=task_name, start_time=FROZEN_DATETIME)

    assert session.task_name == task_name
    assert session.start_time == FROZEN_DATETIME
    assert session.end_time is None
    assert session.status == TaskSessionStatus.STARTED
    assert session._accumulated_duration == timedelta(0)
    assert session._current_segment_start_time == FROZEN_DATETIME
    # Duration for a freshly started session at the frozen moment of start should be 0
    assert session.duration == timedelta(0)


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or TaskSessionStatus is None,
    reason="TaskSession or Status not implemented/imported",
)
def test_task_session_creation_stopped_calculates_duration():
    """Tests TaskSession creation with STOPPED status calculates duration correctly."""
    task_name = "Another Task"
    start_time = FROZEN_DATETIME - timedelta(hours=1)
    end_time = FROZEN_DATETIME  # This is effectively datetime.now() due to freeze_time

    session = TaskSession(
        task_name=task_name,
        start_time=start_time,
        end_time=end_time,  # Explicitly provide end_time
        status=TaskSessionStatus.STOPPED,
    )

    assert session.task_name == task_name
    assert session.start_time == start_time
    assert session.end_time == end_time
    assert session.status == TaskSessionStatus.STOPPED
    assert session._accumulated_duration == timedelta(hours=1)
    assert session._current_segment_start_time is None
    assert session.duration == timedelta(hours=1)


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or TaskSessionStatus is None,
    reason="TaskSession or Status not implemented/imported",
)
def test_task_session_live_duration_started():
    """Tests that duration property shows live duration for a STARTED session."""
    start_offset_seconds = 30
    initial_start_time = FROZEN_DATETIME - timedelta(seconds=start_offset_seconds)
    session = TaskSession(task_name="Live Task", start_time=initial_start_time)

    # At this point, FROZEN_DATETIME is datetime.now() due to freeze_time.
    # So, the duration should be start_offset_seconds.
    expected_duration = timedelta(seconds=start_offset_seconds)
    assert session.status == TaskSessionStatus.STARTED
    assert session._current_segment_start_time == initial_start_time
    assert session._accumulated_duration == timedelta(0)
    assert session.duration == expected_duration


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_started_session():
    """Test pausing a STARTED session."""
    initial_start_time = FROZEN_DATETIME - timedelta(minutes=10)
    session = TaskSession(task_name="Pause Test", start_time=initial_start_time)
    assert session.status == TaskSessionStatus.STARTED
    assert session._current_segment_start_time == initial_start_time
    assert session._accumulated_duration == timedelta(0)

    # Freeze time a bit later to simulate time passing before pause
    # Original time_at_pause_str was for illustration, not used in logic.
    # Example: FROZEN_DATETIME is 12:00:00. initial_start_time is 11:50:00
    # A pause at 12:05:00 means segment was 15 mins.
    # Test below uses explicit start and pause relative to FROZEN_DATETIME.
    initial_start_time_for_this_test = FROZEN_DATETIME # 12:00:00Z
    session_for_pause = TaskSession(
        task_name="Pause Test", start_time=initial_start_time_for_this_test
    )

    pause_time = FROZEN_DATETIME + timedelta(minutes=5)  # 12:05:00Z
    with freeze_time(pause_time.isoformat().replace("+00:00", "Z")):
        session_for_pause.pause()

    assert session_for_pause.status == TaskSessionStatus.PAUSED
    assert session_for_pause._accumulated_duration == timedelta(minutes=5)
    assert session_for_pause._current_segment_start_time is None
    # Duration property for a PAUSED session should return accumulated
    assert session_for_pause.duration == timedelta(minutes=5)


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_paused_session_raises_error():
    """Test pausing an already PAUSED session raises InvalidStateTransitionError."""
    session = TaskSession(
        task_name="Test", start_time=FROZEN_DATETIME, status=TaskSessionStatus.PAUSED
    )
    # Manually set internal state consistent with PAUSED after a segment for this test setup
    session._accumulated_duration = timedelta(minutes=5)
    session._current_segment_start_time = None
    with pytest.raises(
        InvalidStateTransitionError,
        match="Cannot pause a session that is already PAUSED.",
    ):
        session.pause()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_stopped_session_raises_error():
    """Test pausing a STOPPED session raises InvalidStateTransitionError."""
    session = TaskSession(
        task_name="Test", start_time=FROZEN_DATETIME, status=TaskSessionStatus.STOPPED
    )
    with pytest.raises(
        InvalidStateTransitionError,
        match="Cannot pause a session that is already STOPPED.",
    ):
        session.pause()


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_paused_session():
    """Test resuming a PAUSED session."""
    # Setup a session that was started, ran for 5 mins, then paused.
    initial_start_time = FROZEN_DATETIME - timedelta(minutes=10) # 11:50
    session = TaskSession(task_name="Resume Test", start_time=initial_start_time)
    
    pause_time_for_setup = initial_start_time + timedelta(minutes=5) # 11:55
    with freeze_time(pause_time_for_setup.isoformat().replace("+00:00", "Z")):
        session.pause()
        # At this point, status is PAUSED, _accumulated_duration is 5 mins.
        # _current_segment_start_time is None.

    assert session.status == TaskSessionStatus.PAUSED
    assert session._accumulated_duration == timedelta(minutes=5)

    # Now resume it at a later time (FROZEN_DATETIME is 12:00)
    # The effective time for resume() will be FROZEN_DATETIME (12:00)
    session.resume()

    assert session.status == TaskSessionStatus.STARTED
    assert (
        session._current_segment_start_time == FROZEN_DATETIME
    )  # Resumed at current frozen time
    assert session._accumulated_duration == timedelta(minutes=5)  # Unchanged by resume
    # Live duration should now start counting from resume time on top of accumulated
    assert session.duration == timedelta(
        minutes=5
    )  # (FROZEN_DATETIME - FROZEN_DATETIME) + 5min_accumulated


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_started_session_raises_error():
    """Test resuming an already STARTED session raises InvalidStateTransitionError."""
    session = TaskSession(
        task_name="Test", start_time=FROZEN_DATETIME, status=TaskSessionStatus.STARTED
    )
    with pytest.raises(
        InvalidStateTransitionError,
        match="Cannot resume a session that is already STARTED.",
    ):
        session.resume()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_stopped_session_raises_error():
    """Test resuming a STOPPED session raises InvalidStateTransitionError."""
    session = TaskSession(
        task_name="Test", start_time=FROZEN_DATETIME, status=TaskSessionStatus.STOPPED
    )
    with pytest.raises(
        InvalidStateTransitionError,
        match="Cannot resume a session that is already STOPPED.",
    ):
        session.resume()


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_started_session():
    """Test stopping a STARTED session."""
    initial_start_time = FROZEN_DATETIME - timedelta(minutes=30)  # 11:30
    session = TaskSession(task_name="Stop Test", start_time=initial_start_time)
    assert session.status == TaskSessionStatus.STARTED

    # Stop the session at FROZEN_DATETIME (12:00)
    session.stop()

    assert session.status == TaskSessionStatus.STOPPED
    assert session.end_time == FROZEN_DATETIME
    assert session._accumulated_duration == timedelta(minutes=30)
    assert session._current_segment_start_time is None
    assert session.duration == timedelta(minutes=30)


@freeze_time(FROZEN_TIME_STR)
@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_paused_session():
    """Test stopping a PAUSED session."""
    initial_start_time = FROZEN_DATETIME - timedelta(minutes=30)  # 11:30
    session = TaskSession(task_name="Stop Paused Test", start_time=initial_start_time)

    pause_time = initial_start_time + timedelta(minutes=10)  # 11:40
    with freeze_time(pause_time.isoformat().replace("+00:00", "Z")):
        session.pause()  # Accumulated 10 mins

    assert session.status == TaskSessionStatus.PAUSED
    assert session._accumulated_duration == timedelta(minutes=10)

    # Stop the session at FROZEN_DATETIME (12:00) - 20 mins after pause
    session.stop()

    assert session.status == TaskSessionStatus.STOPPED
    assert session.end_time == FROZEN_DATETIME
    # Accumulated duration should remain what it was at pause time
    assert session._accumulated_duration == timedelta(minutes=10)
    assert session._current_segment_start_time is None
    assert session.duration == timedelta(minutes=10)


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_stopped_session_raises_error():
    """Test stopping an already STOPPED session raises InvalidStateTransitionError."""
    session = TaskSession(
        task_name="Test",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        end_time=FROZEN_DATETIME,
        status=TaskSessionStatus.STOPPED,
    )
    with pytest.raises(
        InvalidStateTransitionError,
        match="Cannot stop a session that is already STOPPED.",
    ):
        session.stop()


# --- Tests for invalid state transitions --- (To be added)
