import sys
from src.cli.start_command import StartCommand
from src.cli.pause_command import PauseCommand
from src.cli.resume_command import ResumeCommand
from src.cli.stop_command import StopCommand
from src.cli.status_command import StatusCommand
from src.cli.summary_command import SummaryCommand

COMMANDS = {
    "start": StartCommand,
    "pause": PauseCommand,
    "resume": ResumeCommand,
    "stop": StopCommand,
    "status": StatusCommand,
    "summary": SummaryCommand,
}


def print_usage():
    """Prints usage instructions."""
    print("Usage: task-timer <command> [args...]")
    print("Available commands: " + ", ".join(COMMANDS.keys()))


def main():
    """Main entry point for the CLI application."""
    args = sys.argv[1:]

    if not args:
        print_usage()
        return

    command_name = args[0]
    command_args = args[1:]

    command_class = COMMANDS.get(command_name)

    if command_class:
        command_instance = command_class()
        command_instance.execute(command_args)
    else:
        print(f"Error: Unknown command '{command_name}'")
        print_usage()
        # Consider sys.exit(1) for errors in a real CLI


if __name__ == "__main__":
    main()
