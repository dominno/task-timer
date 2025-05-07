from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.domain.session import TaskSession, TaskSessionStatus
from datetime import datetime, timezone  # Import timezone directly


class StartCommand(Command):
    def execute(self, args: list[str]):
        if not args or not args[0]:
            print("Error: Task name is required.")
            print("Usage: task-timer start <task_name>")
            return

        task_name = args[0]
        storage = JsonStorage()  # This is what the mock targets

        # Check for existing active sessions
        active_session_found = False
        try:
            all_sessions = storage.get_all_sessions()
            for session in all_sessions:
                if session.status == TaskSessionStatus.STARTED:
                    print(
                        f"Error: Task '{session.task_name}' is STARTED. Stop it first."
                    )
                    active_session_found = True
                    break
                elif session.status == TaskSessionStatus.PAUSED:
                    error_msg = (
                        f"Error: Task '{session.task_name}' is PAUSED. "
                        f"Resume and stop, or stop it."
                    )
                    print(error_msg)
                    active_session_found = True
                    break
        except Exception as e:
            print(f"Error accessing storage: {e}")
            return

        if active_session_found:
            return

        # Create and save the new session
        try:
            # Ensure start_time is timezone-aware UTC, matching TaskSession
            # internal handling
            start_time = datetime.now(timezone.utc)
            new_session = TaskSession(task_name=task_name, start_time=start_time)
            storage.save_task_session(new_session)
            # strftime %Z might be unreliable.
            # A more robust way if start_time is guaranteed UTC:
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"Task '{task_name}' started at {start_time_str}.")
        except Exception as e:
            print(f"Error starting task: {e}")
