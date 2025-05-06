from abc import ABC, abstractmethod
from typing import (
    List,
    Any,
)  # Changed from list to List for older Pythons if needed, Any for session type

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
    def save_task_session(
        self, session: Any
    ) -> None:  # TODO: Replace Any with TaskSession once defined
        """Saves a single task session.

        Args:
            session: The TaskSession object to save.
        """
        pass

    @abstractmethod
    def get_all_sessions(
        self,
    ) -> List[Any]:  # TODO: Replace Any with TaskSession once defined
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
