from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.domain.session import TaskSession, TaskSessionStatus
from typing import list
from .cli_utils import format_timedelta_for_cli


class StatusCommand(Command):
    def execute(self, args: list[str]):
        storage = JsonStorage()
        active_sessions: list[TaskSession] = []

        try:
            all_sessions = storage.get_all_sessions()
            for session in all_sessions:
                if (
                    session.status == TaskSessionStatus.STARTED
                    or session.status == TaskSessionStatus.PAUSED
                ):
                    active_sessions.append(session)

            if not active_sessions:
                print("No active task.")
                return

            if len(active_sessions) > 1:
                # This indicates a state that ideally StartCommand prevents.
                # Prioritize showing STARTED if multiple found, otherwise the first PAUSED.
                # Or, more strictly, report an error for manual resolution.
                print("Error: Multiple active sessions found. Resolve manually.")
                # Optionally, could list them out here.
                # For now, simple error is fine as per test.
                return

            # If exactly one active session
            session_to_report = active_sessions[0]
            formatted_start_time = session_to_report.start_time.strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
            current_duration_str = format_timedelta_for_cli(session_to_report.duration)

            if session_to_report.status == TaskSessionStatus.STARTED:
                print(f"Task '{session_to_report.task_name}' is RUNNING.")
                print(f"  Started at: {formatted_start_time}")
                print(f"  Current duration: {current_duration_str}.")
            elif session_to_report.status == TaskSessionStatus.PAUSED:
                print(f"Task '{session_to_report.task_name}' is PAUSED.")
                print(f"  Started at: {formatted_start_time}")
                print(f"  Accumulated duration: {current_duration_str}.")

        except Exception as e_storage:
            print(f"Error accessing storage: {e_storage}")
