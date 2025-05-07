import pytest
import os
import csv
import json

# import json # Removed unused import
from unittest import mock
from datetime import datetime, timedelta, timezone

# Attempt to import JsonStorage and TaskSession
try:
    from src.infra.storage.json_storage import JsonStorage, session_to_dict
    from src.domain.session import TaskSession, TaskSessionStatus
    from src.infra.storage.base import (
        StorageProvider,
        StorageWriteError,
    )  # To check inheritance and import StorageWriteError
    from src.utils.export_utils import task_session_to_csv_row  # Added import
except ImportError:
    JsonStorage = None  # type: ignore
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    StorageProvider = None  # type: ignore

# Define a default path for the test JSON file
TEST_JSON_FILE_PATH = "test_task_timer_records.json"


@pytest.fixture
def temp_json_storage():
    """Fixture to create a JsonStorage instance with a temporary file path."""
    if TaskSession is None:
        pytest.skip("TaskSession not available for JsonStorage tests")
    storage = JsonStorage(file_path=TEST_JSON_FILE_PATH)
    yield storage
    if os.path.exists(TEST_JSON_FILE_PATH):
        os.remove(TEST_JSON_FILE_PATH)


@pytest.mark.skipif(
    JsonStorage is None or StorageProvider is None,
    reason="JsonStorage or StorageProvider not implemented/imported",
)
def test_json_storage_is_storage_provider(temp_json_storage):
    """Tests that JsonStorage is a subclass of StorageProvider."""
    assert isinstance(temp_json_storage, StorageProvider)


@pytest.mark.skipif(
    JsonStorage is None, reason="JsonStorage not implemented or import failed"
)
def test_json_storage_instantiation(temp_json_storage):
    """Test basic instantiation of JsonStorage and callable methods (stubs)."""
    assert temp_json_storage is not None
    assert callable(temp_json_storage.save_task_session)
    assert callable(temp_json_storage.get_all_sessions)
    assert callable(temp_json_storage.clear)


@pytest.mark.skipif(
    JsonStorage is None, reason="JsonStorage not implemented or import failed"
)
def test_get_all_sessions_stub(temp_json_storage):
    """Test that get_all_sessions can be called and returns a list (stub)."""
    try:
        result = temp_json_storage.get_all_sessions()
        assert isinstance(result, list), "get_all_sessions should return a list"
    except Exception as e:
        pytest.fail(f"get_all_sessions (stub) raised an exception: {e}")


@pytest.mark.skipif(
    JsonStorage is None, reason="JsonStorage not implemented or import failed"
)
def test_clear_stub(temp_json_storage):
    """Test that clear can be called (stub)."""
    try:
        temp_json_storage.clear()
    except Exception as e:
        pytest.fail(f"clear (stub) raised an exception: {e}")


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None or TaskSessionStatus is None,
    reason="Dependencies not met",
)
def test_save_and_get_single_session(temp_json_storage):
    """Test saving a single session and then retrieving it."""
    start_time = datetime.now()
    if start_time.tzinfo is not None:
        start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
    session_to_save = TaskSession(
        task_name="Test Save Task",
        start_time=start_time,
        status=TaskSessionStatus.STARTED,
    )
    temp_json_storage.save_task_session(session_to_save)
    sessions_retrieved = temp_json_storage.get_all_sessions()
    assert len(sessions_retrieved) == 1
    retrieved_session = sessions_retrieved[0]
    assert retrieved_session.task_name == session_to_save.task_name
    assert retrieved_session.start_time.replace(
        microsecond=0
    ) == session_to_save.start_time.replace(microsecond=0)
    assert retrieved_session.status == session_to_save.status
    assert retrieved_session.end_time is None


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None, reason="Dependencies not met"
)
def test_get_all_sessions_empty_file(temp_json_storage):
    """Test get_all_sessions returns an empty list
    if the JSON file is empty or non-existent."""
    sessions = temp_json_storage.get_all_sessions()
    assert sessions == []


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None, reason="Dependencies not met"
)
def test_save_multiple_sessions(temp_json_storage):
    """Test saving multiple sessions and retrieving them in order."""
    now_utc = datetime.now(timezone.utc)  # Work with UTC from the start
    start_time1_orig = now_utc - timedelta(hours=2)
    start_time2_orig = now_utc - timedelta(hours=1)

    session1 = TaskSession(task_name="Task 1", start_time=start_time1_orig)
    session2 = TaskSession(
        task_name="Task 2", start_time=start_time2_orig, status=TaskSessionStatus.PAUSED
    )
    temp_json_storage.save_task_session(session1)
    temp_json_storage.save_task_session(session2)
    sessions_retrieved = temp_json_storage.get_all_sessions()
    assert len(sessions_retrieved) == 2
    assert sessions_retrieved[0].task_name == "Task 1"
    assert sessions_retrieved[1].task_name == "Task 2"

    # Compare after ensuring both are UTC and microseconds are
    # zeroed out for robust comparison
    assert sessions_retrieved[0].start_time.replace(
        microsecond=0
    ) == start_time1_orig.replace(microsecond=0)
    assert sessions_retrieved[1].start_time.replace(
        microsecond=0
    ) == start_time2_orig.replace(microsecond=0)


