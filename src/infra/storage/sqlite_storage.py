from .base import StorageProvider
# from ...domain.session import TaskSession # Adjust path as needed

class SQLiteStorage(StorageProvider):
    def save_task_session(self, session) -> None: # Use 'session: TaskSession' once defined
        print(f"Placeholder: Saving session {session} to SQLite")
        pass

    def get_all_sessions(self) -> list: # Use '-> list[TaskSession]' once defined
        print("Placeholder: Getting all sessions from SQLite")
        return []

    def clear(self) -> None:
        print("Placeholder: Clearing SQLite storage")
        pass 