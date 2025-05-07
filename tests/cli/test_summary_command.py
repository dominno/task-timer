from unittest import mock
from datetime import timedelta

# Import the command and dependent components
from src.cli.summary_command import SummaryCommand
from src.domain.session import TaskSession
from src.domain.summary import DATETIME_RANGE_HELPERS


def create_mock_session(task_name_value: str):
    session = mock.MagicMock(spec=TaskSession)
    session.task_name = task_name_value
    return session


class TestSummaryCommand:
    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("src.cli.summary_command.generate_summary_report")
    @mock.patch("builtins.print")
    def test_execute_no_args_defaults_to_today_success(
        self, mock_print, mock_generate_report, mock_json_storage_cls
    ):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.return_value = [
            create_mock_session("SESSION_A")
        ]

        mock_report_data = {"TASK-1": timedelta(hours=1, minutes=30)}
        mock_generate_report.return_value = mock_report_data

        command = SummaryCommand()

        # Act
        command.execute([])

        # Assert
        mock_json_storage_cls.assert_called_once()
        mock_storage_instance.get_all_sessions.assert_called_once()
        mock_generate_report.assert_called_once_with(
            mock_storage_instance.get_all_sessions.return_value, "today"
        )

        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]

        assert "Generating summary for period: today..." in print_calls
        assert "\n--- Summary for Today ---" in print_calls
        assert "- Task: TASK-1: 1h 30m 0s" in print_calls
        assert "--- End of Summary ---" in print_calls

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("src.cli.summary_command.generate_summary_report")
    @mock.patch("builtins.print")
    def test_execute_with_valid_period_arg(
        self, mock_print, mock_generate_report, mock_json_storage_cls
    ):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.return_value = [
            create_mock_session("SESSION_B")
        ]

        mock_report_data = {"TASK-WEEK": timedelta(minutes=45, seconds=10)}
        mock_generate_report.return_value = mock_report_data

        command = SummaryCommand()
        period_arg = "this_week"

        # Act
        command.execute([period_arg])

        # Assert
        mock_generate_report.assert_called_once_with(
            mock_storage_instance.get_all_sessions.return_value, period_arg
        )
        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert f"Generating summary for period: {period_arg}..." in print_calls
        assert "\n--- Summary for This Week ---" in print_calls
        assert "- Task: TASK-WEEK: 45m 10s" in print_calls

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("builtins.print")
    def test_execute_with_invalid_period_arg(self, mock_print, mock_json_storage_cls):
        # Arrange
        command = SummaryCommand()
        invalid_period_arg = "invalid_period"
        supported_periods = list(DATETIME_RANGE_HELPERS().keys())

        # Act
        command.execute([invalid_period_arg])

        # Assert
        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert (
            f"Error: Invalid period name '{invalid_period_arg}'." in print_calls
        )
        assert (
            f"Supported periods are: {', '.join(supported_periods)}."
            in print_calls
        )
        assert (
            f"Usage: task-timer summary [{'/'.join(supported_periods)}]"
            in print_calls
        )

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("src.cli.summary_command.generate_summary_report")
    @mock.patch("builtins.print")
    def test_execute_no_sessions_in_storage(
        self, mock_print, mock_generate_report, mock_json_storage_cls
    ):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.return_value = []  # No sessions

        command = SummaryCommand()

        # Act
        command.execute([])  # Default to 'today'

        # Assert
        mock_storage_instance.get_all_sessions.assert_called_once()
        mock_generate_report.assert_not_called()  # Report generation should be skipped

        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert "Generating summary for period: today..." in print_calls
        assert "No task sessions found in storage." in print_calls

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("src.cli.summary_command.generate_summary_report")
    @mock.patch("builtins.print")
    def test_execute_empty_report_for_period(
        self, mock_print, mock_generate_report, mock_json_storage_cls
    ):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.return_value = [
            create_mock_session("SESSION_C")
        ]

        mock_generate_report.return_value = {}  # Empty report

        command = SummaryCommand()
        period_arg = "this_month"

        # Act
        command.execute([period_arg])

        # Assert
        mock_generate_report.assert_called_once_with(
            mock_storage_instance.get_all_sessions.return_value, period_arg
        )
        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert f"Generating summary for period: {period_arg}..." in print_calls
        assert f"No tasks found for the period '{period_arg}'." in print_calls

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("builtins.print")
    def test_execute_storage_file_not_found(self, mock_print, mock_json_storage_cls):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.side_effect = FileNotFoundError(
            "Storage file not found"
        )

        command = SummaryCommand()

        # Act
        command.execute([])  # Default to 'today'

        # Assert
        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert (
            "Generating summary for period: today..." in print_calls
        )
        assert (
            "No tasks have been recorded yet (storage file not found)."
            in print_calls
        )

    @mock.patch("src.cli.summary_command.JsonStorage")
    @mock.patch("src.cli.summary_command.generate_summary_report")
    @mock.patch("builtins.print")
    def test_execute_generic_exception_during_report(
        self, mock_print, mock_generate_report, mock_json_storage_cls
    ):
        # Arrange
        mock_storage_instance = mock_json_storage_cls.return_value
        mock_storage_instance.get_all_sessions.return_value = [
            create_mock_session("SESSION_D")
        ]

        error_message = "Something went wrong during report generation"
        mock_generate_report.side_effect = Exception(error_message)

        command = SummaryCommand()

        # Act
        command.execute([])  # Default to 'today'

        # Assert
        print_calls = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert "Generating summary for period: today..." in print_calls
        assert (
            f"An error occurred while generating the summary: {error_message}"
            in print_calls
        )
