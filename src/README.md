# Source Code (src)

This directory contains the core source code for the Task Timer CLI application.

## Module Boundaries and Responsibilities

The application is divided into three main layers, each with distinct responsibilities:

1.  **`cli` (Command Line Interface Layer)**
    *   **Responsibility:** Handles user interaction, command parsing, and displaying output.
    *   **Components:**
        *   `main.py`: Main entry point for the CLI.
        *   `command_base.py`: Defines the abstract base class for all commands.
        *   `*_command.py`: Concrete implementations for each CLI command (e.g., `start`, `stop`, `status`).
    *   **Interactions:** Interacts with the `Domain Layer` to execute business logic and with the `Infrastructure Layer` (specifically storage) to persist and retrieve data. It should not contain any business logic itself.

2.  **`domain` (Domain Layer)**
    *   **Responsibility:** Contains the core business logic, entities, and rules of the application. This layer is independent of any specific UI or persistence mechanism.
    *   **Components:**
        *   `models.py`: (Potentially for shared simple data structures or enums if not co-located with their primary entity).
        *   `session.py`: Defines the `TaskSession` entity, its states (e.g., STARTED, PAUSED, STOPPED), and its lifecycle methods (pause, resume, stop).
    *   **Interactions:** Does not depend on the `CLI` or `Infrastructure` layers. It exposes an API for the `CLI` layer to use.

3.  **`infra` (Infrastructure Layer)**
    *   **Responsibility:** Handles external concerns like data storage, external API integrations (if any), etc.
    *   **Submodules:**
        *   **`storage`**:
            *   `base.py`: Defines the `StorageProvider` abstract base class (interface) for storage operations.
            *   `json_storage.py`: Concrete implementation for storing data in JSON files.
            *   `sqlite_storage.py`: (Placeholder) Concrete implementation for storing data in an SQLite database.
    *   **Interactions:** Provides concrete implementations of interfaces defined (or expected by) the `Domain` or `CLI` layers. For example, the `StorageProvider` implementations are used by CLI commands to save and load `TaskSession` data.

## Guiding Principles

*   **Separation of Concerns:** Each layer has a single, well-defined responsibility.
*   **Dependency Rule:** Dependencies flow inwards: `CLI` -> `Domain` <- `Infra`. The `Domain` layer should have no knowledge of the `CLI` or specific `Infra` implementations.
*   **Abstraction:** Interfaces (like `StorageProvider`) are used to decouple layers.

For a visual representation, refer to `docs/architecture.mermaid`. 