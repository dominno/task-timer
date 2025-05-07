import argparse
from .command_base import Command
from src.infra.storage.json_storage import JsonStorage  # Assuming JsonStorage for now
from src.infra.storage.base import StorageWriteError


class ExportCommand(Command):
    def execute(self, args: list[str]):
        parser = argparse.ArgumentParser(
            prog="task-timer export", description="Export task sessions to JSON or CSV."
        )
        parser.add_argument(
            "format",
            choices=["json", "csv"],
            help="The format to export to (json or csv).",
        )
        parser.add_argument(
            "output_path", help="The file path to save the exported data."
        )

        try:
            parsed_args = parser.parse_args(args)
        except (
            SystemExit
        ):  # argparse exits on error, catch to prevent stopping the main app if used interactively  # noqa: E501
            return

        storage = JsonStorage()

        try:
            if parsed_args.format == "json":
                storage.export_to_json(parsed_args.output_path)
                success_message = (
                    f"Successfully exported data in JSON format to: "
                    f"{parsed_args.output_path}"
                )
                print(success_message)
            elif parsed_args.format == "csv":
                storage.export_to_csv(parsed_args.output_path)
                success_message = (
                    f"Successfully exported data in CSV format to: "
                    f"{parsed_args.output_path}"
                )
                print(success_message)
        except StorageWriteError as e:
            print(f"Error during export: {e}")
        except Exception as e_general:
            print(f"An unexpected error occurred: {e_general}")
