import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time

# Attempt to import commands and domain models
try:
    from src.cli.resume_command import ResumeCommand
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
        InvalidStateTransitionError,
    )
    from src.infra.storage.json_storage import JsonStorage
except ImportError:
    ResumeCommand = None
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    InvalidStateTransitionError = None  # type: ignore
    JsonStorage = None  # type: ignore

FROZEN_TIME_STR = "2024-01-12T10:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.fixture
def mock_storage_provider_resume():  # Renamed for clarity
    if JsonStorage is None:
        pytest.skip("JsonStorage not available")
    mock_storage = mock.MagicMock(spec=JsonStorage)
    mock_storage.get_all_sessions.return_value = []
    mock_storage.save_task_session.return_value = None
    return mock_storage


@pytest.mark.skipif(
    ResumeCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_paused_task(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test ResumeCommand resumes a PAUSED task successfully."""
    paused_session = TaskSession(
        task_name="Paused Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=30),
        status=TaskSessionStatus.PAUSED,
    )
    # Mock the resume method of this specific instance to check it's called
    paused_session.resume = mock.MagicMock()
    # Simulate it having some accumulated duration
    paused_session._accumulated_duration = timedelta(minutes=15)

    mock_storage_provider_resume.get_all_sessions.return_value = [paused_session]
    mock_json_storage_class.return_value = mock_storage_provider_resume

    command = ResumeCommand()
    command.execute([])

    paused_session.resume.assert_called_once()  # Verify domain object's resume()
    mock_storage_provider_resume.save_task_session.assert_called_once_with(
        paused_session
    )
    mock_print.assert_any_call("Task 'Paused Task' resumed.")


@pytest.mark.skipif(
    ResumeCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_no_paused_task(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test ResumeCommand prints error if no task is PAUSED (and none is STARTED)."""
    stopped_session = TaskSession(
        task_name="Old Task",
        start_time=FROZEN_DATETIME - timedelta(days=1),
        status=TaskSessionStatus.STOPPED,
    )
    mock_storage_provider_resume.get_all_sessions.return_value = [
        stopped_session
    ]  # Only a STOPPED session
    mock_json_storage_class.return_value = mock_storage_provider_resume

    command = ResumeCommand()
    command.execute([])
    mock_storage_provider_resume.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error: No task is currently PAUSED to resume.")

    # Test with no sessions at all
    mock_print.reset_mock()
    mock_storage_provider_resume.get_all_sessions.return_value = []
    command.execute([])
    mock_storage_provider_resume.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error: No task is currently PAUSED to resume.")


@pytest.mark.skipif(
    ResumeCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_already_started(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test ResumeCommand prints error if a task is already STARTED."""
    started_session = TaskSession(
        task_name="Running Task",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        status=TaskSessionStatus.STARTED,
    )
    mock_storage_provider_resume.get_all_sessions.return_value = [started_session]
    mock_json_storage_class.return_value = mock_storage_provider_resume

    command = ResumeCommand()
    command.execute([])
    mock_storage_provider_resume.save_task_session.assert_not_called()
    mock_print.assert_any_call(
        "Error: Task 'Running Task' is already RUNNING. No task to resume."
    )


@pytest.mark.skipif(
    ResumeCommand is None
    or TaskSession is None
    or InvalidStateTransitionError is None
    or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_domain_error(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test ResumeCommand handles InvalidStateTransitionError from domain."""
    paused_session_causing_error = TaskSession(
        task_name="Error Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=5),
        status=TaskSessionStatus.PAUSED,
    )
    paused_session_causing_error.resume = mock.MagicMock(
        side_effect=InvalidStateTransitionError("Internal domain error on resume.")
    )
    mock_storage_provider_resume.get_all_sessions.return_value = [
        paused_session_causing_error
    ]
    mock_json_storage_class.return_value = mock_storage_provider_resume

    command = ResumeCommand()
    command.execute([])
    mock_storage_provider_resume.save_task_session.assert_not_called()
    mock_print.assert_any_call("Error resuming 'Error Task':")
    mock_print.assert_any_call("Internal domain error on resume.")


@pytest.mark.skipif(
    ResumeCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_storage_access_error(mock_json_storage_class, mock_print):
    """Test ResumeCommand handles error when storage.get_all_sessions() fails."""
    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_storage_instance.get_all_sessions.side_effect = Exception(
        "Failed to read storage"
    )
    mock_json_storage_class.return_value = mock_storage_instance

    command = ResumeCommand()
    command.execute([])

    mock_print.assert_any_call("Error accessing storage: Failed to read storage")


@pytest.mark.skipif(
    ResumeCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_save_error_after_resume(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test ResumeCommand handles error when saving after a successful resume."""
    paused_session = TaskSession(
        task_name="Save Error Task",
        start_time=FROZEN_DATETIME - timedelta(minutes=30),
        status=TaskSessionStatus.PAUSED,
    )
    paused_session.resume = mock.MagicMock()  # Mock domain resume to ensure it's called

    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_storage_instance.get_all_sessions.return_value = [paused_session]
    mock_storage_instance.save_task_session.side_effect = Exception(
        "Disk full during save"
    )
    mock_json_storage_class.return_value = mock_storage_instance

    command = ResumeCommand()
    command.execute([])

    paused_session.resume.assert_called_once()
    mock_storage_instance.save_task_session.assert_called_once_with(paused_session)
    mock_print.assert_any_call("Error saving 'Save Error Task' after resume:")
    mock_print.assert_any_call("Disk full during save")


@pytest.mark.skipif(
    ResumeCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
@mock.patch("src.cli.resume_command.JsonStorage")
def test_resume_command_paused_exists_but_another_is_running(
    mock_json_storage_class, mock_print, mock_storage_provider_resume
):
    """Test error if a paused task exists, but another task is already RUNNING."""
    paused_task = TaskSession(
        task_name="Should Not Resume",
        start_time=FROZEN_DATETIME - timedelta(hours=2),
        status=TaskSessionStatus.PAUSED,
    )
    running_task = TaskSession(
        task_name="Already Running",
        start_time=FROZEN_DATETIME - timedelta(hours=1),
        status=TaskSessionStatus.STARTED,
    )

    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    # find_paused_session should return paused_task
    # The loop for currently_started_session should find running_task
    mock_storage_instance.get_all_sessions.return_value = [paused_task, running_task]
    mock_json_storage_class.return_value = mock_storage_instance

    command = ResumeCommand()
    command.execute([])

    mock_storage_instance.save_task_session.assert_not_called()  # Nothing should be saved
    paused_task.resume = mock.MagicMock()  # ensure resume was NOT called on paused_task
    paused_task.resume.assert_not_called()

    error_msg = f"Error: Task '{running_task.task_name}' " f"is already RUNNING."
    mock_print.assert_any_call(error_msg)
    mock_print.assert_any_call(f"Cannot resume '{paused_task.task_name}'.")