@pytest.mark.skipif(
    JsonStorage is None, reason="JsonStorage not implemented or import failed"
)
def test_get_all_sessions_corrupted_file(temp_json_storage):
    """Test get_all_sessions returns an empty list if the JSON file is corrupted."""
    # Create a corrupted JSON file
    with open(TEST_JSON_FILE_PATH, "w") as f:
        f.write("this is not valid json{")

    sessions = temp_json_storage.get_all_sessions()
    assert sessions == [], "Should return empty list for corrupted JSON"


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None, reason="Dependencies not met"
)
@mock.patch("builtins.open", new_callable=mock.mock_open)
def test_load_sessions_handles_io_error_on_read(mock_open_file, temp_json_storage):
    """Test _load_sessions_from_file handles IOError on read and returns empty list."""
    # Configure the mock_open to raise IOError when read
    mock_open_file.side_effect = IOError("Permission denied")
    # We need to ensure the file path check still works,
    # or bypass it if open is fully mocked.
    # For this test, let's assume os.path.exists might be true but open fails.
    with mock.patch("os.path.exists", return_value=True):
        with mock.patch("os.path.getsize", return_value=100):  # Simulate non-empty file
            sessions = temp_json_storage._load_sessions_from_file()
    assert sessions == [], "Should return empty list if file open for read fails"


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None, reason="Dependencies not met"
)
@mock.patch("builtins.open", new_callable=mock.mock_open)
def test_save_sessions_handles_io_error_on_write(mock_open_file, temp_json_storage):
    """Test _save_sessions_to_file raises StorageWriteError on IOError."""
    mock_open_file.side_effect = IOError("Disk full")
    start_time = datetime.now()
    if start_time.tzinfo is not None:
        start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
    session_to_save = TaskSession(task_name="Test IO Error", start_time=start_time)

    with pytest.raises(
        StorageWriteError, match=r"Failed to write sessions to .*?: Disk full"
    ):
        temp_json_storage._save_sessions_to_file([session_to_save])
    mock_open_file.assert_called_once_with(temp_json_storage.file_path, "w")


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None or task_session_to_csv_row is None,
    reason="Dependencies for CSV export test not met",
)
def test_export_to_csv_successful(temp_json_storage):
    """Test exporting sessions to a CSV file."""
    # 1. Setup: Create some sessions and save them using the internal storage
    now_utc = datetime.now(timezone.utc)
    session1_start = now_utc - timedelta(hours=2)
    session1 = TaskSession(task_name="CSV Export Task 1", start_time=session1_start)
    session1.stop()  # Stop it to make it simple

    session2_start = now_utc - timedelta(hours=1)
    session2 = TaskSession(task_name="CSV Export Task 2", start_time=session2_start)
    # session2 is left running for this test case of export

    temp_json_storage.save_task_session(session1)  # Uses internal records.json
    temp_json_storage.save_task_session(session2)

    # 2. Action: Export to a new CSV file
    export_csv_path = "test_export_output.csv"
    if os.path.exists(export_csv_path):
        os.remove(export_csv_path)  # Clean up if exists from previous failed run

    temp_json_storage.export_to_csv(export_csv_path)

    # 3. Assert: Check if the CSV file was created and contains correct data
    assert os.path.exists(export_csv_path)

    expected_rows = []
    # Header - as defined implicitly by task_session_to_csv_row columns
    expected_header = [
        "task_name",
        "start_time_utc",
        "end_time_utc",
        "status",
        "total_duration_seconds",
        "first_pause_time_utc",
        "last_resume_time_utc",
        "number_of_pauses",
    ]
    expected_rows.append(expected_header)
    expected_rows.append(task_session_to_csv_row(session1))

    # For session2, we need to be careful: its duration is live.
    # To make the test deterministic for CSV content, let's freeze time for its row generation
    # OR, better, for this test, let's also stop session2 before generating its expected row.
    # However, the spirit of exporting might be "as is", so live duration should be captured.
    # For now, to simplify test assertion, let's get its state as it would be written.
    # The actual export_to_csv in JsonStorage will just call get_all_sessions(),
    # which returns the sessions. If a session is RUNNING, its duration is live.
    # CSV content for a running task could change if generated at different times.
    # This is an important consideration for the design of export for live data.
    expected_rows.append(task_session_to_csv_row(session2))  # Add session2 as is

    with open(export_csv_path, "r", newline="") as f:
        reader = csv.reader(f)
        actual_rows = list(reader)

    assert actual_rows == expected_rows

    # Clean up
    if os.path.exists(export_csv_path):
        os.remove(export_csv_path)


