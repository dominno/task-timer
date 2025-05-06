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
    ResumeCommand = None  # type: ignore
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

    paused_session.resume.assert_called_once()  # Verify domain object's resume() was called
    mock_storage_provider_resume.save_task_session.assert_called_once_with(
        paused_session
    )
    mock_print.assert_any_call(f"Task 'Paused Task' resumed.")


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
    """Test ResumeCommand prints error if a task is already STARTED (and no other is paused)."""
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
        f"Error: Task 'Running Task' is already RUNNING. No task to resume."
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
    mock_print.assert_any_call(f"Error resuming 'Error Task':")
    mock_print.assert_any_call("Internal domain error on resume.")
