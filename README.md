# Task Timer CLI Tool

A simple CLI tool to track time spent on tasks.

## Project Structure

-   `docs/`: Contains all project documentation.
    -   `PRD.md`: Product Requirement Document.
    -   `technical.md`: Technical design guidelines and patterns.
    -   `architecture.mermaid`: Mermaid diagram of the system architecture. View this to understand module boundaries and data flow.
    -   `unit_testing_guideline.md`: Guidelines for writing unit tests.
    -   `status.md`: Current project status and progress.
    -   `log.md`: Activity log.
-   `src/`: Contains the application source code. See `src/README.md` for details on module responsibilities.
    -   `cli/`: Command Line Interface layer.
    -   `domain/`: Core business logic and entities.
    -   `infra/`: Infrastructure concerns (e.g., storage).
    -   `main.py`: CLI entry point.
-   `tasks/`: Contains task definitions and implementation plans.
    -   `tasks.md`: Detailed breakdown of tasks.
-   `tests/`: Contains all unit and integration tests.

## Getting Started

### Prerequisites

- Python 3.9 or higher.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone <repository-url>
    cd task-timer
    ```
2.  **Running the tool:**
    The tool can be run directly using the Python module execution:
    ```sh
    python -m src.main <command> [args...]
    ```
    For example:
    ```sh
    python -m src.main start "My new task"
    python -m src.main status
    ```
    (Alternatively, a setup script could be created to install it as a system command, but that is not yet implemented.)

### Basic Usage

-   **Start a new task:**
    ```sh
    python -m src.main start "Task description here"
    ```
-   **Check current task status:**
    ```sh
    python -m src.main status
    ```
-   **Pause the current task:**
    ```sh
    python -m src.main pause
    ```
-   **Resume a paused task:**
    ```sh
    python -m src.main resume
    ```
-   **Stop the current task:**
    ```sh
    python -m src.main stop
    ```
-   **View task summary:**
    ```sh
    python -m src.main summary [today|this_week|this_month|this_year]
    ```
    (Defaults to 'today' if no period is specified)

-   **Export task data:**
    ```sh
    python -m src.main export <format> <output_path>
    ```
    -   `<format>`: `json` or `csv`
    -   `<output_path>`: File path to save the export (e.g., `my_tasks.json` or `my_tasks.csv`)
    Example:
    ```sh
    python -m src.main export json ./tasks_export.json
    python -m src.main export csv ./tasks_export.csv
    ```

## Development

### Setup

1.  Follow the installation steps above to clone the repository.
2.  It is recommended to use a virtual environment:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  Install development dependencies (testing tools). While not yet in a `requirements-dev.txt`, you will need:
    ```sh
    pip install pytest pytest-cov freezegun flake8 black
    ```

### Running Tests

Make sure `pytest` and `pytest-cov` are installed.

To run tests:
```sh
PYTHONPATH=src pytest tests/
```

To run tests with coverage report:
```sh
PYTHONPATH=src pytest --cov=src tests/
```

### Linting

Code should be formatted with `black` and linted with `flake8`.

-   **Format code with Black:**
    ```sh
    black src/ tests/
    ```
-   **Lint code with Flake8:**
    (Ensure your `PYTHONPATH` is set to include the `src` directory if running from the project root, or if your IDE doesn't handle it automatically for imports.)
    ```sh
    PYTHONPATH=src flake8 --max-line-length=88 src/ tests/
    ```
    Alternatively, configure `max-line-length = 88` in a `.flake8` configuration file (see TECH-DEBT-001).

## Architecture Overview

This project follows a strict modular architecture, as illustrated in the architecture diagram below:

![Architecture Diagram](docs/architecture.mermaid)

### Module Structure
- **CLI Layer (`src/cli/`)**: Handles command parsing, user interaction, and dispatches commands to the domain and storage layers. No business or persistence logic.
- **Domain Layer (`src/domain/`)**: Contains core business logic and entities (e.g., `TaskSession`). No direct dependencies on CLI or storage implementation.
- **Infrastructure Layer (`src/infra/storage/`)**: Provides pluggable storage backends (e.g., JSON, SQLite) via a clean interface. No business or CLI logic.

For more details, see:
- [docs/architecture.mermaid](docs/architecture.mermaid)
- [docs/technical.md](docs/technical.md)
