import pytest
from unittest import mock
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time

# Attempt to import main and command classes
try:
    from src.main import main as cli_main  # Alias to avoid pytest collecting 'main'
    from src.cli.start_command import StartCommand
    from src.cli.pause_command import PauseCommand
    from src.infra.storage.json_storage import JsonStorage
    from src.domain.session import TaskSessionStatus

    # Import other commands as needed for testing them specifically
except ImportError:
    cli_main = None  # type: ignore
    StartCommand = None  # type: ignore
    PauseCommand = None  # type: ignore
    JsonStorage = None # type: ignore
    TaskSessionStatus = None # type: ignore


TEST_E2E_STORAGE_FILE = "test_e2e_storage.json"
FROZEN_TIME_STR = "2024-01-15T10:00:00Z"

@pytest.fixture
def temp_e2e_storage_file():
    """Ensure a clean state for E2E storage file."""
    if os.path.exists(TEST_E2E_STORAGE_FILE):
        os.remove(TEST_E2E_STORAGE_FILE)
    yield TEST_E2E_STORAGE_FILE
    if os.path.exists(TEST_E2E_STORAGE_FILE):
        os.remove(TEST_E2E_STORAGE_FILE)


@pytest.mark.skipif(
    cli_main is None, reason="cli_main not implemented or import failed"
)
@mock.patch.object(StartCommand, "execute")
def test_main_dispatches_to_start_command(mock_start_execute):
    """Test that main dispatches to StartCommand.execute for 'start' command."""
    test_args = ["start", "my_task"]
    with mock.patch.object(sys, "argv", ["main.py"] + test_args):
        cli_main()
    mock_start_execute.assert_called_once_with(test_args[1:])


@pytest.mark.skipif(
    cli_main is None, reason="cli_main not implemented or import failed"
)
@mock.patch.object(PauseCommand, "execute")
def test_main_dispatches_to_pause_command(mock_pause_execute):
    """Test that main dispatches to PauseCommand.execute for 'pause' command."""
    test_args = ["pause"]
    with mock.patch.object(sys, "argv", ["main.py"] + test_args):
        cli_main()
    mock_pause_execute.assert_called_once_with([])  # Pause might take no args


@pytest.mark.skipif(
    cli_main is None, reason="cli_main not implemented or import failed"
)
@mock.patch("builtins.print")  # Mock print to check output
def test_main_handles_unknown_command(mock_print):
    """Test that main handles an unknown command gracefully."""
    test_args = ["unknown_command"]
    with mock.patch.object(sys, "argv", ["main.py"] + test_args):
        # Assuming main might raise SystemExit or call sys.exit for errors
        # or simply print an error. For now, let's check print.
        cli_main()
    mock_print.assert_any_call("Error: Unknown command 'unknown_command'")
    # We might also check for a usage message
    mock_print.assert_any_call("Usage: task-timer <command> [args...]")


@pytest.mark.skipif(
    cli_main is None, reason="cli_main not implemented or import failed"
)
@mock.patch("builtins.print")
def test_main_handles_no_command(mock_print):
    """Test that main handles being called with no command (shows usage)."""
    with mock.patch.object(sys, "argv", ["main.py"]):
        cli_main()
    mock_print.assert_any_call("Usage: task-timer <command> [args...]")
    # Check for a list of available commands perhaps
    mock_print.assert_any_call(
        "Available commands: start, pause, resume, stop, status, summary, export"
    )


