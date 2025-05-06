from .command_base import Command

class StopCommand(Command):
    def execute(self, args: list[str]) -> None:
        print("Placeholder for StopCommand")
        pass 