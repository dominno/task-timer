from abc import ABC, abstractmethod
# Forward declaration if TaskSession is in a different module and causes circular import
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from ...domain.session import TaskSession # Adjust path as needed

class StorageProvider(ABC):
    @abstractmethod
    def save_task_session(self, session) -> None: # Use 'session: TaskSession' once defined
        pass

    @abstractmethod
    def get_all_sessions(self) -> list: # Use '-> list[TaskSession]' once defined
        pass

    @abstractmethod
    def clear(self) -> None:
        pass 