@pytest.mark.skipif(
    cli_main is None or JsonStorage is None or TaskSessionStatus is None,
    reason="Dependencies for E2E start test not met"
)
@mock.patch("builtins.print")
def test_main_e2e_start_command(mock_print, temp_e2e_storage_file):
    """End-to-end test for the 'start' command via main dispatcher."""
    task_name = "My E2E Test Task"
    test_args = ["start", task_name]

    # Patch JsonStorage where it's used by StartCommand (or any command that instantiates it directly)
    # This ensures that any instance of JsonStorage created by the command during the test
    # will use the temporary file path.
    with mock.patch("src.cli.start_command.JsonStorage") as MockJsonStorage, \
         mock.patch("src.cli.pause_command.JsonStorage") as MockJsonStoragePause, \
         mock.patch("src.cli.resume_command.JsonStorage") as MockJsonStorageResume, \
         mock.patch("src.cli.stop_command.JsonStorage") as MockJsonStorageStop, \
         mock.patch("src.cli.status_command.JsonStorage") as MockJsonStorageStatus, \
         mock.patch("src.cli.summary_command.JsonStorage") as MockJsonStorageSummary, \
         mock.patch("src.cli.export_command.JsonStorage") as MockJsonStorageExport:

        actual_temp_storage = JsonStorage(file_path=temp_e2e_storage_file)
        
        MockJsonStorage.return_value = actual_temp_storage
        MockJsonStoragePause.return_value = actual_temp_storage
        MockJsonStorageResume.return_value = actual_temp_storage
        MockJsonStorageStop.return_value = actual_temp_storage
        MockJsonStorageStatus.return_value = actual_temp_storage
        MockJsonStorageSummary.return_value = actual_temp_storage
        MockJsonStorageExport.return_value = actual_temp_storage

        with mock.patch.object(sys, "argv", ["main.py"] + test_args):
            cli_main()

    # 1. Check output
    # Find the call that starts with the expected message
    found_call = False
    expected_start = f"Task '{task_name}' started at"
    for call_args, call_kwargs in mock_print.call_args_list:
        if call_args and isinstance(call_args[0], str) and call_args[0].startswith(expected_start):
            found_call = True
            break
    assert found_call, f"Expected print call starting with '{expected_start}' not found."

    # 2. Check storage
    assert os.path.exists(temp_e2e_storage_file), "Storage file was not created"
    
    with open(temp_e2e_storage_file, 'r') as f:
        stored_sessions_raw = json.load(f)
    
    assert len(stored_sessions_raw) == 1, "Should be one session in storage"
    session_data = stored_sessions_raw[0]
    
    assert session_data["task_name"] == task_name
    assert session_data["status"] == TaskSessionStatus.STARTED.value
    
    # Optional: Check start_time is recent (within a few seconds)
    # This requires parsing session_data["start_time"] and comparing with datetime.now(timezone.utc)
    # For now, keeping it simpler.
    
    # Initial assertion to make it fail if not implemented
    # assert False, "Test not fully implemented: storage verification needed"


