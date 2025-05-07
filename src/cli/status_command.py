from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.domain.session import TaskSession, TaskSessionStatus
from .cli_utils import format_timedelta_for_cli
from datetime import datetime, timezone
from typing import Optional


class StatusCommand(Command):
    def execute(self, args: list[str]):
        storage = JsonStorage()
        active_session: Optional[TaskSession] = None
        other_sessions: list[TaskSession] = []

        try:
            all_sessions = storage.get_all_sessions()
            all_sessions.sort(key=lambda s: s.start_time, reverse=True)

            for session in all_sessions:
                if not active_session and (
                    session.status == TaskSessionStatus.STARTED
                    or session.status == TaskSessionStatus.PAUSED
                ):
                    active_session = session
                else:
                    other_sessions.append(session)
            
            now = datetime.now(timezone.utc)

            if active_session:
                formatted_start_time = active_session.start_time.strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                )
                
                current_total_duration = active_session.get_duration_at(now)
                current_duration_str = format_timedelta_for_cli(current_total_duration)

                print(f"Active task: {active_session.task_name} (Started: {formatted_start_time}) - Current total duration: {current_duration_str}")

            else:
                print("No active task.")

            if other_sessions:
                print("\nOther recent tasks (not active):")
                for session in other_sessions:
                    formatted_start = session.start_time.strftime("%Y-%m-%d %H:%M:%S %Z") if session.start_time else "N/A"
                    formatted_end = session.end_time.strftime("%Y-%m-%d %H:%M:%S %Z") if session.end_time else "N/A"
                    duration_str = format_timedelta_for_cli(session.duration)

                    print(f"Task: {session.task_name}, Status: {session.status.value}, Start: {formatted_start}, End: {formatted_end}, Duration: {duration_str}")

        except Exception as e_storage:
            print(f"Error accessing storage: {e_storage}")
