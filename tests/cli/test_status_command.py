import pytest
from unittest import mock
from datetime import datetime, timedelta, timezone
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

        formatted_start_time_with_zone = start_time.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        formatted_duration = format_timedelta_for_cli(expected_duration)
        
        expected_output = f"Active task: Work in Progress (Started: {formatted_start_time_with_zone}) - Current total duration: {formatted_duration}"
        mock_print.assert_any_call(expected_output)


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

        formatted_start_time_with_zone = start_time.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        formatted_duration = format_timedelta_for_cli(
            paused_session._accumulated_duration
        )
        
        expected_output = f"Active task: On Break (Started: {formatted_start_time_with_zone}) - Current total duration: {formatted_duration}"
        mock_print.assert_any_call(expected_output)


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
        """Test StatusCommand correctly displays one active and one other task when multiple could be considered active."""
        # session2 is more recent, PAUSED
        session2_start_time = FROZEN_DATETIME - timedelta(hours=1)
        session2 = TaskSession(
            task_name="Task Two (Paused, More Recent)",
            start_time=session2_start_time,
            status=TaskSessionStatus.PAUSED,
        )
        session2._accumulated_duration = timedelta(minutes=10) # Manually set for paused task

        # session1 is older, STARTED
        session1_start_time = FROZEN_DATETIME - timedelta(hours=2)
        session1 = TaskSession(
            task_name="Task One (Started, Older)",
            start_time=session1_start_time,
            status=TaskSessionStatus.STARTED,
        )

        # Order in list for get_all_sessions might matter if start_times were identical
        # but here they are distinct, and StatusCommand sorts them.
        mock_storage_provider_status.get_all_sessions.return_value = [
            session1, # Older
            session2, # More recent
        ]
        mock_json_storage_class.return_value = mock_storage_provider_status

        command = StatusCommand()
        command.execute([])

        # Expected output for session2 (active, paused)
        # StatusCommand uses get_duration_at for active tasks, which for PAUSED returns _accumulated_duration
        s2_formatted_start = session2.start_time.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        s2_formatted_duration = format_timedelta_for_cli(session2._accumulated_duration)
        expected_active_output = f"Active task: {session2.task_name} (Started: {s2_formatted_start}) - Current total duration: {s2_formatted_duration}"
        mock_print.assert_any_call(expected_active_output)

        # Expected header for other tasks
        mock_print.assert_any_call("\nOther recent tasks (not active):")

        # Expected output for session1 (other, started)
        # For "other" tasks, StatusCommand directly uses session.duration.
        # For a STARTED task, session.duration (which is get_duration_at(now)) will calculate live duration.
        s1_live_duration = FROZEN_DATETIME - session1.start_time
        s1_formatted_start = session1.start_time.replace(tzinfo=timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        s1_formatted_duration = format_timedelta_for_cli(s1_live_duration)
        s1_formatted_end = "N/A" # For a STARTED task shown as other
        expected_other_output = f"Task: {session1.task_name}, Status: {session1.status.value}, Start: {s1_formatted_start}, End: {s1_formatted_end}, Duration: {s1_formatted_duration}"
        mock_print.assert_any_call(expected_other_output)

        # Ensure the old error message is NOT called
        with pytest.raises(AssertionError):
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
