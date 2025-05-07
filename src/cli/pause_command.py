from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.cli.cli_utils import find_session_to_operate_on
from src.domain.session import TaskSessionStatus, InvalidStateTransitionError
# from src.domain.session import TaskSession # Unused
# from typing import Optional # Unused


class PauseCommand(Command):
    def execute(self, args: list[str]):
        storage = JsonStorage()
        try:
            all_sessions = storage.get_all_sessions()
            session_to_pause = find_session_to_operate_on(
                all_sessions, TaskSessionStatus.STARTED, "pause"
            )

            if session_to_pause:
                try:
                    session_to_pause.pause()
                    storage.save_task_session(session_to_pause)
                    print(f"Task '{session_to_pause.task_name}' paused.")
                except InvalidStateTransitionError as e_domain:
                    print(f"Error pausing task '{session_to_pause.task_name}':")
                    print(str(e_domain))
                except Exception as e_save:
                    print(f"Error saving paused task '{session_to_pause.task_name}':")
                    print(str(e_save))

        except Exception as e_storage:
            print(f"Error accessing storage: {e_storage}")
