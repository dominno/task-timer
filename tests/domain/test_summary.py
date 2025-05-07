import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
from unittest import mock

# Attempt to import domain models and summary functions
try:
    from src.domain.session import (
        TaskSession,
        TaskSessionStatus,
    )  # TaskSessionStatus might not be directly used here but good for context
    from src.domain.summary import (
        get_duration_within_period, 
        get_date_range_for_period, 
        generate_summary_report # Added import
    )
except ImportError:
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    get_duration_within_period = None  # type: ignore
    get_date_range_for_period = None  # type: ignore
    generate_summary_report = None # Added fallback

FROZEN_TIME_STR = "2024-03-15T12:00:00Z"  # Consistent frozen time for tests


def specific_utc_dt(year, month, day, hour=0, minute=0, second=0, microsecond=0):
    return datetime(
        year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc
    )


# Helper to create a TaskSession with mocked get_active_segments
def create_mocked_session_with_segments(segments: list[tuple[datetime, datetime]]):
    if TaskSession is None:
        # This check is more for local running; skipif in tests handles imports
        raise ImportError("TaskSession not available for mocking")
    session_mock = mock.MagicMock(spec=TaskSession)
    session_mock.get_active_segments.return_value = segments
    return session_mock


@pytest.mark.skipif(
    TaskSession is None or get_duration_within_period is None,
    reason="Dependencies for get_duration_within_period not met",
)
class TestGetDurationWithinPeriod:

    def test_session_fully_within_period(self):
        period_start = specific_utc_dt(2024, 3, 1, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 31, 23, 59, 59, 999999)

        seg_start = specific_utc_dt(2024, 3, 10, 10, 0, 0)
        seg_end = specific_utc_dt(2024, 3, 10, 11, 0, 0)  # 1 hour duration
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(hours=1)

    def test_session_fully_outside_before_period(self):
        period_start = specific_utc_dt(2024, 3, 1, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 31, 23, 59, 59, 999999)

        seg_start = specific_utc_dt(2024, 2, 25, 10, 0, 0)
        seg_end = specific_utc_dt(2024, 2, 25, 11, 0, 0)
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(0)

    def test_session_fully_outside_after_period(self):
        period_start = specific_utc_dt(2024, 3, 1, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 31, 23, 59, 59, 999999)

        seg_start = specific_utc_dt(2024, 4, 5, 10, 0, 0)
        seg_end = specific_utc_dt(2024, 4, 5, 11, 0, 0)
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(0)

    def test_session_starts_before_ends_within_period(self):
        period_start = specific_utc_dt(2024, 3, 10, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 23, 59, 59, 999999)

        seg_start = specific_utc_dt(2024, 3, 9, 23, 0, 0)  # Starts 1 hour before period
        seg_end = specific_utc_dt(2024, 3, 10, 1, 0, 0)  # Ends 1 hour into period
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(hours=1)  # Only the part within the period

    def test_session_starts_within_ends_after_period(self):
        period_start = specific_utc_dt(2024, 3, 10, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 1, 0, 0)  # Period is 1 hour long

        seg_start = specific_utc_dt(2024, 3, 10, 0, 30, 0)  # Starts 30 mins into period
        seg_end = specific_utc_dt(2024, 3, 10, 1, 30, 0)  # Ends 30 mins after period
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(minutes=30)  # Only the part within the period

    def test_session_starts_before_ends_after_period(self):  # Period inside session
        period_start = specific_utc_dt(2024, 3, 10, 10, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 11, 0, 0)  # Period is 1 hour long

        seg_start = specific_utc_dt(2024, 3, 10, 9, 0, 0)  # Session starts 1 hr before
        seg_end = specific_utc_dt(2024, 3, 10, 12, 0, 0)  # Session ends 1 hr after
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(hours=1)  # Duration is the full period length

    def test_session_with_multiple_segments_various_overlaps(self):
        period_start = specific_utc_dt(2024, 3, 15, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 15, 23, 59, 59, 999999)

        segments = [
            (
                specific_utc_dt(2024, 3, 14, 23, 0, 0),
                specific_utc_dt(2024, 3, 15, 1, 0, 0),
            ),  # 1 hr in period
            (
                specific_utc_dt(2024, 3, 15, 2, 0, 0),
                specific_utc_dt(2024, 3, 15, 3, 0, 0),
            ),  # 1 hr fully in period
            (
                specific_utc_dt(2024, 3, 15, 23, 30, 0),
                specific_utc_dt(2024, 3, 16, 0, 30, 0),
            ),  # 30 mins in period
            (
                specific_utc_dt(2024, 3, 16, 10, 0, 0),
                specific_utc_dt(2024, 3, 16, 11, 0, 0),
            ),  # 0 mins, fully outside
        ]
        session = create_mocked_session_with_segments(segments)

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(seconds=8999, microseconds=999999)

    def test_session_with_no_active_segments(self):
        period_start = specific_utc_dt(2024, 3, 1, 0, 0, 0)
        period_end = specific_utc_dt(2024, 3, 31, 23, 59, 59, 999999)
        session = create_mocked_session_with_segments([])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(0)

    def test_period_start_and_end_identical_no_overlap(self):
        period_start_end = specific_utc_dt(2024, 3, 15, 12, 0, 0)

        seg_start = specific_utc_dt(2024, 3, 15, 10, 0, 0)
        seg_end = specific_utc_dt(2024, 3, 15, 11, 0, 0)  # Ends before period point
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(
            session, period_start_end, period_start_end
        )
        assert duration == timedelta(0)

    def test_period_start_and_end_identical_segment_contains_point(self):
        period_start_end = specific_utc_dt(2024, 3, 15, 12, 0, 0)

        seg_start = specific_utc_dt(2024, 3, 15, 11, 0, 0)
        seg_end = specific_utc_dt(2024, 3, 15, 13, 0, 0)
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(
            session, period_start_end, period_start_end
        )
        assert duration == timedelta(0)

    def test_segment_ends_exactly_on_period_start(self):
        period_start = specific_utc_dt(2024, 3, 10, 12, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 13, 0, 0)

        seg_start = specific_utc_dt(2024, 3, 10, 11, 0, 0)
        seg_end = specific_utc_dt(2024, 3, 10, 12, 0, 0)
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(0)

    def test_segment_starts_exactly_on_period_end(self):
        period_start = specific_utc_dt(2024, 3, 10, 12, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 13, 0, 0)

        seg_start = specific_utc_dt(2024, 3, 10, 13, 0, 0)
        seg_end = specific_utc_dt(2024, 3, 10, 14, 0, 0)
        session = create_mocked_session_with_segments([(seg_start, seg_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(0)

    def test_segment_matches_period_exactly(self):
        period_start = specific_utc_dt(2024, 3, 10, 12, 0, 0)
        period_end = specific_utc_dt(2024, 3, 10, 13, 0, 0)

        session = create_mocked_session_with_segments([(period_start, period_end)])

        duration = get_duration_within_period(session, period_start, period_end)
        assert duration == timedelta(hours=1)


@pytest.mark.skipif(
    get_date_range_for_period is None, reason="get_date_range_for_period not available"
)
class TestGetDateRangeForPeriod:

    @freeze_time(FROZEN_TIME_STR)  # 2024-03-15T12:00:00Z
    def test_get_date_range_for_period_today(self):
        start, end = get_date_range_for_period("today")
        assert start == specific_utc_dt(2024, 3, 15, 0, 0, 0)
        assert end == specific_utc_dt(2024, 3, 15, 23, 59, 59, 999999)

    @freeze_time(FROZEN_TIME_STR)  # 2024-03-15 (Friday)
    def test_get_date_range_for_period_week(self):
        start, end = get_date_range_for_period("week")
        assert start == specific_utc_dt(2024, 3, 11, 0, 0, 0)  # Monday
        assert end == specific_utc_dt(2024, 3, 17, 23, 59, 59, 999999)  # Sunday

    @freeze_time(FROZEN_TIME_STR)  # 2024-03-15
    def test_get_date_range_for_period_month(self):
        start, end = get_date_range_for_period("month")
        assert start == specific_utc_dt(2024, 3, 1, 0, 0, 0)
        assert end == specific_utc_dt(
            2024, 3, 31, 23, 59, 59, 999999
        )  # March has 31 days

    @freeze_time(FROZEN_TIME_STR)  # 2024-03-15
    def test_get_date_range_for_period_year(self):
        start, end = get_date_range_for_period("year")
        assert start == specific_utc_dt(2024, 1, 1, 0, 0, 0)
        assert end == specific_utc_dt(
            2024, 12, 31, 23, 59, 59, 999999
        )  # 2024 is a leap year

    def test_get_date_range_for_period_invalid(self):
        with pytest.raises(
            ValueError, match="Invalid period specified: invalid_period"
        ):
            get_date_range_for_period("invalid_period")

    @freeze_time("2024-12-15T10:00:00Z") # Test for December month end
    def test_get_date_range_for_period_month_december(self):
        start, end = get_date_range_for_period("month")
        assert start == specific_utc_dt(2024, 12, 1, 0, 0, 0)
        assert end == specific_utc_dt(2024, 12, 31, 23, 59, 59, 999999)

# Placeholder for TestGenerateSummaryReport


# --- Tests for generate_summary_report ---

# Use real TaskSession objects now, as generate_summary_report calls get_duration_within_period
# which relies on the session's get_active_segments.

@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies for generate_summary_report not met",
)
@freeze_time(FROZEN_TIME_STR) # 2024-03-15T12:00:00Z
class TestGenerateSummaryReport:

    def test_generate_summary_empty_sessions(self):
        report = generate_summary_report([], "today")
        assert report == {}

    def test_generate_summary_invalid_period(self):
        session = TaskSession(
            task_name="Any Task",
            start_time=specific_utc_dt(2024, 3, 15, 10), # Within FROZEN_TIME_STR day
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 15, 11)
        )
        with pytest.raises(ValueError, match="Invalid period specified: bogus"):
            generate_summary_report([session], "bogus")

    def test_generate_summary_no_sessions_in_period(self):
        # Session on March 14th, period is "today" (March 15th)
        session = TaskSession(
            task_name="Yesterday Task",
            start_time=specific_utc_dt(2024, 3, 14, 10), 
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 14, 11)
        )
        report = generate_summary_report([session], "today")
        assert report == {}

    def test_generate_summary_basic_case_today(self):
        # Session today (Mar 15) 10:00 to 11:00 UTC
        session = TaskSession(
            task_name="Morning Work",
            start_time=specific_utc_dt(2024, 3, 15, 10), 
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 15, 11)
        )
        report = generate_summary_report([session], "today")
        assert report == {"Morning Work": timedelta(hours=1)}

    def test_generate_summary_partial_overlap_today(self):
        # Session starts yesterday (Mar 14 23:30) ends today (Mar 15 00:30)
        session = TaskSession(
            task_name="Late Night Task",
            start_time=specific_utc_dt(2024, 3, 14, 23, 30), 
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 15, 0, 30)
        )
        report = generate_summary_report([session], "today")
        # Only the 30 minutes on Mar 15th should count
        assert report == {"Late Night Task": timedelta(minutes=30)}

    def test_generate_summary_multiple_sessions_same_task_week(self):
        # Frozen date is Fri, Mar 15. Week starts Mon, Mar 11.
        session1 = TaskSession(
            task_name="Project X",
            start_time=specific_utc_dt(2024, 3, 12, 9), # Tue
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 12, 11) # 2 hours
        )
        session2 = TaskSession(
            task_name="Project X",
            start_time=specific_utc_dt(2024, 3, 14, 14), # Thu
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 14, 15, 30) # 1.5 hours
        )
        # Session outside the week
        session_outside = TaskSession(
            task_name="Project X",
            start_time=specific_utc_dt(2024, 3, 10, 10), # Sun before
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 10, 11)
        )
        report = generate_summary_report([session1, session2, session_outside], "week")
        assert report == {"Project X": timedelta(hours=3, minutes=30)}

    def test_generate_summary_multiple_tasks_month(self):
        # Frozen date is Mar 15. Month is March.
        task_a_mar1 = TaskSession(
            task_name="Task A", start_time=specific_utc_dt(2024, 3, 1, 8), 
            status=TaskSessionStatus.STOPPED, end_time=specific_utc_dt(2024, 3, 1, 9) # 1 hr
        )
        task_a_mar10 = TaskSession(
            task_name="Task A", start_time=specific_utc_dt(2024, 3, 10, 10), 
            status=TaskSessionStatus.STOPPED, end_time=specific_utc_dt(2024, 3, 10, 11) # 1 hr
        )
        task_b_mar5 = TaskSession(
            task_name="Task B", start_time=specific_utc_dt(2024, 3, 5, 13), 
            status=TaskSessionStatus.STOPPED, end_time=specific_utc_dt(2024, 3, 5, 14) # 1 hr
        )
        # Task A also overlaps from Feb
        task_a_feb_mar = TaskSession(
            task_name="Task A", start_time=specific_utc_dt(2024, 2, 29, 23), 
            status=TaskSessionStatus.STOPPED, end_time=specific_utc_dt(2024, 3, 1, 1) # 1 hr in March
        )
        # Task C entirely in Feb
        task_c_feb = TaskSession(
            task_name="Task C", start_time=specific_utc_dt(2024, 2, 28, 10), 
            status=TaskSessionStatus.STOPPED, end_time=specific_utc_dt(2024, 2, 28, 11) 
        )
        sessions = [task_a_mar1, task_a_mar10, task_b_mar5, task_a_feb_mar, task_c_feb]
        report = generate_summary_report(sessions, "month")
        assert report == {
            "Task A": timedelta(hours=3), # 1hr + 1hr + 1hr from overlap
            "Task B": timedelta(hours=1)
        }
        assert "Task C" not in report

    def test_generate_summary_ignores_session_with_no_name(self):
        session_named = TaskSession(
            task_name="Valid Task",
            start_time=specific_utc_dt(2024, 3, 15, 10), 
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 15, 11) # 1 hr
        )
        session_no_name = TaskSession(
            task_name="", # Empty task name
            start_time=specific_utc_dt(2024, 3, 15, 13), 
            status=TaskSessionStatus.STOPPED,
            end_time=specific_utc_dt(2024, 3, 15, 14) # 1 hr
        )
        report = generate_summary_report([session_named, session_no_name], "today")
        assert report == {"Valid Task": timedelta(hours=1)}
        assert "" not in report

    # Test involving pauses requires careful segment calculation
    def test_generate_summary_with_paused_session_overlap(self):
        # Frozen date is Mar 15. Period "today".
        start_time = specific_utc_dt(2024, 3, 15, 9, 0, 0) # Start 9:00
        pause_time = specific_utc_dt(2024, 3, 15, 9, 30, 0) # Pause 9:30 (30m elapsed)
        resume_time = specific_utc_dt(2024, 3, 15, 10, 0, 0) # Resume 10:00
        stop_time = specific_utc_dt(2024, 3, 15, 10, 15, 0) # Stop 10:15 (15m elapsed)
        
        session = TaskSession(task_name="Pause Test", start_time=start_time)
        # Simulate lifecycle
        with freeze_time(pause_time):
            session.pause()
        with freeze_time(resume_time):
            session.resume()
        with freeze_time(stop_time):
            session.stop()
            
        # Total duration = 30m + 15m = 45m
        assert session.duration == timedelta(minutes=45)
            
        report = generate_summary_report([session], "today")
        assert report == {"Pause Test": timedelta(minutes=45)}
