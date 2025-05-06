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
  - `start_time: datetime`
  - `end_time: datetime | None`
  - `duration: timedelta`
  - `status: Enum(STARTED, PAUSED, STOPPED)`

Business logic should **only operate on this model**. No timestamps, file paths, or CLI args should be passed into domain logic directly. All mutation is done through clearly named methods:

```python
session.pause()
session.resume()
session.stop()
```

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



