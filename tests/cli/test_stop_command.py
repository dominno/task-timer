import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time

# Attempt to import commands and domain models
try:
    from src.cli.stop_command import StopCommand
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
        InvalidStateTransitionError,
    )
    from src.infra.storage.json_storage import JsonStorage
except ImportError:
    StopCommand = None  # type: ignore
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    InvalidStateTransitionError = None  # type: ignore
    JsonStorage = None  # type: ignore

FROZEN_TIME_STR = "2024-01-13T16:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.fixture
def mock_storage_provider_stop():  # Renamed for clarity
    if JsonStorage is None:
        pytest.skip("JsonStorage not available")
    mock_storage = mock.MagicMock(spec=JsonStorage)
    mock_storage.get_all_sessions.return_value = []
    mock_storage.save_task_session.return_value = None
    return mock_storage


def format_timedelta(td: timedelta) -> str:
    """Helper to format timedelta to HH:MM:SS string."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


@pytest.mark.skipif(
    StopCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.stop_command.JsonStorage")
def test_stop_command_started_task(
    mock_json_storage_class, mock_print, mock_storage_provider_stop
):
    """Test StopCommand stops a STARTED task successfully."""
    start_time = FROZEN_DATETIME - timedelta(hours=1, minutes=5, seconds=10)
    started_session = TaskSession(
        task_name="Running Task",
        start_time=start_time,
        status=TaskSessionStatus.STARTED,
    )
    # Mock the stop method to verify call and control its side effects for testing
    started_session.stop = mock.MagicMock()
    # Simulate what stop() would do to the session for duration checking if it were real
    # When stop() is called, it will set end_time and status. Duration is calculated then.
    # For this test, we need to ensure the duration is as expected after stop() is called.
    # The actual stop() method will update _accumulated_duration. We'll mock that.

    def mock_stop_impl():  # Simulate what the real stop() does for return values
        started_session.status = TaskSessionStatus.STOPPED
        started_session.end_time = FROZEN_DATETIME
        started_session._accumulated_duration = (
            FROZEN_DATETIME - start_time
        )  # This is key

    started_session.stop.side_effect = mock_stop_impl
    # The `duration` property will be called by the command AFTER stop() has modified the session.
    type(started_session).duration = mock.PropertyMock(
        return_value=FROZEN_DATETIME - start_time
    )

    mock_storage_provider_stop.get_all_sessions.return_value = [started_session]
    mock_json_storage_class.return_value = mock_storage_provider_stop

    command = StopCommand()
    command.execute([])

    started_session.stop.assert_called_once()
    mock_storage_provider_stop.save_task_session.assert_called_once_with(started_session)
    expected_duration_str = format_timedelta(FROZEN_DATETIME - start_time)
    mock_print.assert_any_call(f"Task 'Running Task' stopped.")
    mock_print.assert_any_call(f"  Total duration: {expected_duration_str}.")


@pytest.mark.skipif(
    StopCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.stop_command.JsonStorage")
def test_stop_command_paused_task(
    mock_json_storage_class, mock_print, mock_storage_provider_stop
):
    """Test StopCommand stops a PAUSED task successfully."""
    start_time = FROZEN_DATETIME - timedelta(hours=2)
    paused_session = TaskSession(
        task_name="Paused Task", start_time=start_time, status=TaskSessionStatus.PAUSED
    )
    paused_session._accumulated_duration = timedelta(
        minutes=45
    )  # Paused after 45 mins of work

    paused_session.stop = mock.MagicMock()

    def mock_stop_impl_paused():
        paused_session.status = TaskSessionStatus.STOPPED
        paused_session.end_time = FROZEN_DATETIME
        # _accumulated_duration for a paused task doesn't change further on stop

    paused_session.stop.side_effect = mock_stop_impl_paused
    type(paused_session).duration = mock.PropertyMock(
        return_value=timedelta(minutes=45)
    )

    mock_storage_provider_stop.get_all_sessions.return_value = [paused_session]
    mock_json_storage_class.return_value = mock_storage_provider_stop

    command = StopCommand()
    command.execute([])

    paused_session.stop.assert_called_once()
    mock_storage_provider_stop.save_task_session.assert_called_once_with(paused_session)
    expected_duration_str = format_timedelta(timedelta(minutes=45))
    mock_print.assert_any_call(f"Task 'Paused Task' stopped.")
    mock_print.assert_any_call(f"  Total duration: {expected_duration_str}.")


@pytest.mark.skipif(
    StopCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.stop_command.JsonStorage")
def test_stop_command_no_active_task(
    mock_json_storage_class, mock_print, mock_storage_provider_stop
):
    """Test StopCommand prints error if no task is active (STARTED or PAUSED)."""
    stopped_session = TaskSession(
        task_name="Old Task",
        start_time=FROZEN_DATETIME - timedelta(days=1),
        status=TaskSessionStatus.STOPPED,
    )
    mock_storage_provider_stop.get_all_sessions.return_value = [stopped_session]
    mock_json_storage_class.return_value = mock_storage_provider_stop

    command = StopCommand()
    command.execute([])
    mock_storage_provider_stop.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error: No active task to stop.")


@pytest.mark.skipif(
    StopCommand is None
    or TaskSession is None
    or InvalidStateTransitionError is None
    or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.stop_command.JsonStorage")
def test_stop_command_domain_error(
    mock_json_storage_class, mock_print, mock_storage_provider_stop
):
    """Test StopCommand handles InvalidStateTransitionError from domain if trying to stop an already STOPPED task."""
    active_session_causing_error = TaskSession(
        task_name="Error Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=5),
        status=TaskSessionStatus.STARTED,
    )  # Could be PAUSED too
    active_session_causing_error.stop = mock.MagicMock(
        side_effect=InvalidStateTransitionError("Internal domain error on stop.")
    )
    mock_storage_provider_stop.get_all_sessions.return_value = [
        active_session_causing_error
    ]
    mock_json_storage_class.return_value = mock_storage_provider_stop

    command = StopCommand()
    command.execute([])
    mock_storage_provider_stop.save_task_session.assert_not_called()
    mock_print.assert_any_call(f"Error stopping task 'Error Task':")
    mock_print.assert_any_call("Internal domain error on stop.")
