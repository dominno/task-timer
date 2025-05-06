from typing import List, Any  # Add typing
from .base import StorageProvider

# from ...domain.session import TaskSession # Adjust path as needed


class SQLiteStorage(StorageProvider):
    """Placeholder for SQLite-based storage provider."""

    def save_task_session(
        self, session: Any
    ) -> None:  # TODO: Replace Any with TaskSession
        # print(f"Placeholder: Saving session {session} to SQLite")
        pass

    def get_all_sessions(self) -> List[Any]:  # TODO: Replace Any with TaskSession
        # print("Placeholder: Getting all sessions from SQLite")
        return []

    def clear(self) -> None:
        # print("Placeholder: Clearing SQLite storage")
        pass
