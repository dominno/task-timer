from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.domain.session import (
    TaskSession,
    TaskSessionStatus,
    InvalidStateTransitionError,
)
# from datetime import datetime, timezone # REMOVED as likely unused now
from typing import Optional
from .cli_utils import find_session_to_operate_on, format_timedelta_for_cli


class StopCommand(Command):
    def execute(self, args: list[str]):
        storage = JsonStorage()
        try:
            all_sessions = storage.get_all_sessions()
            session_to_stop = find_session_to_operate_on(all_sessions, TaskSessionStatus.STARTED, "stop")
            
            if session_to_stop:
                try:
                    session_to_stop.stop()
                    stopped_duration = session_to_stop.duration
                    storage.save_task_session(session_to_stop)
                    duration_str = format_timedelta_for_cli(stopped_duration)
                    print(f"Task '{session_to_stop.task_name}' stopped.")
                    print(f"  Total duration: {duration_str}.")
                except InvalidStateTransitionError as e_domain:
                    print(f"Error stopping task '{session_to_stop.task_name}':")
                    print(str(e_domain))
                except Exception as e_save:
                    print(f"Error saving stopped task '{session_to_stop.task_name}':")
                    print(str(e_save))
            # If find_session_to_operate_on returned None, it already printed an error.

        except Exception as e_storage:
            print(f"Error accessing storage: {e_storage}")
