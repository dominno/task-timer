import pytest
from enum import Enum
from datetime import datetime, timedelta

# Attempt to import TaskSession and TaskSessionStatus
try:
    from src.domain.session import TaskSession, TaskSessionStatus
except ImportError:
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore


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


@pytest.mark.skipif(
    TaskSession is None or TaskSessionStatus is None,
    reason="TaskSession or Status not implemented/imported",
)
def test_task_session_creation_defaults():
    """Tests TaskSession creation with default values."""
    task_name = "Test Task"
    start_time = datetime.now()

    session = TaskSession(task_name=task_name, start_time=start_time)

    assert session.task_name == task_name
    assert session.start_time == start_time
    assert session.end_time is None
    assert session.status == TaskSessionStatus.STARTED
    assert isinstance(session.duration, timedelta)
    assert session.duration == timedelta(0)  # Initial duration


@pytest.mark.skipif(
    TaskSession is None or TaskSessionStatus is None,
    reason="TaskSession or Status not implemented/imported",
)
def test_task_session_creation_with_specifics():
    """Tests TaskSession creation with specific end_time and status."""
    task_name = "Another Task"
    start_time = datetime.now() - timedelta(hours=1)
    end_time = datetime.now()
    status = TaskSessionStatus.STOPPED

    session = TaskSession(
        task_name=task_name, start_time=start_time, end_time=end_time, status=status
    )

    assert session.task_name == task_name
    assert session.start_time == start_time
    assert session.end_time == end_time
    assert session.status == status
    assert session.duration == end_time - start_time
