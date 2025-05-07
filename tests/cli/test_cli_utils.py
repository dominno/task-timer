import pytest
from datetime import timedelta, datetime
from unittest import mock

try:
    from src.cli.cli_utils import format_timedelta_for_cli, find_session_to_operate_on
    from src.domain.session import TaskSession, TaskSessionStatus
except ImportError:
    format_timedelta_for_cli = None
    find_session_to_operate_on = None
    TaskSession = None
    TaskSessionStatus = None

@pytest.mark.skipif(format_timedelta_for_cli is None, reason="format_timedelta_for_cli not available")
@pytest.mark.parametrize(
    "input_delta, expected_output",
    [
        (timedelta(seconds=0), "00:00:00"),
        (timedelta(seconds=5), "00:00:05"),
        (timedelta(seconds=59), "00:00:59"),
        (timedelta(seconds=60), "00:01:00"),
        (timedelta(seconds=119), "00:01:59"),
        (timedelta(minutes=59, seconds=59), "00:59:59"),
        (timedelta(hours=1), "01:00:00"),
        (timedelta(hours=1, minutes=1, seconds=1), "01:01:01"),
        (timedelta(hours=23, minutes=59, seconds=59), "23:59:59"),
        (timedelta(days=1), "24:00:00"), # 1 day
        (timedelta(days=1, hours=1, minutes=30, seconds=5), "25:30:05"),
        (timedelta(seconds=3661), "01:01:01"), # 1 hour, 1 minute, 1 second
        (timedelta(microseconds=500000), "00:00:00"), # Rounds down
        (timedelta(seconds=1.4), "00:00:01"),
        (timedelta(seconds=1.6), "00:00:01"), # Rounds down due to int()
    ],
)
def test_format_timedelta_for_cli(input_delta, expected_output):
    assert format_timedelta_for_cli(input_delta) == expected_output

# Placeholder for find_session_to_operate_on tests
@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies for find_session_to_operate_on not available")
def test_find_session_to_operate_on_placeholder():
    # This is just a placeholder to make the file runnable initially
    # We will add actual tests for find_session_to_operate_on next
    assert True # Ensure this line is indented 

# --- Tests for find_session_to_operate_on ---

