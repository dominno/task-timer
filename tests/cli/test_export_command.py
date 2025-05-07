import pytest
import os
from unittest import mock

# Attempt to import commands and domain models
try:
    from src.cli.export_command import ExportCommand
    from src.infra.storage.json_storage import JsonStorage  # For mocking
    from src.infra.storage.base import StorageWriteError
except ImportError:
    ExportCommand = None
    JsonStorage = None
    StorageWriteError = None

EXPORT_TEST_DIR = "test_cli_exports"


@pytest.fixture(autouse=True)
def manage_export_test_dir():
    """Create and clean up a directory for export test files."""
    if not os.path.exists(EXPORT_TEST_DIR):
        os.makedirs(EXPORT_TEST_DIR)
    yield
    # Teardown: Remove all files in EXPORT_TEST_DIR after tests in this module run
    # for f_name in os.listdir(EXPORT_TEST_DIR):
    #     os.remove(os.path.join(EXPORT_TEST_DIR, f_name))
    # os.rmdir(EXPORT_TEST_DIR) # Might fail if test creates subdirs/fails mid-creation
    # A more robust cleanup might be needed if tests are complex, for now, this is a start
    # For simplicity, manual cleanup or git clean might be easier initially than robust pytest teardown here.


@pytest.mark.skipif(
    ExportCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@mock.patch("builtins.print")
@mock.patch(  # noqa: E501
    "src.cli.export_command.JsonStorage"  # noqa: E501
    # Mock the storage instance used by the command
)
def test_export_command_json_successful(mock_json_storage_class, mock_print):
    """Test ExportCommand for JSON successfully calls storage.export_to_json."""
    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_json_storage_class.return_value = mock_storage_instance

    target_file_path = os.path.join(EXPORT_TEST_DIR, "test_out.json")

    command = ExportCommand()
    command.execute(["json", target_file_path])

    mock_storage_instance.export_to_json.assert_called_once_with(target_file_path)
    mock_print.assert_any_call(
        f"Successfully exported data in JSON format to: {target_file_path}"
    )


@pytest.mark.skipif(
    ExportCommand is None or JsonStorage is None, reason="Dependencies not met"
)
@mock.patch("builtins.print")
@mock.patch(  # noqa: E501
    "src.cli.export_command.JsonStorage"  # noqa: E501
    # Mock the storage instance used by the command
)
def test_export_command_csv_successful(mock_json_storage_class, mock_print):
    """Test ExportCommand for CSV successfully calls storage.export_to_csv."""
    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_json_storage_class.return_value = mock_storage_instance

    target_file_path = os.path.join(EXPORT_TEST_DIR, "test_out.csv")

    command = ExportCommand()
    command.execute(["csv", target_file_path])

    mock_storage_instance.export_to_csv.assert_called_once_with(target_file_path)
    mock_print.assert_any_call(
        f"Successfully exported data in CSV format to: {target_file_path}"
    )


@pytest.mark.skipif(
    ExportCommand is None or JsonStorage is None or StorageWriteError is None,
    reason="Dependencies not met",
)
@mock.patch("builtins.print")
@mock.patch(  # noqa: E501
    "src.cli.export_command.JsonStorage"  # noqa: E501
    # Mock the storage instance used by the command
)
def test_export_command_storage_write_error(mock_json_storage_class, mock_print):
    """Test ExportCommand handles StorageWriteError during export."""
    mock_storage_instance = mock.MagicMock(spec=JsonStorage)
    mock_storage_instance.export_to_json.side_effect = StorageWriteError("Disk full")
    mock_json_storage_class.return_value = mock_storage_instance

    target_file_path = os.path.join(EXPORT_TEST_DIR, "error_test.json")

    command = ExportCommand()
    command.execute(["json", target_file_path])

    mock_storage_instance.export_to_json.assert_called_once_with(target_file_path)
    mock_print.assert_any_call("Error during export: Disk full")


# TODO: Add tests for:
# - Missing arguments (format, output_path)
# - Invalid format argument
# - StorageWriteError during export
# - Other unexpected errors