@pytest.mark.skipif(
    JsonStorage is None or TaskSession is None,
    reason="Dependencies for JSON export test not met",
)
def test_export_to_json_successful(temp_json_storage):
    """Test exporting sessions to a JSON file."""
    # 1. Setup: Create some sessions and save them using the internal storage
    now_utc = datetime.now(timezone.utc)
    session1_start = now_utc - timedelta(hours=2)
    session1 = TaskSession(task_name="JSON Export Task 1", start_time=session1_start)
    session1.stop()

    session2_start = now_utc - timedelta(hours=1)
    session2 = TaskSession(task_name="JSON Export Task 2", start_time=session2_start)
    # session2 is left running

    temp_json_storage.save_task_session(session1)
    temp_json_storage.save_task_session(session2)

    # 2. Action: Export to a new JSON file
    export_json_path = "test_export_output.json"
    if os.path.exists(export_json_path):
        os.remove(export_json_path)  # Clean up

    temp_json_storage.export_to_json(export_json_path)

    # 3. Assert: Check if the JSON file was created and contains correct data
    assert os.path.exists(export_json_path)

    with open(export_json_path, "r") as f:
        exported_data = json.load(f)

    assert len(exported_data) == 2
    # We can use session_to_dict for comparison, assuming export uses similar logic
    expected_data = [
        session_to_dict(session1),
        session_to_dict(session2),
    ]  # Need session_to_dict

    # Compare field by field for robustness if dict ordering or float precision is an issue
    # For now, direct comparison might work if session_to_dict is deterministic and used by export.
    assert exported_data[0]["task_name"] == expected_data[0]["task_name"]
    assert exported_data[1]["task_name"] == expected_data[1]["task_name"]
    # Add more specific assertions as needed, especially for datetime strings and duration.

    # Clean up
    if os.path.exists(export_json_path):
        os.remove(export_json_path)


# Further tests for actual file I/O, error handling, etc., will be added incrementally.