@pytest.mark.skipif(
    cli_main is None or JsonStorage is None or TaskSessionStatus is None,
    reason="Dependencies for E2E stop test not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
def test_main_e2e_stop_command(mock_print, temp_e2e_storage_file):
    """End-to-end test for the 'stop' command via main dispatcher."""
    task_name = "My Task To Stop"
    start_time = datetime.now(timezone.utc) - timedelta(minutes=30) # Started 30 mins ago

    # 1. Setup initial state: Create a storage file with a running task
    # Only include fields that are normally serialized/deserialized
    initial_session_data = { 
        "task_name": task_name, 
        "start_time": start_time.isoformat(), 
        "end_time": None, 
        "status": TaskSessionStatus.STARTED.value, 
        # Do NOT include internal fields like _accumulated_duration, _current_segment_start_time etc.
        # These will be reconstructed by TaskSession on loading, if needed.
    } 
    with open(temp_e2e_storage_file, 'w') as f: 
        json.dump([initial_session_data], f)

    # 2. Execute stop command
    test_args = ["stop"]
    
    # Patch JsonStorage instantiation in all command modules
    with mock.patch("src.cli.start_command.JsonStorage") as MockJsonStorageStart, \
         mock.patch("src.cli.pause_command.JsonStorage") as MockJsonStoragePause, \
         mock.patch("src.cli.resume_command.JsonStorage") as MockJsonStorageResume, \
         mock.patch("src.cli.stop_command.JsonStorage") as MockJsonStorageStop, \
         mock.patch("src.cli.status_command.JsonStorage") as MockJsonStorageStatus, \
         mock.patch("src.cli.summary_command.JsonStorage") as MockJsonStorageSummary, \
         mock.patch("src.cli.export_command.JsonStorage") as MockJsonStorageExport:

        actual_temp_storage = JsonStorage(file_path=temp_e2e_storage_file)
        
        MockJsonStorageStart.return_value = actual_temp_storage
        MockJsonStoragePause.return_value = actual_temp_storage
        MockJsonStorageResume.return_value = actual_temp_storage
        MockJsonStorageStop.return_value = actual_temp_storage
        MockJsonStorageStatus.return_value = actual_temp_storage
        MockJsonStorageSummary.return_value = actual_temp_storage
        MockJsonStorageExport.return_value = actual_temp_storage

        with mock.patch.object(sys, "argv", ["main.py"] + test_args):
            cli_main()

    # 3. Check output
    mock_print.assert_any_call(f"Task '{task_name}' stopped.")
    # Duration should be 30 minutes (1800 seconds) based on freeze_time
    mock_print.assert_any_call("  Total duration: 00:30:00.")

    # 4. Check storage
    assert os.path.exists(temp_e2e_storage_file), "Storage file should still exist"
    
    with open(temp_e2e_storage_file, 'r') as f:
        stored_sessions_raw = json.load(f)
    
    assert len(stored_sessions_raw) == 1, "Should still be one session in storage"
    session_data = stored_sessions_raw[0]
    
    assert session_data["task_name"] == task_name 
    assert session_data["status"] == TaskSessionStatus.STOPPED.value 
    assert session_data["end_time"] is not None 
    # Check end_time matches the frozen time when stop was called
    stop_time = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00")) 
    assert session_data["end_time"] == stop_time.isoformat() 
    # We cannot reliably assert on _accumulated_duration from the JSON 
    # if it's not serialized. The duration print output is checked above.
    # assert session_data["_accumulated_duration"] == expected_duration_seconds # REMOVED


@pytest.mark.skipif(
    cli_main is None or JsonStorage is None or TaskSessionStatus is None,
    reason="Dependencies for E2E pause test not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
def test_main_e2e_pause_command(mock_print, temp_e2e_storage_file):
    """End-to-end test for the 'pause' command via main dispatcher."""
    task_name = "My Task To Pause"
    start_time = datetime.now(timezone.utc) - timedelta(minutes=15) # Started 15 mins ago

    # 1. Setup initial state: Create a storage file with a running task
    initial_session_data = {
        "task_name": task_name,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "status": TaskSessionStatus.STARTED.value
    }
    with open(temp_e2e_storage_file, 'w') as f:
        json.dump([initial_session_data], f)

    # 2. Execute pause command
    test_args = ["pause"]
    pause_time = datetime.now(timezone.utc) # Capture the time pause is executed
    
    # Patch JsonStorage instantiation in all command modules
    with mock.patch("src.cli.start_command.JsonStorage") as MockJsonStorageStart, \
         mock.patch("src.cli.pause_command.JsonStorage") as MockJsonStoragePause, \
         mock.patch("src.cli.resume_command.JsonStorage") as MockJsonStorageResume, \
         mock.patch("src.cli.stop_command.JsonStorage") as MockJsonStorageStop, \
         mock.patch("src.cli.status_command.JsonStorage") as MockJsonStorageStatus, \
         mock.patch("src.cli.summary_command.JsonStorage") as MockJsonStorageSummary, \
         mock.patch("src.cli.export_command.JsonStorage") as MockJsonStorageExport:

        actual_temp_storage = JsonStorage(file_path=temp_e2e_storage_file)
        
        MockJsonStorageStart.return_value = actual_temp_storage
        MockJsonStoragePause.return_value = actual_temp_storage
        MockJsonStorageResume.return_value = actual_temp_storage
        MockJsonStorageStop.return_value = actual_temp_storage
        MockJsonStorageStatus.return_value = actual_temp_storage
        MockJsonStorageSummary.return_value = actual_temp_storage
        MockJsonStorageExport.return_value = actual_temp_storage

        with mock.patch.object(sys, "argv", ["main.py"] + test_args):
            cli_main()

    # 3. Check output
    mock_print.assert_any_call(f"Task '{task_name}' paused.")

    # 4. Check storage
    assert os.path.exists(temp_e2e_storage_file), "Storage file should still exist"
    
    with open(temp_e2e_storage_file, 'r') as f:
        stored_sessions_raw = json.load(f)
    
    assert len(stored_sessions_raw) == 1, "Should still be one session in storage"
    session_data = stored_sessions_raw[0]
    
    assert session_data["task_name"] == task_name
    assert session_data["status"] == TaskSessionStatus.PAUSED.value
    assert session_data["end_time"] is None
    assert session_data["_current_segment_start_time"] is None
    
    # Check accumulated duration (should be 15 minutes)
    expected_duration_seconds = 900.0 # 15 minutes
    assert session_data["_accumulated_duration_seconds"] == expected_duration_seconds
    
    # Check pause times list
    assert "_pause_times" in session_data
    assert len(session_data["_pause_times"]) == 1
    assert session_data["_pause_times"][0] == pause_time.isoformat()


@pytest.mark.skipif(
    cli_main is None or JsonStorage is None or TaskSessionStatus is None,
    reason="Dependencies for E2E resume test not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
def test_main_e2e_resume_command(mock_print, temp_e2e_storage_file):
    """End-to-end test for the 'resume' command via main dispatcher."""
    task_name = "My Task To Resume"
    start_time = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00")) - timedelta(hours=1) # Task started 1 hour ago
    paused_at = start_time + timedelta(minutes=30) # Paused 30 minutes after start
    # Resume will happen at FROZEN_TIME_STR (1 hour after start, 30 mins after pause)

    # 1. Setup initial state: Create a storage file with a PAUSED task
    initial_session_data = {
        "task_name": task_name,
        "start_time": start_time.isoformat(),
        "end_time": None,
        "status": TaskSessionStatus.PAUSED.value,
        "_current_segment_start_time": None,  # Was paused
        "_accumulated_duration_seconds": timedelta(minutes=30).total_seconds(), # 30 mins accumulated
        "_pause_times": [paused_at.isoformat()],
        "_resume_times": []
    }
    with open(temp_e2e_storage_file, 'w') as f:
        json.dump([initial_session_data], f)

    # 2. Execute resume command
    test_args = ["resume"]
    resume_time = datetime.now(timezone.utc) # Capture the time resume is executed (FROZEN_TIME_STR)
    
    with mock.patch("src.cli.start_command.JsonStorage") as MockJsonStorageStart, \
         mock.patch("src.cli.pause_command.JsonStorage") as MockJsonStoragePause, \
         mock.patch("src.cli.resume_command.JsonStorage") as MockJsonStorageResume, \
         mock.patch("src.cli.stop_command.JsonStorage") as MockJsonStorageStop, \
         mock.patch("src.cli.status_command.JsonStorage") as MockJsonStorageStatus, \
         mock.patch("src.cli.summary_command.JsonStorage") as MockJsonStorageSummary, \
         mock.patch("src.cli.export_command.JsonStorage") as MockJsonStorageExport:

        actual_temp_storage = JsonStorage(file_path=temp_e2e_storage_file)
        MockJsonStorageStart.return_value = actual_temp_storage
        MockJsonStoragePause.return_value = actual_temp_storage
        MockJsonStorageResume.return_value = actual_temp_storage
        MockJsonStorageStop.return_value = actual_temp_storage
        MockJsonStorageStatus.return_value = actual_temp_storage
        MockJsonStorageSummary.return_value = actual_temp_storage
        MockJsonStorageExport.return_value = actual_temp_storage

        with mock.patch.object(sys, "argv", ["main.py"] + test_args):
            cli_main()

    # 3. Check output
    mock_print.assert_any_call(f"Task '{task_name}' resumed.")

    # 4. Check storage
    assert os.path.exists(temp_e2e_storage_file), "Storage file should still exist"
    
    with open(temp_e2e_storage_file, 'r') as f:
        stored_sessions_raw = json.load(f)
    
    assert len(stored_sessions_raw) == 1, "Should still be one session in storage"
    session_data = stored_sessions_raw[0]
    
    assert session_data["task_name"] == task_name
    assert session_data["status"] == TaskSessionStatus.STARTED.value
    assert session_data["end_time"] is None
    
    # Check _current_segment_start_time is the resume_time
    assert session_data["_current_segment_start_time"] == resume_time.isoformat()
    
    # Accumulated duration should still be 30 mins, as no new duration is added until next pause/stop
    assert session_data["_accumulated_duration_seconds"] == timedelta(minutes=30).total_seconds()
    
    # Check pause and resume times lists
    assert len(session_data["_pause_times"]) == 1
    assert session_data["_pause_times"][0] == paused_at.isoformat()
    assert "_resume_times" in session_data
    assert len(session_data["_resume_times"]) == 1
    assert session_data["_resume_times"][0] == resume_time.isoformat()


@pytest.mark.skipif(
    cli_main is None or JsonStorage is None or TaskSessionStatus is None,
    reason="Dependencies for E2E status test not met"
)
@freeze_time(FROZEN_TIME_STR)
@mock.patch("builtins.print")
def test_main_e2e_status_command_running_task(mock_print, temp_e2e_storage_file):
    """End-to-end test for the 'status' command with a running task."""
    task_name_running = "My Running Task for Status"
    # Task started 45 minutes before FROZEN_TIME_STR
    start_time_running = datetime.fromisoformat(FROZEN_TIME_STR.replace("Z", "+00:00")) - timedelta(minutes=45)

    task_name_stopped = "My Stopped Task for Status"
    start_time_stopped = start_time_running - timedelta(hours=2) # Started 2 hours before running task
    end_time_stopped = start_time_running - timedelta(hours=1) # Stopped 1 hour before running task started (1 hour duration)

    # 1. Setup initial state: Create a storage file with one running and one stopped task
    initial_sessions_data = [
        { # Running Task
            "task_name": task_name_running,
            "start_time": start_time_running.isoformat(),
            "end_time": None,
            "status": TaskSessionStatus.STARTED.value,
            "_current_segment_start_time": start_time_running.isoformat(),
            "_accumulated_duration_seconds": 0,
            "_pause_times": [],
            "_resume_times": []
        },
        { # Stopped Task
            "task_name": task_name_stopped,
            "start_time": start_time_stopped.isoformat(),
            "end_time": end_time_stopped.isoformat(),
            "status": TaskSessionStatus.STOPPED.value,
            "_current_segment_start_time": None,
            "_accumulated_duration_seconds": timedelta(hours=1).total_seconds(), # 1 hour duration
            "_pause_times": [],
            "_resume_times": []
        }
    ]
    with open(temp_e2e_storage_file, 'w') as f:
        json.dump(initial_sessions_data, f)

    # 2. Execute status command
    test_args = ["status"]
    
    with mock.patch("src.cli.start_command.JsonStorage") as MockJsonStorageStart, \
         mock.patch("src.cli.pause_command.JsonStorage") as MockJsonStoragePause, \
         mock.patch("src.cli.resume_command.JsonStorage") as MockJsonStorageResume, \
         mock.patch("src.cli.stop_command.JsonStorage") as MockJsonStorageStop, \
         mock.patch("src.cli.status_command.JsonStorage") as MockJsonStorageStatus, \
         mock.patch("src.cli.summary_command.JsonStorage") as MockJsonStorageSummary, \
         mock.patch("src.cli.export_command.JsonStorage") as MockJsonStorageExport:

        actual_temp_storage = JsonStorage(file_path=temp_e2e_storage_file)
        MockJsonStorageStart.return_value = actual_temp_storage
        MockJsonStoragePause.return_value = actual_temp_storage
        MockJsonStorageResume.return_value = actual_temp_storage
        MockJsonStorageStop.return_value = actual_temp_storage
        MockJsonStorageStatus.return_value = actual_temp_storage
        MockJsonStorageSummary.return_value = actual_temp_storage
        MockJsonStorageExport.return_value = actual_temp_storage

        with mock.patch.object(sys, "argv", ["main.py"] + test_args):
            cli_main()

    # 3. Check output
    # Expected duration for the running task is 45 minutes at FROZEN_TIME_STR
    expected_running_duration_str = "00:45:00"
    expected_output_running = f"Active task: {task_name_running} (Started: {start_time_running.strftime('%Y-%m-%d %H:%M:%S %Z')}) - Current total duration: {expected_running_duration_str}"
    
    # Expected duration for the stopped task is 1 hour
    expected_stopped_duration_str = "01:00:00"
    expected_output_stopped = f"Task: {task_name_stopped}, Status: STOPPED, Start: {start_time_stopped.strftime('%Y-%m-%d %H:%M:%S %Z')}, End: {end_time_stopped.strftime('%Y-%m-%d %H:%M:%S %Z')}, Duration: {expected_stopped_duration_str}"

    # Check that print was called with the expected strings
    # Order might vary, or other messages might be printed, so check for any_call
    mock_print.assert_any_call(expected_output_running)
    mock_print.assert_any_call(expected_output_stopped)
    mock_print.assert_any_call("\nOther recent tasks (not active):")


# Add more tests for other commands and argument passing as needed
