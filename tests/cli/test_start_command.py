import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time

# Attempt to import commands and domain models
try:
    from src.cli.start_command import StartCommand
    from src.domain.session import TaskSession, TaskSessionStatus
    from src.infra.storage.json_storage import (
        JsonStorage,
    )  # For mocking its instance methods

    # If StartCommand needs specific exceptions, import them here too.
except ImportError:
    StartCommand = None  # type: ignore
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    JsonStorage = None  # type: ignore

FROZEN_TIME_STR = "2024-01-10T10:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.fixture
def mock_storage_provider():
    """Fixture to create a mock JsonStorage provider."""
    if JsonStorage is None:
        pytest.skip("JsonStorage not available for StartCommand tests")
    # Create a MagicMock instance that *behaves* like a JsonStorage instance
    mock_storage = mock.MagicMock(spec=JsonStorage)
    mock_storage.get_all_sessions.return_value = []  # Default: no existing sessions
    mock_storage.save_task_session.return_value = None
    return mock_storage


@pytest.mark.skipif(
    StartCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch(
    "src.cli.start_command.JsonStorage"
)  # Mock the class itself where it's imported by StartCommand
def test_start_command_new_task(
    mock_json_storage_class, mock_print, mock_storage_provider
):
    """Test StartCommand starts a new task successfully when no active session exists."""
    # Configure the mock JsonStorage class to return our fixture mock instance
    mock_json_storage_class.return_value = mock_storage_provider

    command = StartCommand()
    task_name = "My New Task"
    command.execute([task_name])

    # Verify JsonStorage.get_all_sessions was called to check for active sessions
    mock_storage_provider.get_all_sessions.assert_called_once()

    # Verify JsonStorage.save_task_session was called with the new TaskSession
    assert mock_storage_provider.save_task_session.call_count == 1
    saved_session_arg = mock_storage_provider.save_task_session.call_args[0][0]
    assert isinstance(saved_session_arg, TaskSession)
    assert saved_session_arg.task_name == task_name
    assert saved_session_arg.start_time == FROZEN_DATETIME
    assert saved_session_arg.status == TaskSessionStatus.STARTED

    # Verify console output
    expected_msg = (
        f"Task '{task_name}' started at "
        f"{FROZEN_DATETIME.strftime('%Y-%m-%d %H:%M:%S UTC')}."
    )
    mock_print.assert_any_call(expected_msg)


@pytest.mark.skipif(
    StartCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.start_command.JsonStorage")
def test_start_command_active_session_exists(
    mock_json_storage_class, mock_print, mock_storage_provider
):
    """Test StartCommand prints error if an active (STARTED) session exists."""
    active_session = TaskSession(
        task_name="Existing Task",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        status=TaskSessionStatus.STARTED,
    )
    mock_storage_provider.get_all_sessions.return_value = [active_session]
    mock_json_storage_class.return_value = mock_storage_provider

    command = StartCommand()
    command.execute(["Another Task"])

    mock_storage_provider.get_all_sessions.assert_called_once()
    mock_storage_provider.save_task_session.assert_not_called()
    mock_print.assert_any_call(
        "Error: Task 'Existing Task' is STARTED. Stop it first."
    )


@pytest.mark.skipif(
    StartCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.start_command.JsonStorage")
def test_start_command_paused_session_exists(
    mock_json_storage_class, mock_print, mock_storage_provider
):
    """Test StartCommand prints error if an active (PAUSED) session exists."""
    paused_session = TaskSession(
        task_name="Paused Task",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        status=TaskSessionStatus.PAUSED,
    )
    mock_storage_provider.get_all_sessions.return_value = [paused_session]
    mock_json_storage_class.return_value = mock_storage_provider

    command = StartCommand()
    command.execute(["New Task Name"])

    mock_storage_provider.get_all_sessions.assert_called_once()
    mock_storage_provider.save_task_session.assert_not_called()
    mock_print.assert_any_call(
        "Error: Task 'Paused Task' is PAUSED. Resume and stop, or stop it."
    )


@pytest.mark.skipif(
    StartCommand is None, reason="StartCommand not implemented or import failed"
)
@mock.patch("builtins.print")
def test_start_command_no_task_name(mock_print):
    """Test StartCommand prints error if no task name is provided."""
    command = StartCommand()
    command.execute([])  # No arguments
    mock_print.assert_any_call("Error: Task name is required.")
    mock_print.assert_any_call("Usage: task-timer start <task_name>")