# Helper to create a TaskSession for tests
NOW = datetime.now()
if TaskSessionStatus and TaskSession: # Ensure imports worked
    SESSION_STARTED_1 = TaskSession(task_name="TaskS1", start_time=NOW - timedelta(hours=3), status=TaskSessionStatus.STARTED)
    SESSION_STARTED_2 = TaskSession(task_name="TaskS2", start_time=NOW - timedelta(hours=2), status=TaskSessionStatus.STARTED)
    SESSION_PAUSED_1 = TaskSession(task_name="TaskP1", start_time=NOW - timedelta(hours=5), status=TaskSessionStatus.PAUSED)
    SESSION_PAUSED_1._accumulated_duration = timedelta(minutes=30)
    SESSION_PAUSED_2 = TaskSession(task_name="TaskP2", start_time=NOW - timedelta(hours=4), status=TaskSessionStatus.PAUSED)
    SESSION_PAUSED_2._accumulated_duration = timedelta(minutes=60)
    SESSION_STOPPED_1 = TaskSession(task_name="TaskDone", start_time=NOW - timedelta(days=1), status=TaskSessionStatus.STOPPED)

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print") # To capture print calls
def test_fsto_stop_multiple_started(mock_print):
    """Test find_session_to_operate_on for 'stop' with multiple STARTED tasks."""
    sessions = [SESSION_STARTED_1, SESSION_STARTED_2, SESSION_PAUSED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "stop")
    assert result is None
    mock_print.assert_any_call("Error: Multiple RUNNING tasks found. Cannot reliably stop.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_stop_multiple_paused_no_started(mock_print):
    """Test find_session_to_operate_on for 'stop' with multiple PAUSED tasks and no STARTED."""
    sessions = [SESSION_PAUSED_1, SESSION_PAUSED_2, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "stop") # Target status for stop is less relevant here
    assert result is None
    mock_print.assert_any_call("Error: Multiple active (PAUSED) tasks found. Cannot reliably stop.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_stop_one_started_one_paused(mock_print):
    """Test find_session_to_operate_on for 'stop' with one STARTED and one PAUSED."""
    sessions = [SESSION_STARTED_1, SESSION_PAUSED_1, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "stop")
    assert result == SESSION_STARTED_1
    mock_print.assert_not_called() # Should not print errors 

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_pause_but_already_paused(mock_print):
    """Test find_session_to_operate_on for 'pause' when a task is already PAUSED."""
    sessions = [SESSION_PAUSED_1, SESSION_STOPPED_1]
    # Attempting to pause (which targets STARTED) but only a PAUSED one exists
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "pause")
    assert result is None
    mock_print.assert_any_call(f"Error: Task '{SESSION_PAUSED_1.task_name}' is already PAUSED. Cannot pause again.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_resume_but_already_started(mock_print):
    """Test find_session_to_operate_on for 'resume' when a task is already STARTED."""
    sessions = [SESSION_STARTED_1, SESSION_STOPPED_1]
    # Attempting to resume (which targets PAUSED) but only a STARTED one exists
    result = find_session_to_operate_on(sessions, TaskSessionStatus.PAUSED, "resume")
    assert result is None
    mock_print.assert_any_call(f"Error: Task '{SESSION_STARTED_1.task_name}' is already RUNNING. No task to resume.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_resume_no_task_to_resume(mock_print):
    """Test find_session_to_operate_on for 'resume' when no PAUSED task exists (and no STARTED either)."""
    sessions = [SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.PAUSED, "resume")
    assert result is None
    mock_print.assert_any_call("Error: No task is currently PAUSED to resume.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_pause_no_running_task(mock_print):
    """Test find_session_to_operate_on for 'pause' when no task is RUNNING (and none PAUSED)."""
    sessions = [SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "pause")
    assert result is None
    mock_print.assert_any_call("Error: No task is currently RUNNING to pause.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_generic_no_candidate_found(mock_print):
    """Test find_session_to_operate_on for a generic action when no task has the target status."""
    sessions = [SESSION_STARTED_1]
    # Example: trying to perform an action that requires a STOPPED task, but none exist with that status.
    # Let's imagine a hypothetical "archive" action targeting STOPPED tasks.
    target_status_for_test = TaskSessionStatus.STOPPED 
    action_verb_for_test = "archive"
    result = find_session_to_operate_on(sessions, target_status_for_test, action_verb_for_test)
    assert result is None
    mock_print.assert_any_call(f"Error: No task with status {target_status_for_test.value} to {action_verb_for_test}.")

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_generic_multiple_candidates(mock_print):
    """Test find_session_to_operate_on for a generic action with multiple matching tasks."""
    # Create two stopped sessions for this test
    stopped_task_A = TaskSession(task_name="DoneA", start_time=NOW - timedelta(days=2), status=TaskSessionStatus.STOPPED)
    stopped_task_B = TaskSession(task_name="DoneB", start_time=NOW - timedelta(days=3), status=TaskSessionStatus.STOPPED)
    sessions = [stopped_task_A, stopped_task_B, SESSION_STARTED_1]
    
    target_status_for_test = TaskSessionStatus.STOPPED
    action_verb_for_test = "review"
    result = find_session_to_operate_on(sessions, target_status_for_test, action_verb_for_test)
    assert result is None
    mock_print.assert_any_call(f"Error: Multiple tasks found with status {target_status_for_test.value}. Cannot reliably {action_verb_for_test}.")

# Final check on simple cases
@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_simple_pause_success(mock_print):
    sessions = [SESSION_STARTED_1, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "pause")
    assert result == SESSION_STARTED_1
    mock_print.assert_not_called()

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_simple_resume_success(mock_print):
    sessions = [SESSION_PAUSED_1, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.PAUSED, "resume")
    assert result == SESSION_PAUSED_1
    mock_print.assert_not_called()

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_simple_stop_started_success(mock_print):
    sessions = [SESSION_STARTED_1, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.STARTED, "stop") # Target status for stop is flexible
    assert result == SESSION_STARTED_1
    mock_print.assert_not_called()

@pytest.mark.skipif(find_session_to_operate_on is None or TaskSession is None, reason="Dependencies not available")
@mock.patch("builtins.print")
def test_fsto_simple_stop_paused_success(mock_print):
    sessions = [SESSION_PAUSED_1, SESSION_STOPPED_1]
    result = find_session_to_operate_on(sessions, TaskSessionStatus.PAUSED, "stop") # Target status for stop is flexible
    assert result == SESSION_PAUSED_1
    mock_print.assert_not_called() 