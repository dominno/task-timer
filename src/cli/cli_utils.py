from typing import Optional, List
from src.domain.session import TaskSession, TaskSessionStatus
from datetime import timedelta # Moved import to top level

def find_session_to_operate_on(
    all_sessions: List[TaskSession],
    target_status: TaskSessionStatus,
    action_verb: str # e.g., "pause", "resume", "stop"
) -> Optional[TaskSession]:
    """Finds a unique session with the target_status.
    
    Prints errors and returns None if:
    - No session with target_status is found.
    - Multiple sessions with target_status are found.
    - For stopping: if no STARTED or PAUSED session is found.
    """
    candidate_sessions = [s for s in all_sessions if s.status == target_status]

    if action_verb == "stop": # Stop can target STARTED or PAUSED
        stoppable_sessions = [
            s for s in all_sessions if s.status in [TaskSessionStatus.STARTED, TaskSessionStatus.PAUSED]
        ]
        if not stoppable_sessions:
            print(f"Error: No active task to {action_verb}.")
            return None
        if len(stoppable_sessions) > 1:
            # Prioritize STARTED if multiple, otherwise this is an ambiguous state
            started_ones = [s for s in stoppable_sessions if s.status == TaskSessionStatus.STARTED]
            if len(started_ones) == 1:
                return started_ones[0]
            elif len(started_ones) > 1:
                print(f"Error: Multiple RUNNING tasks found. Cannot reliably {action_verb}.")
                return None
            else: # Multiple PAUSED, or a mix that doesn't include a single STARTED
                print(f"Error: Multiple active (PAUSED) tasks found. Cannot reliably {action_verb}.")
                return None
        return stoppable_sessions[0] # Exactly one stoppable (STARTED or PAUSED)

    # For actions other than stop (pause, resume)
    if not candidate_sessions:
        if target_status == TaskSessionStatus.STARTED:
            # Check if a PAUSED one exists to give a more specific message for 'pause' action
            paused_sessions = [s for s in all_sessions if s.status == TaskSessionStatus.PAUSED]
            if paused_sessions:
                print(f"Error: Task '{paused_sessions[0].task_name}' is already PAUSED. Cannot {action_verb} again.")
            else:
                print(f"Error: No task is currently RUNNING to {action_verb}.")
        elif target_status == TaskSessionStatus.PAUSED:
             # Check if a STARTED one exists to give a more specific message for 'resume' action
            started_sessions = [s for s in all_sessions if s.status == TaskSessionStatus.STARTED]
            if started_sessions:
                print(f"Error: Task '{started_sessions[0].task_name}' is already RUNNING. No task to {action_verb}.")
            else:
                print(f"Error: No task is currently PAUSED to {action_verb}.")
        else:
            print(f"Error: No task with status {target_status.value} to {action_verb}.")
        return None
    
    if len(candidate_sessions) > 1:
        print(f"Error: Multiple tasks found with status {target_status.value}. Cannot reliably {action_verb}.")
        # TODO: Future enhancement - list tasks and allow selection.
        return None
        
    return candidate_sessions[0]


def format_timedelta_for_cli(td: timedelta) -> str:
    """Helper to format timedelta to HH:MM:SS string for CLI output."""
    # This was in stop_command.py, moving it here for general use.
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}" 