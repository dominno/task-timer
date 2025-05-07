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
    from src.domain.summary import get_duration_within_period, get_date_range_for_period
except ImportError:
    TaskSession = None  # type: ignore
    TaskSessionStatus = None  # type: ignore
    get_duration_within_period = None  # type: ignore
    get_date_range_for_period = None  # type: ignore

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
