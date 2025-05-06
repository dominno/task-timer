# Task Timer CLI Tool

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
