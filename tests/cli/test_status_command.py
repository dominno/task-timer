import pytest
from unittest import mock
from datetime import datetime, timedelta
from freezegun import freeze_time

# Attempt to import commands and domain models
try:
    from src.cli.status_command import (
        StatusCommand,
    )  # Assuming it will be in status_command.py
    from src.domain.session import TaskSession, TaskSessionStatus
    from src.infra.storage.json_storage import JsonStorage
    from src.cli.cli_utils import format_timedelta_for_cli  # UPDATED IMPORT PATH
except ImportError:
    StatusCommand = None  # type: ignore
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    JsonStorage = None  # type: ignore
    format_timedelta_for_cli = None  # type: ignore

FROZEN_TIME_STR = "2024-01-14T10:00:00Z"
FROZEN_DATETIME = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00"))


@pytest.fixture
def mock_storage_provider_status():
    if JsonStorage is None:
        pytest.skip("JsonStorage not available")
    mock_storage = mock.MagicMock(spec=JsonStorage)
    mock_storage.get_all_sessions.return_value = []
    return mock_storage


@pytest.mark.skipif(
    StatusCommand is None
    or TaskSession is None
    or JsonStorage is None
    or format_timedelta_for_cli is None,
    reason="Dependencies not met",
)
@mock.patch("builtins.print")
@mock.patch("src.cli.status_command.JsonStorage")
def test_status_command_running_task(
    mock_json_storage_class, mock_print, mock_storage_provider_status
):
    with freeze_time(FROZEN_TIME_STR):
        """Test StatusCommand shows details for a RUNNING task."""
        start_time = FROZEN_DATETIME - timedelta(minutes=15, seconds=30)
        running_session = TaskSession(
            task_name="Work in Progress",
            start_time=start_time,
            status=TaskSessionStatus.STARTED,
        )
        # The duration property will be called by the command
        # For a running session, duration is live: FROZEN_DATETIME - start_time
        expected_duration = FROZEN_DATETIME - start_time

        mock_storage_provider_status.get_all_sessions.return_value = [running_session]
        mock_json_storage_class.return_value = mock_storage_provider_status

        command = StatusCommand()
        command.execute([])

        formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted_duration = format_timedelta_for_cli(expected_duration)
        mock_print.assert_any_call("Task 'Work in Progress' is RUNNING.")
        mock_print.assert_any_call("  Started at: " + formatted_start_time)
        mock_print.assert_any_call("  Current duration: " + formatted_duration + ".")


@pytest.mark.skipif(
    StatusCommand is None
    or TaskSession is None
    or JsonStorage is None
    or format_timedelta_for_cli is None,
    reason="Dependencies not met",
)
@mock.patch("builtins.print")
@mock.patch("src.cli.status_command.JsonStorage")
def test_status_command_paused_task(
    mock_json_storage_class, mock_print, mock_storage_provider_status
):
    with freeze_time(FROZEN_TIME_STR):
        """Test StatusCommand shows details for a PAUSED task."""
        start_time = FROZEN_DATETIME - timedelta(hours=1)
        paused_session = TaskSession(
            task_name="On Break", start_time=start_time, status=TaskSessionStatus.PAUSED
        )
        paused_session._accumulated_duration = timedelta(minutes=25, seconds=5)

        mock_storage_provider_status.get_all_sessions.return_value = [paused_session]
        mock_json_storage_class.return_value = mock_storage_provider_status

        command = StatusCommand()
        command.execute([])

        formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted_duration = format_timedelta_for_cli(
            paused_session._accumulated_duration
        )
        mock_print.assert_any_call("Task 'On Break' is PAUSED.")
        mock_print.assert_any_call("  Started at: " + formatted_start_time)
        mock_print.assert_any_call(
            "  Accumulated duration: " + formatted_duration + "."
        )


@pytest.mark.skipif(
    StatusCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@mock.patch("builtins.print")
@mock.patch("src.cli.status_command.JsonStorage")
def test_status_command_no_active_task(
    mock_json_storage_class, mock_print, mock_storage_provider_status
):
    with freeze_time(FROZEN_TIME_STR):
        """Test StatusCommand shows 'No active task' if none are STARTED or PAUSED."""
        stopped_session = TaskSession(
            task_name="Finished Work",
            start_time=FROZEN_DATETIME - timedelta(days=1),
            status=TaskSessionStatus.STOPPED,
        )
        mock_storage_provider_status.get_all_sessions.return_value = [stopped_session]
        mock_json_storage_class.return_value = mock_storage_provider_status

        command = StatusCommand()
        command.execute([])
        mock_print.assert_any_call("No active task.")

        # Also test with an empty list of sessions
        mock_print.reset_mock()
        mock_storage_provider_status.get_all_sessions.return_value = []
        command.execute([])
        mock_print.assert_any_call("No active task.")


@pytest.mark.skipif(
    StatusCommand is None or TaskSession is None or JsonStorage is None,
    reason="Dependencies not met",
)
@mock.patch("builtins.print")
@mock.patch("src.cli.status_command.JsonStorage")
def test_status_command_multiple_active_error(
    mock_json_storage_class, mock_print, mock_storage_provider_status
):
    with freeze_time(FROZEN_TIME_STR):
        """Test StatusCommand prints error if multiple active "tasks" are found
        (e.g., one STARTED, one PAUSED)."""
        session1 = TaskSession(
            task_name="Task One",
            start_time=FROZEN_DATETIME - timedelta(hours=2),
            status=TaskSessionStatus.STARTED,
        )
        session2 = TaskSession(
            task_name="Task Two",
            start_time=FROZEN_DATETIME - timedelta(hours=1),
            status=TaskSessionStatus.PAUSED,
        )
        mock_storage_provider_status.get_all_sessions.return_value = [
            session1,
            session2,
        ]
        mock_json_storage_class.return_value = mock_storage_provider_status

        command = StatusCommand()
        command.execute([])
        mock_print.assert_any_call(
            "Error: Multiple active sessions found. Resolve manually."
        )


@pytest.mark.skipif(
    StatusCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@mock.patch("builtins.print")
@mock.patch("src.cli.status_command.JsonStorage")
def test_status_command_storage_access_error(mock_json_storage_class, mock_print):
    """Test StatusCommand handles error when storage.get_all_sessions() fails."""
    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_storage_instance.get_all_sessions.side_effect = Exception(
        "Storage connection failed"
    )
    mock_json_storage_class.return_value = mock_storage_instance

    command = StatusCommand()
    command.execute([])

    mock_print.assert_any_call("Error accessing storage: Storage connection failed")
