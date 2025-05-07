from abc import ABC, abstractmethod
from typing import List

# Import TaskSession for type hinting
from src.domain.session import TaskSession  # Adjusted path assuming domain.session

# Forward declaration for type hinting TaskSession if it's in a different module
# to avoid circular imports. This is a common pattern.
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from ...domain.session import TaskSession # Adjust path as needed


class StorageProvider(ABC):
    """Abstract Base Class for a storage provider.

    This interface defines the contract for concrete storage implementations
    (e.g., JSON, SQLite) to interact with TaskSession data.
    """

    @abstractmethod
    def save_task_session(self, session: TaskSession) -> None:
        """Saves a single task session.

        Args:
            session: The TaskSession object to save.
        """
        pass

    @abstractmethod
    def get_all_sessions(self) -> List[TaskSession]:
        """Retrieves all task sessions.

        Returns:
            A list of all TaskSession objects.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clears all task sessions from the storage.

        This is typically used for testing or resetting the application state.
        """
        pass

    @abstractmethod
    def export_to_csv(self, target_path: str) -> None:
        """Exports all task sessions to a CSV file at the given path."""
        pass

    @abstractmethod
    def export_to_json(self, target_path: str) -> None:
        """Exports all task sessions to a JSON file at the given path."""
        pass


class StorageError(Exception):
    """Base class for storage-related errors."""

    pass


class StorageWriteError(StorageError):
    """Raised when an error occurs during a storage write operation."""

    pass
