# Placeholder for TaskSession entity and logic

from enum import Enum
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class TaskSessionStatus(Enum):
    """Represents the status of a task session."""

    STARTED = "STARTED"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    # UNKNOWN = "UNKNOWN" # Consider if needed for error states


class InvalidStateTransitionError(Exception):
    """Raised when a lifecycle method is called on a session in an invalid state."""

    pass


@dataclass
class TaskSession:
    """Represents a single task tracking session.

    Attributes:
        task_name (str): The name or description of the task.
        start_time (dt.datetime): The overall start time when the session was created.
        end_time (Optional[dt.datetime]): The overall end time when the session was
                                     stopped. None if ongoing or paused.
        status (TaskSessionStatus): The current status of the session (STARTED,
                                  PAUSED, STOPPED).
        _accumulated_duration (dt.timedelta): Internal: Stores duration from
                                         completed segments.
        _current_segment_start_time (Optional[dt.datetime]): Internal: Time current
                                                       active segment started, or None.
        _pause_times: list[dt.datetime] = field(default_factory=list, init=False)
        _resume_times: list[dt.datetime] = field(default_factory=list, init=False)
        # duration (dt.timedelta): Calculated total active duration of the session. Removed to use property

    State Transitions (managed by lifecycle methods):
        - A new session starts in STARTED status.
        - STARTED -> PAUSED (via pause())
        - PAUSED -> STARTED (via resume())
        - STARTED or PAUSED -> STOPPED (via stop())
        - STOPPED is a terminal state for a session instance for time accumulation.
    """

    task_name: str
    start_time: datetime # Ensure this is timezone-aware, preferably UTC
    end_time: Optional[datetime] = None # Also timezone-aware if set
    status: TaskSessionStatus = TaskSessionStatus.STARTED

    # Internal fields for accurate duration calculation across pauses/resumes
    _accumulated_duration: timedelta = field(
        init=False, default_factory=timedelta
    )
    # Stores total duration of completed segments (when paused/stopped).

    _current_segment_start_time: Optional[datetime] = field(init=False)
    # If task is STARTED, marks beginning of current active segment.
    # This should also be timezone-aware UTC.

    # To reconstruct segments for reporting or detailed logs
    _pause_times: list[datetime] = field(init=False, default_factory=list)
    _resume_times: list[datetime] = field(default_factory=list, init=False)

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
            # This logic is primarily for initialization from stored data
            # where duration might not have been pre-calculated or stored.
            if self.start_time > self.end_time: # Basic validation
                raise ValueError("end_time cannot be before start_time")
            # If _accumulated_duration is not already set (e.g. loaded from simple JSON)
            # And we are initializing a STOPPED session with start/end times
            if self._accumulated_duration == timedelta(0): # Check if it's at default
                 self._accumulated_duration = self.end_time - self.start_time
            self._current_segment_start_time = None
        elif self.status == TaskSessionStatus.PAUSED:
            self._current_segment_start_time = None
        # If _accumulated_duration has a value (e.g. from a more complete JSON load),
        # it will retain that value due to field(init=False) unless explicitly set.

    @property
    def duration(self) -> timedelta:
        # This is the effective total duration up to 'now' if running/paused,
        # or final duration if stopped.
        return self.get_duration_at(datetime.now(timezone.utc))

    def get_duration_at(self, calculation_time: datetime) -> timedelta:
        """Calculates the total active duration of the task session up to a specific point in time."""
        # Ensure calculation_time is timezone-aware UTC for comparison
        if calculation_time.tzinfo is None:
            calculation_time = calculation_time.replace(tzinfo=timezone.utc)
        elif calculation_time.tzinfo != timezone.utc:
             calculation_time = calculation_time.astimezone(timezone.utc)

        if self.status == TaskSessionStatus.STOPPED:
            return self._accumulated_duration
        elif self.status == TaskSessionStatus.PAUSED:
            return self._accumulated_duration
        elif self.status == TaskSessionStatus.STARTED:
            if self._current_segment_start_time:
                # Ensure _current_segment_start_time is timezone-aware UTC
                current_segment_start_time_utc = self._current_segment_start_time
                if current_segment_start_time_utc.tzinfo is None: # Should not happen if set correctly
                    current_segment_start_time_utc = current_segment_start_time_utc.replace(tzinfo=timezone.utc)
                
                current_segment_duration = calculation_time - current_segment_start_time_utc
                return self._accumulated_duration + current_segment_duration
            else:
                # This case should ideally not happen for a STARTED session
                # if _current_segment_start_time is None, it implies it hasn't truly started a segment
                return self._accumulated_duration
        return timedelta(0) # Default for UNKNOWN or other states

    def pause(self) -> None:
        """Pauses an active (STARTED) session."""
        if self.status == TaskSessionStatus.PAUSED:
            # Allow re-pausing a paused task? No, treat as no-op or error.
            # For now, raise error for clarity.
            raise InvalidStateTransitionError(
                "Cannot pause a session that is already PAUSED."
            )
        if self.status == TaskSessionStatus.STOPPED:
            raise InvalidStateTransitionError(
                "Cannot pause a session that is already STOPPED."
            )

        # If it's STARTED, calculate duration of current segment and add to accumulated
        now = datetime.now(timezone.utc) # Use a single 'now' for this operation
        if (
            self.status == TaskSessionStatus.STARTED
            and self._current_segment_start_time
        ):
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
        # If PAUSED, transition to STARTED and mark new segment start time
        now = datetime.now(timezone.utc)
        self._resume_times.append(now)  # Record resume time
        self.status = TaskSessionStatus.STARTED
        self._current_segment_start_time = now  # This is UTC

    def stop(self) -> None:
        """Stops an active (STARTED) or PAUSED session."""
        if self.status == TaskSessionStatus.STOPPED:
            # Allow re-stopping a stopped task? No, treat as no-op or error.
            # For now, raise error.
            raise InvalidStateTransitionError(
                "Cannot stop a session that is already STOPPED."
            )

        now = datetime.now(timezone.utc) # Use a single 'now'

        # If it was STARTED, calculate duration of final segment
        if (
            self.status == TaskSessionStatus.STARTED
            and self._current_segment_start_time
        ):
            # _current_segment_start_time is now guaranteed to be UTC
            self._accumulated_duration += now - self._current_segment_start_time
        # If it was PAUSED, _accumulated_duration is already up-to-date.

        self.end_time = now  # This is UTC
        self.status = TaskSessionStatus.STOPPED
        self._current_segment_start_time = None

    def get_active_segments(self) -> list[tuple[datetime, datetime]]:
        """Reconstructs and returns a list of [start, end] tuples for active segments.
        Useful for detailed reporting or visualization.
        Segments are defined by start/end times or pause/resume events.
        For a currently running session, the last segment's end time is 'now'.
        """
        segments: list[tuple[datetime, datetime]] = []
        if not self.start_time: # Should not happen for a valid session
            return segments

        current_segment_start = self.start_time
        num_pauses = len(self._pause_times)
        num_resumes = len(self._resume_times)

        # Iterate through recorded pauses
        for i in range(num_pauses):
            pause_time = self._pause_times[i]
            if current_segment_start < pause_time: # Ensure segment has positive duration
                segments.append((current_segment_start, pause_time))
            
            if i < num_resumes:
                current_segment_start = self._resume_times[i]
            else:
                # Paused and not resumed further, so no more segments from here
                current_segment_start = None # type: ignore
                break
        
        # Handle the last segment if the session is not PAUSED or was never paused
        if current_segment_start: # This means it's either running or was stopped while running
            if self.status == TaskSessionStatus.STARTED:
                # Currently running: segment is from last resume (or start_time) to now
                # Use a consistent "now" for this calculation if called multiple times rapidly
                # but for segment definition, datetime.now is fine.
                now_for_segment = datetime.now(timezone.utc)
                segments.append((current_segment_start, now_for_segment))
            elif self.status == TaskSessionStatus.STOPPED and self.end_time:
                # Stopped: segment is from last resume (or start_time) to end_time
                if current_segment_start < self.end_time:
                     segments.append((current_segment_start, self.end_time))
            # If PAUSED, the last segment was already added up to the last pause_time,
            # and current_segment_start would be None.

        return segments