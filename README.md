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

(To be added: instructions on how to install, run, and use the tool.)

## Development

(To be added: instructions on how to set up the development environment, run tests, and contribute.)

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

(To be added: specific linting commands)

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
