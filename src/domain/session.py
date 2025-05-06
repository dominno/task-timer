# Placeholder for TaskSession entity and logic

from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


class TaskSessionStatus(Enum):
    """Represents the status of a task session."""

    STARTED = "STARTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


@dataclass
class TaskSession:
    """Represents a single task tracking session.

    Attributes:
        task_name (str): The name or description of the task.
        start_time (datetime): The time when the session started.
        end_time (Optional[datetime]): The time when the session ended. None if
            ongoing or paused.
        status (TaskSessionStatus): The current status of the session (STARTED,
            PAUSED, STOPPED).
        duration (timedelta): Calculated duration. If not STOPPED, behavior may be
            refined. If not ended, defaults to timedelta(0) unless overridden.
        _duration_override (Optional[timedelta]): Allows explicitly setting duration,
            bypassing calculation. Useful for importing data.

    State Transitions (managed by lifecycle methods - to be implemented):
        - A new session starts in STARTED status.
        - STARTED -> PAUSED (via pause())
        - PAUSED -> STARTED (via resume())
        - STARTED or PAUSED -> STOPPED (via stop())
        - STOPPED is a terminal state for a session instance for time accumulation.
    """

    task_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskSessionStatus = TaskSessionStatus.STARTED
    # Using field for default_factory to ensure new timedelta for each instance
    _duration_override: Optional[timedelta] = field(
        default=None, repr=False
    )  # For specific cases like data import

    @property
    def duration(self) -> timedelta:
        if self._duration_override is not None:
            return self._duration_override
        if self.end_time:
            return self.end_time - self.start_time
        # If not stopped/paused, duration is from start_time to now.
        # Behavior might be refined later for PAUSED state.
        # For now, if active, duration might be ongoing or zero until stopped.
        # Assume duration is mainly for completed/explicit periods.
        # Or, if ongoing, calculate to now. PRD implies duration for completed.
        # Simple model: if not ended, duration is zero unless overridden.
        # Consider if active session should show running duration.
        # Match test_task_session_creation_defaults (expects 0 if not ended).
        return timedelta(0)

    # Placeholder for lifecycle methods to be implemented next
    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def stop(self) -> None:
        pass
