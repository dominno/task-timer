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
        end_time (Optional[datetime]): The overall end time when the session was
                                     stopped. None if ongoing or paused.
        status (TaskSessionStatus): The current status of the session (STARTED,
                                  PAUSED, STOPPED).
        _accumulated_duration (timedelta): Internal: Stores duration from
                                         completed segments.
        _current_segment_start_time (Optional[datetime]): Internal: Time current
                                                       active segment started, or None.
        _pause_times: list[datetime] = field(default_factory=list, init=False)
        _resume_times: list[datetime] = field(default_factory=list, init=False)
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

    # Internal fields for accurate duration calculation across pauses/resumes
    _accumulated_duration: timedelta = field(init=False, default_factory=timedelta)
    # Stores total duration of completed segments (when paused/stopped).

    _current_segment_start_time: Optional[datetime] = field(init=False)
    # If task is STARTED, marks beginning of current active segment.

    # To reconstruct segments for reporting or detailed logs
    _pause_times: list[datetime] = field(init=False, default_factory=list)
    _resume_times: list[datetime] = field(default_factory=list, init=False)

    def __post_init__(self):
        if not isinstance(self.start_time, datetime):
            raise TypeError("start_time must be a datetime object")

        # Normalize start_time to UTC
        if self.start_time.tzinfo is None:  # If naive, assume UTC
            self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        elif self.start_time.tzinfo != timezone.utc:  # If aware but not UTC, convert
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
            self._current_segment_start_time = self.start_time  # Now guaranteed UTC
        elif self.status == TaskSessionStatus.STOPPED and self.end_time is not None:
            if self.start_time > self.end_time:
                raise ValueError("end_time cannot be before start_time")
            self._accumulated_duration = self.end_time - self.start_time
            self._current_segment_start_time = None
        elif self.status == TaskSessionStatus.PAUSED:
            self._current_segment_start_time = None

    @property
    def duration(self) -> timedelta:
        """Calculates the total active duration of the task session."""
        # Assumes if STARTED, `now` is current time.
        # For PAUSED/STOPPED, duration is fixed.
        # Accumulation happens in pause() and stop() methods.
        now = datetime.now(timezone.utc)
        current_duration = self._accumulated_duration
        if (
            self.status == TaskSessionStatus.STARTED
            and self._current_segment_start_time
        ):
            current_duration += now - self._current_segment_start_time
        return current_duration

    def pause(self) -> None:
        """Pauses an active (STARTED) session."""
        if self.status == TaskSessionStatus.PAUSED:
            raise InvalidStateTransitionError(
                "Cannot pause a session that is already PAUSED."
            )
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError(
                "Cannot pause a session that is already STOPPED."
            )

        if (
            self.status == TaskSessionStatus.STARTED
            and self._current_segment_start_time
        ):
            now = datetime.now(timezone.utc)
            # _current_segment_start_time is now guaranteed to be UTC
            self._accumulated_duration += now - self._current_segment_start_time

        self._pause_times.append(now)  # Record pause time
        self.status = TaskSessionStatus.PAUSED
        self._current_segment_start_time = None

    def resume(self) -> None:
        """Resumes a PAUSED session."""
        if self.status == TaskSessionStatus.STARTED:
            raise InvalidStateTransitionError(
                "Cannot resume a session that is already STARTED."
            )
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError(
                "Cannot resume a session that is already STOPPED."
            )

        now = datetime.now(timezone.utc)
        self._resume_times.append(now)  # Record resume time
        self.status = TaskSessionStatus.STARTED
        self._current_segment_start_time = now  # This is UTC

    def stop(self) -> None:
        """Stops an active (STARTED) or PAUSED session."""
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError(
                "Cannot stop a session that is already STOPPED."
            )

        now = datetime.now(timezone.utc)

        if (
            self.status == TaskSessionStatus.STARTED
            and self._current_segment_start_time
        ):
            # _current_segment_start_time is now guaranteed to be UTC
            self._accumulated_duration += now - self._current_segment_start_time

        self.end_time = now  # This is UTC
        self.status = TaskSessionStatus.STOPPED
        self._current_segment_start_time = None

    def get_active_segments(self) -> list[tuple[datetime, datetime]]:
        """Reconstructs and returns a list of [start, end] tuples for active segments."""
        segments: list[tuple[datetime, datetime]] = []
        if not self.start_time:
            return segments  # Should not happen for a valid session

        current_segment_start = self.start_time
        num_pauses = len(self._pause_times)
        num_resumes = len(self._resume_times)

        # Iterate through recorded pauses
        for i in range(num_pauses):
            pause_time = self._pause_times[i]
            if (
                current_segment_start < pause_time
            ):  # Ensure segment has positive duration
                segments.append((current_segment_start, pause_time))

            if i < num_resumes:
                current_segment_start = self._resume_times[i]
            else:
                # Paused and not resumed further, so no more segments from here
                current_segment_start = None
                break

        # Handle the last segment if the session is not PAUSED or was never paused
        if (
            current_segment_start
        ):  # This means it's either running or was stopped while running
            if self.status == TaskSessionStatus.STARTED:
                # Currently running: segment is from last resume (or start_time) to now
                # Use a consistent "now" for this calculation if called multiple times rapidly
                # but for segment definition, datetime.now is fine.
                segments.append((current_segment_start, datetime.now(timezone.utc)))
            elif self.status == TaskSessionStatus.STOPPED and self.end_time:
                # Stopped: segment is from last resume (or start_time) to end_time
                if current_segment_start < self.end_time:
                    segments.append((current_segment_start, self.end_time))
            # If PAUSED, the last segment was already added up to the last pause_time,
            # and current_segment_start would be None.

        return segments
