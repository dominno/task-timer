from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.cli.cli_utils import find_paused_session
from src.domain.session import TaskSessionStatus, InvalidStateTransitionError


class ResumeCommand(Command):
    def execute(self, args: list[str]):
        storage = JsonStorage()
        try:
            all_sessions = storage.get_all_sessions()
            session_to_resume = find_paused_session(
                all_sessions, "resume"
            )

            if session_to_resume:
                currently_started_session = None
                for s in all_sessions:
                    if s.status == TaskSessionStatus.STARTED:
                        currently_started_session = s
                        break

                if currently_started_session:
                    print(
                        f"Error: Task '{currently_started_session.task_name}' is already RUNNING."
                    )
                    print(f"Cannot resume '{session_to_resume.task_name}'.")
                    return

                try:
                    session_to_resume.resume()
                    storage.save_task_session(session_to_resume)
                    print(f"Task '{session_to_resume.task_name}' resumed.")
                except InvalidStateTransitionError as e_domain:
                    print(f"Error resuming '{session_to_resume.task_name}':")
                    print(str(e_domain))
                except Exception as e_save:
                    print(f"Error saving '{session_to_resume.task_name}' after resume:")
                    print(str(e_save))
        except Exception as e_storage:
            print(f"Error accessing storage: {e_storage}")
