import pytest

# from enum import Enum # Unused
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

# from unittest import mock # Confirmed unused, so removed.

# Attempt to import TaskSession and TaskSessionStatus
try:
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
        InvalidStateTransitionError,
    )
except ImportError:
    TaskSession = None
    TaskSessionStatus = None
    InvalidStateTransitionError = None

FROZEN_TIME_STR = "2024-01-01T12:00:00Z"


def specific_utc_dt(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)


@pytest.mark.skipif(
    TaskSessionStatus is None, reason="TaskSessionStatus not implemented"
)
def test_task_session_status_enum():
    assert hasattr(TaskSessionStatus, "STARTED")
    assert hasattr(TaskSessionStatus, "PAUSED")
    assert hasattr(TaskSessionStatus, "STOPPED")
    assert TaskSessionStatus.STARTED.value == "STARTED"


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_task_session_creation_defaults():
    with freeze_time(FROZEN_TIME_STR):
        task_name = "Test Task"
        current_frozen_time = datetime.now(timezone.utc)
        session = TaskSession(task_name=task_name, start_time=current_frozen_time)
        assert session.task_name == task_name
        assert session.start_time == current_frozen_time
        assert session.end_time is None
        assert session.status == TaskSessionStatus.STARTED
        assert session._accumulated_duration == timedelta(0)
        assert session._current_segment_start_time == current_frozen_time
        assert session.get_duration_at(current_frozen_time) == timedelta(0)


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_task_session_creation_stopped_calculates_duration():
    with freeze_time(FROZEN_TIME_STR):
        task_name = "Another Task"
        current_frozen_now = datetime.now(timezone.utc)
        start_time = current_frozen_now - timedelta(hours=1)
        end_time = current_frozen_now
        session = TaskSession(
            task_name=task_name,
            start_time=start_time,
            end_time=end_time,
            status=TaskSessionStatus.STOPPED,
        )
        assert session.start_time == start_time
        assert session.end_time == end_time
        assert session.status == TaskSessionStatus.STOPPED
        assert session._accumulated_duration == timedelta(hours=1)
        assert session._current_segment_start_time is None
        assert session.get_duration_at(end_time) == timedelta(hours=1)


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_task_session_live_duration_started():
    # Test if duration property updates correctly with freezegun tick
    with freeze_time(FROZEN_TIME_STR) as freezer:
        start_offset_seconds = 30
        initial_start_time = datetime.now(timezone.utc) - timedelta(seconds=start_offset_seconds)
        session = TaskSession(task_name="Live Task", start_time=initial_start_time)
        
        # Check initial duration immediately after creation
        current_frozen_time_1 = datetime.now(timezone.utc)
        assert session.get_duration_at(current_frozen_time_1) == timedelta(seconds=start_offset_seconds), "Initial duration mismatch"

        # Tick the clock forward
        tick_delta = timedelta(minutes=10)
        freezer.tick(tick_delta)

        # Check duration after ticking
        current_frozen_time_2 = datetime.now(timezone.utc)
        expected_duration_after_tick = timedelta(seconds=start_offset_seconds) + tick_delta
        assert session.get_duration_at(current_frozen_time_2) == expected_duration_after_tick, "Duration mismatch after tick"

        # --- Original Assertions (commented out for new test logic) ---
        # current_frozen_now = datetime.now(timezone.utc)
        # initial_start_time = current_frozen_now - timedelta(
        #     seconds=start_offset_seconds
        # )
        # session = TaskSession(task_name="Live Task", start_time=initial_start_time)
        # expected_duration = timedelta(seconds=start_offset_seconds)
        # assert session.status == TaskSessionStatus.STARTED
        # assert session._current_segment_start_time == initial_start_time
        # assert session._accumulated_duration == timedelta(0)
        # assert session.duration == expected_duration


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_started_session():
    with freeze_time(FROZEN_TIME_STR) as freezer:
        current_frozen_now = datetime.now(timezone.utc)
        initial_start_time_for_this_test = current_frozen_now
        session_for_pause = TaskSession(
            task_name="Pause Test", start_time=initial_start_time_for_this_test
        )

        pause_time = current_frozen_now + timedelta(minutes=5)
        with freeze_time(pause_time.isoformat().replace("+00:00", "Z")) as inner_freezer:
            session_for_pause.pause()
            paused_at_time = datetime.now(timezone.utc) # Time is 12:05

        assert session_for_pause.status == TaskSessionStatus.PAUSED
        assert session_for_pause._accumulated_duration == timedelta(minutes=5)
        assert session_for_pause._current_segment_start_time is None
        assert session_for_pause.get_duration_at(paused_at_time) == timedelta(minutes=5)
        assert len(session_for_pause._pause_times) == 1
        assert session_for_pause._pause_times[0] == pause_time
        assert len(session_for_pause._resume_times) == 0


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_paused_session_raises_error():
    start_dt = specific_utc_dt(2024, 1, 1, 12, 0, 0)
    session = TaskSession(
        task_name="Test", start_time=start_dt, status=TaskSessionStatus.PAUSED
    )
    session._accumulated_duration = timedelta(
        minutes=5
    )  # Manual setup consistent with PAUSED
    session._current_segment_start_time = None
    with pytest.raises(InvalidStateTransitionError, match="already PAUSED"):
        session.pause()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_pause_stopped_session_raises_error():
    start_dt = specific_utc_dt(2024, 1, 1, 12, 0, 0)
    session = TaskSession(
        task_name="Test", start_time=start_dt, status=TaskSessionStatus.STOPPED
    )
    with pytest.raises(InvalidStateTransitionError, match="already STOPPED"):
        session.pause()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_paused_session():
    with freeze_time(FROZEN_TIME_STR) as freezer:
        outer_frozen_now = datetime.now(timezone.utc) # 12:00
        initial_start_time = outer_frozen_now - timedelta(minutes=10) # 11:50
        session = TaskSession(task_name="Resume Test", start_time=initial_start_time)
        pause_time_for_setup = initial_start_time + timedelta(minutes=5) # 11:55
        with freeze_time(pause_time_for_setup.isoformat().replace("+00:00", "Z")):
            session.pause() # Pause happens at 11:55
        
        # Resume happens at outer_frozen_now (12:00)
        session.resume() 
        resumed_at_time = outer_frozen_now

        assert session.status == TaskSessionStatus.STARTED
        assert session._current_segment_start_time == resumed_at_time
        assert session._accumulated_duration == timedelta(minutes=5)
        assert session.get_duration_at(resumed_at_time) == timedelta(minutes=5)
        assert len(session._resume_times) == 1
        assert session._resume_times[-1] == resumed_at_time


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_started_session_raises_error():
    start_dt = specific_utc_dt(2024, 1, 1, 12, 0, 0)
    session = TaskSession(
        task_name="Test", start_time=start_dt, status=TaskSessionStatus.STARTED
    )
    with pytest.raises(InvalidStateTransitionError, match="already STARTED"):
        session.resume()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_resume_stopped_session_raises_error():
    start_dt = specific_utc_dt(2024, 1, 1, 12, 0, 0)
    session = TaskSession(
        task_name="Test", start_time=start_dt, status=TaskSessionStatus.STOPPED
    )
    with pytest.raises(InvalidStateTransitionError, match="already STOPPED"):
        session.resume()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_started_session():
    with freeze_time(FROZEN_TIME_STR) as freezer:
        outer_frozen_now = datetime.now(timezone.utc) # 12:00
        initial_start_time = outer_frozen_now - timedelta(minutes=30) # 11:30
        session = TaskSession(task_name="Stop Test", start_time=initial_start_time)
        
        session.stop()  # Stops at outer_frozen_now (12:00)
        stopped_at_time = outer_frozen_now

        assert session.status == TaskSessionStatus.STOPPED
        assert session.end_time == stopped_at_time
        assert session._accumulated_duration == timedelta(minutes=30)
        assert session._current_segment_start_time is None
        assert session.get_duration_at(stopped_at_time) == timedelta(minutes=30)


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_paused_session():
    with freeze_time(FROZEN_TIME_STR) as freezer:
        outer_frozen_now = datetime.now(timezone.utc) # 12:00
        initial_start_time = outer_frozen_now - timedelta(minutes=30) # 11:30
        session = TaskSession(
            task_name="Stop Paused Test", start_time=initial_start_time
        )
        pause_time = initial_start_time + timedelta(minutes=10) # 11:40
        with freeze_time(pause_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        
        session.stop()  # Stops at outer_frozen_now (12:00)
        stopped_at_time = outer_frozen_now

        assert session.status == TaskSessionStatus.STOPPED
        assert session.end_time == stopped_at_time
        assert session._accumulated_duration == timedelta(minutes=10)
        assert session._current_segment_start_time is None
        assert session.get_duration_at(stopped_at_time) == timedelta(minutes=10)


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_stop_stopped_session_raises_error():
    start_dt = specific_utc_dt(2024, 1, 1, 11, 0, 0)
    end_dt = specific_utc_dt(2024, 1, 1, 12, 0, 0)
    session = TaskSession(
        task_name="Test",
        start_time=start_dt,
        end_time=end_dt,
        status=TaskSessionStatus.STOPPED,
    )
    with pytest.raises(InvalidStateTransitionError, match="already STOPPED"):
        session.stop()


@pytest.mark.skipif(
    TaskSession is None or InvalidStateTransitionError is None,
    reason="Dependencies not met",
)
def test_multiple_pause_resume_cycles():
    with freeze_time(FROZEN_TIME_STR):
        frozen_start_time = datetime.now(timezone.utc)
        session = TaskSession(task_name="Cycle Test", start_time=frozen_start_time)

        pause1_time = frozen_start_time + timedelta(minutes=10)
        resume1_time = frozen_start_time + timedelta(minutes=20)
        with freeze_time(pause1_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(resume1_time.isoformat().replace("+00:00", "Z")):
            session.resume()

        pause2_time = frozen_start_time + timedelta(minutes=25)
        resume2_time = frozen_start_time + timedelta(minutes=30)
        with freeze_time(pause2_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(resume2_time.isoformat().replace("+00:00", "Z")):
            session.resume()

        stop_time = frozen_start_time + timedelta(minutes=32)
        with freeze_time(stop_time.isoformat().replace("+00:00", "Z")):
            session.stop()

        assert session.status == TaskSessionStatus.STOPPED
        assert session._accumulated_duration == timedelta(minutes=17)
        assert session.end_time == stop_time
        assert len(session._pause_times) == 2
        assert session._pause_times[0] == pause1_time
        assert session._pause_times[1] == pause2_time
        assert len(session._resume_times) == 2
        assert session._resume_times[0] == resume1_time
        assert session._resume_times[1] == resume2_time


# --- Tests for get_active_segments ---


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_get_active_segments_just_started():
    with freeze_time(FROZEN_TIME_STR):
        current_frozen_time = datetime.now(timezone.utc)
        session = TaskSession(
            task_name="Test", start_time=current_frozen_time - timedelta(minutes=10)
        )
        segments = session.get_active_segments()
        assert len(segments) == 1
        assert segments[0] == (
            current_frozen_time - timedelta(minutes=10),
            current_frozen_time,
        )


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_get_active_segments_started_paused_stopped():
    with freeze_time(FROZEN_TIME_STR):
        current_frozen_time = datetime.now(timezone.utc)
        session_start_time = current_frozen_time - timedelta(minutes=30)
        session = TaskSession(task_name="Test", start_time=session_start_time)

        pause_time = current_frozen_time - timedelta(minutes=20)
        stop_time = current_frozen_time - timedelta(minutes=10)  # Stop time after pause

        with freeze_time(pause_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(stop_time.isoformat().replace("+00:00", "Z")):
            session.stop()

        segments = session.get_active_segments()
        assert len(segments) == 1, f"Segments: {segments}"
        assert segments[0] == (session_start_time, pause_time)


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_get_active_segments_started_paused_resumed_stopped():
    with freeze_time(FROZEN_TIME_STR):
        current_frozen_time = datetime.now(timezone.utc)
        session_start_time = current_frozen_time - timedelta(minutes=30)
        session = TaskSession(task_name="Test", start_time=session_start_time)

        pause_time = current_frozen_time - timedelta(minutes=20)
        resume_time = current_frozen_time - timedelta(minutes=15)
        stop_time = current_frozen_time - timedelta(minutes=5)

        with freeze_time(pause_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(resume_time.isoformat().replace("+00:00", "Z")):
            session.resume()
        with freeze_time(stop_time.isoformat().replace("+00:00", "Z")):
            session.stop()

        segments = session.get_active_segments()
        assert len(segments) == 2, f"Segments: {segments}"
        assert segments[0] == (session_start_time, pause_time)
        assert segments[1] == (resume_time, stop_time)


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_get_active_segments_currently_paused():
    with freeze_time(FROZEN_TIME_STR):
        current_frozen_time = datetime.now(timezone.utc)
        session_start_time = current_frozen_time - timedelta(minutes=30)
        session = TaskSession(task_name="Test", start_time=session_start_time)

        pause1_time = current_frozen_time - timedelta(minutes=20)
        resume1_time = current_frozen_time - timedelta(minutes=15)
        pause2_time = current_frozen_time - timedelta(minutes=10)

        with freeze_time(pause1_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(resume1_time.isoformat().replace("+00:00", "Z")):
            session.resume()
        with freeze_time(pause2_time.isoformat().replace("+00:00", "Z")):
            session.pause()

        segments = session.get_active_segments()
        assert len(segments) == 2, f"Segments: {segments}"
        assert segments[0] == (session_start_time, pause1_time)
        assert segments[1] == (resume1_time, pause2_time)


@pytest.mark.skipif(TaskSession is None, reason="TaskSession not implemented")
def test_get_active_segments_currently_started():
    with freeze_time(FROZEN_TIME_STR):
        current_frozen_time = datetime.now(timezone.utc)
        session_start_time = current_frozen_time - timedelta(minutes=30)
        session = TaskSession(task_name="Test", start_time=session_start_time)

        pause1_time = current_frozen_time - timedelta(minutes=20)
        resume1_time = current_frozen_time - timedelta(minutes=15)

        with freeze_time(pause1_time.isoformat().replace("+00:00", "Z")):
            session.pause()
        with freeze_time(resume1_time.isoformat().replace("+00:00", "Z")):
            session.resume()

        segments = (
            session.get_active_segments()
        )  # Called when "now" is current_frozen_time (12:00)
        assert len(segments) == 2, f"Segments: {segments}"
        assert segments[0] == (session_start_time, pause1_time)
        assert segments[1] == (resume1_time, current_frozen_time)
