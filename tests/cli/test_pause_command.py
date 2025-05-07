import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time

# Attempt to import commands and domain models
try:
    from src.cli.pause_command import PauseCommand
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
        InvalidStateTransitionError,
    )
    from src.infra.storage.json_storage import JsonStorage
except ImportError:
    PauseCommand = None  # type: ignore
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    InvalidStateTransitionError = None  # type: ignore
    JsonStorage = None  # type: ignore

FROZEN_TIME_STR = "2024-01-11T14:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.fixture
def mock_storage_provider_pause():  # Renamed to avoid conflict if tests run together
    if JsonStorage is None:
        pytest.skip("JsonStorage not available")
    mock_storage = mock.MagicMock(spec=JsonStorage)
    mock_storage.get_all_sessions.return_value = []
    mock_storage.save_task_session.return_value = None
    return mock_storage


@pytest.mark.skipif(
    PauseCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.pause_command.JsonStorage")
def test_pause_command_active_task(
    mock_json_storage_class, mock_print, mock_storage_provider_pause
):
    """Test PauseCommand pauses an active (STARTED) task successfully."""
    started_session = TaskSession(
        task_name="Active Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=30),
        status=TaskSessionStatus.STARTED,
    )
    # Mock the pause method of this specific instance to check it's called
    started_session.pause = mock.MagicMock()

    mock_storage_provider_pause.get_all_sessions.return_value = [started_session]
    mock_json_storage_class.return_value = mock_storage_provider_pause

    command = PauseCommand()
    command.execute([])

    started_session.pause.assert_called_once()  # Verify domain object's pause() was called
    mock_storage_provider_pause.save_task_session.assert_called_once_with(
        started_session
    )
    mock_print.assert_any_call("Task 'Active Task' paused.")


@pytest.mark.skipif(
    PauseCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.pause_command.JsonStorage")
def test_pause_command_no_active_task(
    mock_json_storage_class, mock_print, mock_storage_provider_pause
):
    """Test PauseCommand prints error if no task is STARTED."""
    stopped_session = TaskSession(
        task_name="Old Task",
        start_time=FROZEN_DATETIME - timedelta(days=1),
        status=TaskSessionStatus.STOPPED,
    )
    mock_storage_provider_pause.get_all_sessions.return_value = [stopped_session]
    mock_json_storage_class.return_value = mock_storage_provider_pause

    command = PauseCommand()
    command.execute([])
    mock_storage_provider_pause.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error: No task is currently RUNNING to pause.")


@pytest.mark.skipif(
    PauseCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.pause_command.JsonStorage")
def test_pause_command_already_paused(
    mock_json_storage_class, mock_print, mock_storage_provider_pause
):
    """Test PauseCommand prints error if the active task is already PAUSED."""
    paused_session = TaskSession(
        task_name="Paused Task",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        status=TaskSessionStatus.PAUSED,
    )
    mock_storage_provider_pause.get_all_sessions.return_value = [paused_session]
    mock_json_storage_class.return_value = mock_storage_provider_pause

    command = PauseCommand()
    command.execute([])
    mock_storage_provider_pause.save_task_session.assert_not_called()
    mock_print.assert_any_call(
        "Error: Task 'Paused Task' is already PAUSED. Cannot pause again."
    )


@pytest.mark.skipif(
    PauseCommand is None
    or TaskSession is None
    or InvalidStateTransitionError is None
    or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.pause_command.JsonStorage")
def test_pause_command_domain_error(
    mock_json_storage_class, mock_print, mock_storage_provider_pause
):
    """Test PauseCommand handles InvalidStateTransitionError from domain."""
    # This case should ideally not be hit if CLI logic is correct, but tests robustness
    # For example, if somehow a STOPPED session was found and pause attempted on it.
    stopped_session = TaskSession(
        task_name="Stopped Task",
        start_time=FROZEN_DATETIME - timedelta(hours=2),
        status=TaskSessionStatus.STOPPED,
    )

    def mock_pause_method():
        raise InvalidStateTransitionError(
            "Cannot pause a session that is already STOPPED."
        )

    stopped_session.pause = mock_pause_method

    mock_storage_provider_pause.get_all_sessions.return_value = [stopped_session]
    mock_json_storage_class.return_value = mock_storage_provider_pause

    command = PauseCommand()
    # We need to simulate the command identifying this session as the one to pause.
    # The current pause command logic will determine this. For now, let's assume it picks one.
    # If the command's logic correctly filters out STOPPED sessions, this direct test might be
    # tricky. A better way: ensure PauseCommand *only* tries to pause STARTED sessions.
    # This test becomes more about if pause() itself fails, how the CLI command reacts.

    # Let's refine: test that if a session is identified as active (STARTED) but its .pause()
    # fails, the CLI handles it. This requires the CLI to find a STARTED session first.
    active_session_causing_error = TaskSession(
        task_name="Error Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=5),
        status=TaskSessionStatus.STARTED,
    )
    error_message = "Internal domain error on pause."
    active_session_causing_error.pause = mock.MagicMock(
        side_effect=InvalidStateTransitionError(error_message)
    )
    mock_storage_provider_pause.get_all_sessions.return_value = [
        active_session_causing_error
    ]

    command.execute([])
    mock_storage_provider_pause.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error pausing task 'Error Task':")
    mock_print.assert_any_call(error_message)


@pytest.mark.skipif(
    PauseCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.pause_command.JsonStorage")
def test_pause_command_save_error(
    mock_json_storage_class, mock_print, mock_storage_provider_pause
):
    """Test PauseCommand handles exceptions during storage save."""
    active_session = TaskSession(
        task_name="Save Fail Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=10),
        status=TaskSessionStatus.STARTED,
    )
    # Mock pause to work correctly in this instance
    active_session.pause = mock.MagicMock()
    
    mock_storage_provider_pause.get_all_sessions.return_value = [active_session]
    
    # Make save_task_session raise an error
    save_error_message = "Disk is full!"
    mock_storage_provider_pause.save_task_session.side_effect = Exception(save_error_message)
    
    mock_json_storage_class.return_value = mock_storage_provider_pause

    command = PauseCommand()
    command.execute([])

    active_session.pause.assert_called_once() # Ensure pause was attempted
    mock_storage_provider_pause.save_task_session.assert_called_once_with(active_session)
    mock_print.assert_any_call("Error saving paused task 'Save Fail Task':")
    mock_print.assert_any_call(save_error_message)
