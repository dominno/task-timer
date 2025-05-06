import pytest
import os

# import json # Removed unused import
from unittest import mock
from datetime import datetime, timedelta, timezone

# Attempt to import JsonStorage and TaskSession
try:
    from src.infra.storage.json_storage import JsonStorage
    from src.domain.session import TaskSession, TaskSessionStatus
    from src.infra.storage.base import (
        StorageProvider,
        StorageWriteError,
    )  # To check inheritance and import StorageWriteError
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
    start_time1 = datetime.now() - timedelta(hours=2)
    start_time2 = datetime.now() - timedelta(hours=1)
    if start_time1.tzinfo is not None:
        start_time1 = start_time1.astimezone(timezone.utc).replace(tzinfo=None)
    if start_time2.tzinfo is not None:
        start_time2 = start_time2.astimezone(timezone.utc).replace(tzinfo=None)
    session1 = TaskSession(task_name="Task 1", start_time=start_time1)
    session2 = TaskSession(
        task_name="Task 2", start_time=start_time2, status=TaskSessionStatus.PAUSED
    )
    temp_json_storage.save_task_session(session1)
    temp_json_storage.save_task_session(session2)
    sessions_retrieved = temp_json_storage.get_all_sessions()
    assert len(sessions_retrieved) == 2
    assert sessions_retrieved[0].task_name == "Task 1"
    assert sessions_retrieved[1].task_name == "Task 2"
    assert sessions_retrieved[0].start_time.replace(
        microsecond=0
    ) == start_time1.replace(microsecond=0)
    assert sessions_retrieved[1].start_time.replace(
        microsecond=0
    ) == start_time2.replace(microsecond=0)
    assert sessions_retrieved[1].status == TaskSessionStatus.PAUSED


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


# Further tests for actual file I/O, error handling, etc., will be added incrementally.
