# PRD: Task Timer CLI Tool

## 1. Overview

A command-line tool that allows users to track time spent on tasks. The tool supports starting, pausing, resuming, and stopping task timers and can generate daily or weekly summaries. Data is stored locally in JSON format.

This enables solo developers, freelancers, or makers to log focused work sessions and export time reports without depending on SaaS tools or cloud storage.

## 2. Problem Statement

Users need a lightweight, offline-compatible time tracking utility that doesn’t require GUI, internet, or account signup. Existing solutions are bloated or subscription-based. Developers want something they can version with their projects and invoke from a terminal.

## 3. User Stories

- As a developer, I want to **start a timer** with a task name so I can log what I’m working on.
- As a developer, I want to **pause or resume a timer** so I can handle interruptions.
- As a developer, I want to **stop a timer and record the time** to a local file.
- As a developer, I want to **see a daily summary** of time spent per task.
- As a developer, I want to **export time data** to JSON or CSV for analysis.

## 4. Features (MVP)

- `timer start [task_name]` – Starts a new timer
- `timer pause` – Pauses the current timer
- `timer resume` – Resumes the paused timer
- `timer stop` – Stops and records the task session
- `timer status` – Shows current timer status
- `timer summary --today` – Prints today’s task time totals
- `timer summary --week` – Prints this week’s task time totals
- `timer summary --month` – Prints this month’s task time totals
- `timer summary --year` – Prints this year’s task time totals
- Data persistence in `~/.task_timer/records.json`

## 5. Out of Scope (MVP)

- Multi-user support
- Time editing or retroactive entries
- Cloud sync or GUI
- Monthly reporting (stretch)

## 6. Constraints

- Must run on Python 3.9+
- Must not depend on external services
- CLI must be cross-platform (Unix and Windows)
- All time data must be stored in a structured local file format (JSON)

## 7. Success Metrics

- CLI commands work consistently and return meaningful output
- Time records persist across sessions
- Summary reports match the sum of recorded times
- Unit tests cover:
  - Timer lifecycle
  - File I/O persistence
  - Summary generation

## 8. Risks

- File corruption during write
- System clock manipulation (edge case)
- Overlapping timers or misuse (handled via CLI constraints)

## 9. Alternatives Considered

- Building a GUI (rejected: scope bloat)
- Using SQLite instead of JSON (post-MVP)
- Using shell aliases or Bash scripts (too fragile for test coverage)

