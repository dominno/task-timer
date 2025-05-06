# Placeholder for TaskSession entity and logic

from enum import Enum
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional


class TaskSessionStatus(Enum):
    """Represents the status of a task session."""

    STARTED = "STARTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


class InvalidStateTransitionError(Exception):
    """Raised when a lifecycle method is called on a session in an invalid state."""

    pass


@dataclass
class TaskSession:
    """Represents a single task tracking session.

    Attributes:
        task_name (str): The name or description of the task.
        start_time (datetime): The overall start time when the session was created.
        end_time (Optional[datetime]): The overall end time when the session was stopped.
                                     None if ongoing or paused.
        status (TaskSessionStatus): The current status of the session (STARTED,
                                  PAUSED, STOPPED).
        _accumulated_duration (timedelta): Internal: Stores duration from completed segments.
        _current_segment_start_time (Optional[datetime]): Internal: Time current active
                                                       segment started, or None.
        duration (timedelta): Calculated total active duration of the session.

    State Transitions (managed by lifecycle methods):
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
    _accumulated_duration: timedelta = field(default_factory=timedelta, init=False)
    _current_segment_start_time: Optional[datetime] = field(init=False, default=None)

    def __post_init__(self):
        if not isinstance(self.start_time, datetime):
            raise TypeError("start_time must be a datetime object")
        
        # Normalize start_time to UTC
        if self.start_time.tzinfo is None: # If naive, assume UTC
            self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        elif self.start_time.tzinfo != timezone.utc: # If aware but not UTC, convert
            self.start_time = self.start_time.astimezone(timezone.utc)
        
        if self.end_time is not None:
            if not isinstance(self.end_time, datetime):
                raise TypeError("end_time must be a datetime object or None")
            # Normalize end_time to UTC
            if self.end_time.tzinfo is None:
                self.end_time = self.end_time.replace(tzinfo=timezone.utc)
            elif self.end_time.tzinfo != timezone.utc:
                self.end_time = self.end_time.astimezone(timezone.utc)

        if self.status == TaskSessionStatus.STARTED:
            self._current_segment_start_time = self.start_time # Now guaranteed UTC
        elif self.status == TaskSessionStatus.STOPPED and self.end_time is not None:
            if self.start_time > self.end_time:
                 raise ValueError("end_time cannot be before start_time")
            self._accumulated_duration = self.end_time - self.start_time
            self._current_segment_start_time = None
        elif self.status == TaskSessionStatus.PAUSED:
            self._current_segment_start_time = None

    @property
    def duration(self) -> timedelta:
        current_segment_duration = timedelta(0)
        if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
            now = datetime.now(timezone.utc)
            # _current_segment_start_time is now guaranteed to be UTC
            current_segment_duration = now - self._current_segment_start_time
        return self._accumulated_duration + current_segment_duration

    def pause(self) -> None:
        """Pauses an active (STARTED) session."""
        if self.status == TaskSessionStatus.PAUSED:
            raise InvalidStateTransitionError("Cannot pause a session that is already PAUSED.")
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError("Cannot pause a session that is already STOPPED.")
        
        if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
            now = datetime.now(timezone.utc)
            # _current_segment_start_time is now guaranteed to be UTC
            self._accumulated_duration += (now - self._current_segment_start_time)
        
        self.status = TaskSessionStatus.PAUSED
        self._current_segment_start_time = None

    def resume(self) -> None:
        """Resumes a PAUSED session."""
        if self.status == TaskSessionStatus.STARTED:
            raise InvalidStateTransitionError("Cannot resume a session that is already STARTED.")
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError("Cannot resume a session that is already STOPPED.")
        
        self.status = TaskSessionStatus.STARTED
        self._current_segment_start_time = datetime.now(timezone.utc) # This is UTC

    def stop(self) -> None:
        """Stops an active (STARTED) or PAUSED session."""
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError("Cannot stop a session that is already STOPPED.")

        now = datetime.now(timezone.utc)

        if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
            # _current_segment_start_time is now guaranteed to be UTC
            self._accumulated_duration += (now - self._current_segment_start_time)
        
        self.end_time = now # This is UTC
        self.status = TaskSessionStatus.STOPPED
        self._current_segment_start_time = None
