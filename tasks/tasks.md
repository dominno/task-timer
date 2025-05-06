## ARCH-001: Establish Project Architecture and Module Boundaries
Status: In Progress
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: All (CLI, Domain, Infra)  
Dependencies: None

### 🔧 Implementation Plan
- [x] Create project folder structure as per architecture.mermaid
- [x] Scaffold empty modules: cli, domain, infra/storage
- [x] Add placeholder files for each module/component
- [x] Document module boundaries and responsibilities
- [x] Add README with architecture diagram reference
- [x] Status/log updates

### ✅ Acceptance Criteria
1. Folder structure matches architecture.mermaid
2. All modules have placeholder files
3. Boundaries and responsibilities are documented
4. No implementation logic yet

### 🧐 Edge Cases
- Directory creation errors
- File permission issues

---

## ARCH-002: Define Storage Abstraction Layer (Strategy Pattern)
Status: Planned
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: infra/storage  
Dependencies: ARCH-001

### 🔧 Implementation Plan
- [ ] Define StorageProvider ABC in infra/storage/base.py
- [ ] Document required interface methods
- [ ] Add placeholder for JSON and SQLite implementations
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. StorageProvider ABC exists with all required methods
2. JSON/SQLite storage classes stubbed
3. No persistence logic yet

### 🧐 Edge Cases
- Method signature mismatches
- Future backend extensibility

---

## ARCH-003: Domain Model — TaskSession Entity & Lifecycle
Status: Planned  
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: domain  
Dependencies: ARCH-001

### 🔧 Implementation Plan
- [ ] Define TaskSession model in domain/session.py
- [ ] Add status Enum (STARTED, PAUSED, STOPPED)
- [ ] Implement lifecycle methods: pause, resume, stop (no logic yet)
- [ ] Document model fields and transitions
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. TaskSession model and Enum defined
2. Lifecycle methods stubbed
3. Model docstring covers all fields and transitions

### 🧐 Edge Cases
- Enum extensibility
- Invalid state transitions

---

## ARCH-004: CLI Command Routing Skeleton
Status: Planned  
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: cli  
Dependencies: ARCH-001

### 🔧 Implementation Plan
- [ ] Create main.py entry point
- [ ] Define Command ABC in cli/command_base.py
- [ ] Scaffold command files: start, pause, resume, stop, status, summary
- [ ] Implement command dispatcher skeleton
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. CLI entry point and dispatcher exist
2. Command skeletons for all MVP commands
3. No business logic yet

### 🧐 Edge Cases
- Command name collisions
- CLI arg parsing errors

---

## FEAT-001: Implement JSON Storage Provider
Status: Planned  
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: infra/storage  
Dependencies: ARCH-002

### 🔧 Implementation Plan
- [ ] Implement JsonStorage class with save/load/clear
- [ ] Handle file I/O and error cases
- [ ] Write unit tests (happy path, file corruption, permission error)
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. JsonStorage passes all tests
2. Handles file errors gracefully
3. 90%+ test coverage

### 🧐 Edge Cases
- Corrupted JSON file
- Disk full or permission denied

---

## FEAT-002: Implement TaskSession Lifecycle Logic
Status: Planned  
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: domain  
Dependencies: ARCH-003

### 🔧 Implementation Plan
- [ ] Implement pause, resume, stop logic in TaskSession
- [ ] Enforce valid state transitions
- [ ] Write unit tests (happy path, invalid transitions, clock abuse)
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. TaskSession lifecycle logic passes all tests
2. Invalid transitions raise errors
3. 100% test coverage

### 🧐 Edge Cases
- System clock manipulation
- Overlapping sessions

---

## FEAT-003: Implement CLI Command Logic (Start, Pause, Resume, Stop, Status)
Status: Planned
Priority: High  
PRD Reference: @{docs/PRD.md}  
Architectural Module: cli  
Dependencies: ARCH-004, FEAT-001, FEAT-002

### 🔧 Implementation Plan
- [ ] Implement each command to interact with domain and storage
- [ ] Validate CLI args and error handling
- [ ] Write unit tests (happy path, invalid input, storage errors)
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. All CLI commands work as specified
2. Error cases handled gracefully
3. 100% test coverage

### 🧐 Edge Cases
- Invalid command usage
- Storage backend unavailable

---

## FEAT-004: Implement Summary Reporting (Today, Week, Month, Year)
Status: Planned
Priority: Medium  
PRD Reference: @{docs/PRD.md}  
Architectural Module: cli, domain  
Dependencies: FEAT-003

### 🔧 Implementation Plan
- [ ] Implement summary logic in domain
- [ ] Add CLI options for summary periods
- [ ] Write unit tests (happy path, empty data, time zone edge cases)
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. Summary reports match recorded times
2. Handles empty/no data cases
3. 100% test coverage

### 🧐 Edge Cases
- No sessions recorded
- Daylight saving time changes

---

## FEAT-005: Export Data to JSON/CSV
Status: Planned  
Priority: Medium  
PRD Reference: @{docs/PRD.md}  
Architectural Module: cli, infra/storage  
Dependencies: FEAT-004

### 🔧 Implementation Plan
- [ ] Implement export logic for JSON/CSV
- [ ] Add CLI command for export
- [ ] Write unit tests (happy path, file write errors)
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. Data export works for all formats
2. Handles file errors gracefully
3. 100% test coverage

### 🧐 Edge Cases
- Export file already exists
- Invalid export path

---

## TEST-001: Enforce Unit Testing and Coverage Standards
Status: Planned  
Priority: High  
PRD Reference: @{docs/unit_testing_guideline.md}  
Architectural Module: All  
Dependencies: All feature tasks

### 🔧 Implementation Plan
- [ ] Ensure all modules have 90%+ coverage
- [ ] Add coverage check to CI (if applicable)
- [ ] Review test structure, naming, and edge cases
- [ ] Status/log updates

### ✅ Acceptance Criteria
1. 90%+ coverage for all modules
2. All test guidelines followed
3. No happy-path-only suites

### 🧐 Edge Cases
- Missed edge cases
- Flaky or non-deterministic tests
