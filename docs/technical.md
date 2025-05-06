# Technical Design Guidelines — Task Timer CLI Tool

## Overview

This document outlines the core engineering principles, module boundaries, and design patterns used in the Task Timer CLI Tool. The goal is to enable testable, extensible, and maintainable features from day one — especially around time tracking logic and storage persistence.

---

## 1. Storage Abstraction (Primary Focus)

### Problem
The system must support multiple storage backends (initially JSON, later SQLite/MySQL) without leaking persistence logic into the domain or CLI layers.

### Solution: Strategy Pattern for Storage

All read/write operations will be abstracted behind a clean interface:

```python
# src/infra/storage/base.py
class StorageProvider(ABC):
    @abstractmethod
    def save_task_session(self, session: TaskSession): ...
    
    @abstractmethod
    def get_all_sessions(self) -> list[TaskSession]: ...
    
    @abstractmethod
    def clear(self): ...
```

Then, plug in implementations like:

```python
# src/infra/storage/json_storage.py
class JsonStorage(StorageProvider):
    def save_task_session(...) -> None:
        ...

# src/infra/storage/sqlite_storage.py
class SQLiteStorage(StorageProvider):
    def save_task_session(...) -> None:
        ...
```

The concrete implementation will be injected at runtime using a factory method or configuration layer (e.g., based on env var or CLI arg).

> ✅ DRY: No duplication of persistence logic across domains  
> ✅ SOLID: Open/Closed principle via interface  
> ✅ KISS: Simple interface, pure logic, no magic

---

## 2. Domain Model

- Core domain entity: `TaskSession`
  - `task_name: str`
  - `start_time: datetime` (Overall start of the session)
  - `end_time: Optional[datetime]` (Overall end of the session, set when stopped)
  - `status: Enum(STARTED, PAUSED, STOPPED)`
  - `_accumulated_duration: timedelta` (Internal: Stores duration from completed segments before a pause)
  - `_current_segment_start_time: Optional[datetime]` (Internal: Time current active segment started, or None if paused/stopped)
  - `duration: timedelta` (Calculated property, see lifecycle logic)

Business logic should **only operate on this model**. No timestamps, file paths, or CLI args should be passed into domain logic directly. All mutation is done through clearly named methods:

```python
# Example of how TaskSession might be structured internally
# (actual implementation in src/domain/session.py)

# from datetime import datetime, timedelta
# from enum import Enum
# from dataclasses import dataclass, field

# class TaskSessionStatus(Enum):
#     STARTED = "STARTED"
#     PAUSED = "PAUSED"
#     STOPPED = "STOPPED"

# @dataclass
# class TaskSession:
#     task_name: str
#     start_time: datetime
#     end_time: Optional[datetime] = None
#     status: TaskSessionStatus = TaskSessionStatus.STARTED
#     _accumulated_duration: timedelta = field(default_factory=timedelta)
#     _current_segment_start_time: Optional[datetime] = field(init=False, default=None)

#     def __post_init__(self):
#         if self.status == TaskSessionStatus.STARTED:
#             self._current_segment_start_time = self.start_time

#     @property
#     def duration(self) -> timedelta:
#         current_segment_duration = timedelta(0)
#         if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
#             current_segment_duration = datetime.now() - self._current_segment_start_time # Or use timezone.now()
#         return self._accumulated_duration + current_segment_duration

#     def pause(self) -> None:
#         if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
#             self._accumulated_duration += (datetime.now() - self._current_segment_start_time)
#         self.status = TaskSessionStatus.PAUSED
#         self._current_segment_start_time = None

#     def resume(self) -> None:
#         if self.status == TaskSessionStatus.PAUSED:
#             self.status = TaskSessionStatus.STARTED
#             self._current_segment_start_time = datetime.now()

#     def stop(self) -> None:
#         if self.status == TaskSessionStatus.STARTED and self._current_segment_start_time:
#             self._accumulated_duration += (datetime.now() - self._current_segment_start_time)
#         self.end_time = datetime.now()
#         self.status = TaskSessionStatus.STOPPED
#         self._current_segment_start_time = None

# Example usage:
session.pause()
session.resume()
session.stop()
```

