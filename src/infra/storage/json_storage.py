from typing import List
from .base import StorageProvider
from src.domain.session import TaskSession  # Import TaskSession

# from ...domain.session import TaskSession # Adjust path as needed


class JsonStorage(StorageProvider):
    """Placeholder for JSON-based storage provider."""

    def save_task_session(
        self, session: TaskSession
    ) -> None:  # TODO: Replace Any with TaskSession
        # print(f"Placeholder: Saving session {session} to JSON")
        pass

    def get_all_sessions(
        self,
    ) -> List[TaskSession]:  # TODO: Replace Any with TaskSession
        # print("Placeholder: Getting all sessions from JSON")
        return []

    def clear(self) -> None:
        # print("Placeholder: Clearing JSON storage")
        pass
