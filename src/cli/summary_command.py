from .command_base import Command
from src.infra.storage.json_storage import JsonStorage
from src.domain.summary import generate_summary_report


class SummaryCommand(Command):
    def execute(self, args: list[str]) -> None:
        storage = JsonStorage()
        supported_periods = ["today", "week", "month", "year"]
        period_name = "today"  # Default period

        if args:
            if args[0] in supported_periods:
                period_name = args[0]
            else:
                print(f"Error: Invalid period name '{args[0]}'.")
                print(f"Supported periods are: {', '.join(supported_periods)}.")
                usage_msg = f"Usage: task-timer summary [{'/'.join(supported_periods)}]"
                print(usage_msg)
                return

        print(f"Generating summary for period: {period_name}...")

        try:
            all_sessions = storage.get_all_sessions()
            if not all_sessions:
                print("No task sessions found in storage.")
                return

            report = generate_summary_report(all_sessions, period_name)

            if not report:
                print(f"No tasks found for the period '{period_name}'.")
                return

            print(f"\n--- Summary for {period_name.replace('_', ' ').title()} ---")
            for task_name, duration in report.items():
                # Format timedelta to HH:MM:SS or similar
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                if hours > 0:
                    duration_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    duration_str = f"{minutes}m {seconds}s"
                else:
                    duration_str = f"{seconds}s"

                print(f"- Task: {task_name}: {duration_str}")
            print("--- End of Summary ---")

        except FileNotFoundError:
            print("No tasks have been recorded yet (storage file not found).")
        except Exception as e:
            print(f"An error occurred while generating the summary: {e}")