**Lifecycle and Duration Calculation for `TaskSession`:**
-   A new `TaskSession` is initialized with `status = STARTED`, `_accumulated_duration = timedelta(0)`, and `_current_segment_start_time = start_time`.
-   **`pause()` method:**
    -   If `status` is `STARTED`: Calculates the duration of the current active segment (e.g., `datetime.now() - _current_segment_start_time`) and adds it to `_accumulated_duration`.
    -   Sets `status` to `PAUSED`.
    -   Sets `_current_segment_start_time` to `None`.
    -   Throws an error if already `PAUSED` or `STOPPED`.
-   **`resume()` method:**
    -   If `status` is `PAUSED`: Sets `status` to `STARTED`.
    -   Sets `_current_segment_start_time` to `datetime.now()`.
    -   Throws an error if already `STARTED` or `STOPPED`.
-   **`stop()` method:**
    -   If `status` is `STARTED`: Calculates the duration of the current active segment and adds it to `_accumulated_duration`.
    -   Sets `end_time` to `datetime.now()`.
    -   Sets `status` to `STOPPED`.
    -   Sets `_current_segment_start_time` to `None`.
    -   Throws an error if already `STOPPED`.
-   **`duration` property (read-only):**
    -   If `status` is `STARTED` and `_current_segment_start_time` is set: Returns `_accumulated_duration + (datetime.now() - _current_segment_start_time)`. This provides a live duration.
    -   If `status` is `PAUSED`: Returns `_accumulated_duration`.
    -   If `status` is `STOPPED`: Returns `_accumulated_duration` (which at this point represents the total active time).
    -   Note: For time calculations, consistently use timezone-aware `datetime` objects, preferably UTC for internal storage and calculations, converting to local time only for display. The `freezegun` library will be essential for testing time-dependent logic.

> ✅ SOLID: SRP is enforced  
> ✅ DRY: Shared lifecycle logic resides in domain, not CLI or storage  
> ✅ KISS: No external dependencies in core logic

---

## 3. CLI Command Routing

All CLI commands (`start`, `pause`, `resume`, etc.) are routed through a single entry point (`main.py`) using a command dispatcher pattern.

```python
COMMANDS = {
    "start": StartCommand,
    "pause": PauseCommand,
    ...
}
```

Each command implements:

```python
class Command(ABC):
    def execute(self, args: list[str]) -> None: ...
```

> ✅ Open/Closed: add new commands by extending  
> ✅ KISS: each command has one responsibility  
> ✅ Testable: commands can be unit tested in isolation

---

## 4. Testing Standards

- **Unit tests** for:
  - Domain lifecycle transitions (start → pause → resume → stop)
  - Storage provider save/load behavior
  - CLI command parsing and routing

- **Mocking strategy:**
  - Use in-memory mocks for storage
  - Time-freezing for deterministic `datetime.now()` behavior (via `freezegun`)

- **Coverage requirements:**
  - 90%+ test coverage required for all domain and storage modules
  - No happy-path-only tests. Must include:
    - Invalid commands
    - Corrupted files
    - System clock abuse

---

## 5. Folder Structure

```
src/
  cli/
    start_command.py
    pause_command.py
    ...
  domain/
    models.py
    session.py
  infra/
    storage/
      base.py
      json_storage.py
      sqlite_storage.py
main.py
```

> ✅ Clear separation of CLI / domain / infra  
> ✅ Storage logic never touches domain directly  
> ✅ Modules map to architectural boundaries

---

## 6. Design Patterns in Use

| Pattern        | Use Case                                     |
|----------------|----------------------------------------------|
| Strategy       | Switchable storage backends                  |
| Command        | CLI command execution                        |
| Factory        | Instantiate appropriate storage provider     |
| Enum           | Session state control                        |
| Adapter (later)| Wrap DB results to fit `TaskSession` model   |

---

## 7. Principles Summary

| Principle | Enforcement |
|----------|-------------|
| SOLID    | Domain and CLI layers follow SRP and OCP strictly |
| DRY      | No duplication between CLI and domain logic       |
| KISS     | Prefer clarity and separation over premature reuse|
| YAGNI    | Only JSON backend implemented in MVP              |



