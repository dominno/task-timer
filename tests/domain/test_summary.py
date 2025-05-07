import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

try:
    from unittest import mock
except ImportError:  # Python 2
    import mock  # type: ignore

# Attempt to import summary functions (will be created in src/domain/summary.py)
try:
    from src.domain.summary import (
        get_today_range,
        get_this_week_range,  # Monday as start of week
        get_this_month_range,
        get_this_year_range,
        get_duration_within_period,
    )
    from src.domain.session import TaskSession  # For type hint and creating instances
except ImportError:
    get_today_range = None  # type: ignore
    get_this_week_range = None  # type: ignore
    get_this_month_range = None  # type: ignore
    get_this_year_range = None  # type: ignore
    get_duration_within_period = None  # type: ignore
    TaskSession = None  # type: ignore

# All datetime objects created by helpers should be timezone-aware (UTC start of day /
# end of day) and should represent the very start (00:00:00) and very end
# (23:59:59.999999) of the period.


@pytest.mark.skipif(get_today_range is None, reason="get_today_range not implemented")
@freeze_time("2024-07-15T14:30:00Z")  # Monday
def test_get_today_range():
    start_of_day, end_of_day = get_today_range()
    assert start_of_day == datetime(2024, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert end_of_day == datetime(2024, 7, 15, 23, 59, 59, 999999, tzinfo=timezone.utc)


@pytest.mark.skipif(
    get_this_week_range is None, reason="get_this_week_range not implemented"
)
@freeze_time("2024-07-15T10:00:00Z")  # Monday, July 15th, 2024
def test_get_this_week_range_on_monday():
    start_of_week, end_of_week = get_this_week_range()
    assert start_of_week == datetime(
        2024, 7, 15, 0, 0, 0, tzinfo=timezone.utc
    )  # Current Monday
    assert end_of_week == datetime(
        2024, 7, 21, 23, 59, 59, 999999, tzinfo=timezone.utc
    )  # Sunday of this week


@pytest.mark.skipif(
    get_this_week_range is None, reason="get_this_week_range not implemented"
)
@freeze_time("2024-07-17T16:00:00Z")  # Wednesday, July 17th, 2024
def test_get_this_week_range_on_wednesday():
    start_of_week, end_of_week = get_this_week_range()
    assert start_of_week == datetime(
        2024, 7, 15, 0, 0, 0, tzinfo=timezone.utc
    )  # Monday of this week
    assert end_of_week == datetime(
        2024, 7, 21, 23, 59, 59, 999999, tzinfo=timezone.utc
    )  # Sunday of this week


@pytest.mark.skipif(
    get_this_week_range is None, reason="get_this_week_range not implemented"
)
@freeze_time("2024-07-21T23:00:00Z")  # Sunday, July 21st, 2024
def test_get_this_week_range_on_sunday():
    start_of_week, end_of_week = get_this_week_range()
    assert start_of_week == datetime(
        2024, 7, 15, 0, 0, 0, tzinfo=timezone.utc
    )  # Monday of this week
    assert end_of_week == datetime(
        2024, 7, 21, 23, 59, 59, 999999, tzinfo=timezone.utc
    )  # Current Sunday


@pytest.mark.skipif(
    get_this_month_range is None, reason="get_this_month_range not implemented"
)
@freeze_time("2024-07-15T10:00:00Z")
def test_get_this_month_range():
    start_of_month, end_of_month = get_this_month_range()
    assert start_of_month == datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert end_of_month == datetime(
        2024, 7, 31, 23, 59, 59, 999999, tzinfo=timezone.utc
    )


@pytest.mark.skipif(
    get_this_month_range is None, reason="get_this_month_range not implemented"
)
@freeze_time("2024-02-10T10:00:00Z")  # Leap year
def test_get_this_month_range_feb_leap_year():
    start_of_month, end_of_month = get_this_month_range()
    assert start_of_month == datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert end_of_month == datetime(
        2024, 2, 29, 23, 59, 59, 999999, tzinfo=timezone.utc
    )


@pytest.mark.skipif(
    get_this_year_range is None, reason="get_this_year_range not implemented"
)
@freeze_time("2024-07-15T10:00:00Z")
def test_get_this_year_range():
    start_of_year, end_of_year = get_this_year_range()
    assert start_of_year == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert end_of_year == datetime(
        2024, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc
    )


# --- Tests for get_duration_within_period ---

# Need TaskSession for these tests
# For simplicity in test setup, we might mock get_active_segments
# or create TaskSession instances and manually set their segment-related fields.
# Let's try mocking get_active_segments for focused unit tests on overlap logic.


@pytest.fixture
def mock_session_with_segments(monkeypatch):
    """Fixture to create a mock TaskSession that returns predefined segments."""
    if TaskSession is None:
        pytest.skip("TaskSession not available")

    def _set_segments(segments_to_return):
        # Create a fresh mock session each time _set_segments is called
        fresh_mock_session = mock.MagicMock(spec=TaskSession)
        monkeypatch.setattr(
            fresh_mock_session, "get_active_segments", lambda: segments_to_return
        )
        # Initialize task_name to None by default on the mock, similar to a real new
        # TaskSession might not have it immediately
        # Or rely on tests to set it. For spec adherence, TaskSession requires
        # task_name on init.
        # Let's assume tests will set it. The spec will ensure task_name is a valid
        # attribute.
        return fresh_mock_session

    return _set_segments


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_fully_inside(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Segment: 10:30 to 11:30 (1 hour)
    segments = [
        (
            datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 11, 30, 0, tzinfo=timezone.utc),
        )
    ]
    session = mock_session_with_segments(segments)

    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(hours=1)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_fully_outside(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Segment before: 08:00 to 09:00
    segments_before = [
        (
            datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        )
    ]
    session_before = mock_session_with_segments(segments_before)
    assert get_duration_within_period(
        session_before, period_start, period_end
    ) == timedelta(0)

    # Segment after: 13:00 to 14:00
    segments_after = [
        (
            datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        )
    ]
    session_after = mock_session_with_segments(segments_after)
    assert get_duration_within_period(
        session_after, period_start, period_end
    ) == timedelta(0)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_straddle_start(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Segment: 09:30 to 10:30 (overlaps 30 mins into period)
    segments = [
        (
            datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
        )
    ]
    session = mock_session_with_segments(segments)
    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(minutes=30)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_straddle_end(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Segment: 11:30 to 12:30 (overlaps 30 mins at end of period)
    segments = [
        (
            datetime(2024, 1, 1, 11, 30, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        )
    ]
    session = mock_session_with_segments(segments)
    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(minutes=30)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_encompass_period(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )  # Period is 2 hours

    # Segment: 09:00 to 13:00 (encompasses the 2hr period)
    segments = [
        (
            datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )
    ]
    session = mock_session_with_segments(segments)
    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(hours=2)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_multiple_segments(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(
        2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc
    )  # Period 10:00 - 14:00

    segments = [
        (
            datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
        ),  # 30m in period
        (
            datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 11, 45, 0, tzinfo=timezone.utc),
        ),  # 45m in period
        (
            datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        ),  # 30m in period
        (
            datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 16, 0, 0, tzinfo=timezone.utc),
        ),  # 0m in period
    ]
    session = mock_session_with_segments(segments)
    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(minutes=(30 + 45 + 30))


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time("2024-01-01T12:00:00Z")  # "now" for ongoing session
def test_get_duration_within_period_ongoing_session(mock_session_with_segments):
    period_start = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(
        2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc
    )  # Period 11:00 - 13:00

    # Segment: 11:30 to now (12:00) -> 30m in period
    current_time = datetime.now(timezone.utc)  # This will be the frozen time
    segments = [(datetime(2024, 1, 1, 11, 30, 0, tzinfo=timezone.utc), current_time)]
    session = mock_session_with_segments(segments)

    duration = get_duration_within_period(session, period_start, period_end)
    assert duration == timedelta(minutes=30)


@pytest.mark.skipif(
    get_duration_within_period is None or TaskSession is None,
    reason="Dependencies not met",
)
def test_get_duration_within_period_no_overlap_segment_same_time_as_period_boundary(
    mock_session_with_segments,
):
    period_start = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    period_end = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Segment ends exactly when period starts
    segments1 = [
        (
            datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        )
    ]
    session1 = mock_session_with_segments(segments1)
    assert get_duration_within_period(session1, period_start, period_end) == timedelta(
        0
    )

    # Segment starts exactly when period ends
    segments2 = [
        (
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
        )
    ]
    session2 = mock_session_with_segments(segments2)
    assert get_duration_within_period(session2, period_start, period_end) == timedelta(
        0
    )


# --- Tests for generate_summary_report ---

# Attempt to import generate_summary_report
try:
    from src.domain.summary import generate_summary_report
except ImportError:
    generate_summary_report = None  # type: ignore

FROZEN_NOW = datetime(
    2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc
)  # Monday, July 15th, 2024, 12:00 PM UTC


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_NOW.isoformat().replace("+00:00", "Z"))
def test_generate_summary_report_empty_sessions():
    report = generate_summary_report(sessions=[], period_name="today")
    assert report == {}


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_NOW.isoformat().replace("+00:00", "Z"))
def test_generate_summary_report_invalid_period_name(monkeypatch):
    mock_session = mock.MagicMock(spec=TaskSession)
    mock_session.task_name = "TASK-001"  # Use task_name
    monkeypatch.setattr(mock_session, "get_active_segments", lambda: [])

    report = generate_summary_report(
        sessions=[mock_session], period_name="invalid_period"
    )
    assert report == {}


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(
    FROZEN_NOW.isoformat().replace("+00:00", "Z")
)  # Monday, July 15th, 2024, 12:00
def test_generate_summary_report_today_single_task(
    mock_session_with_segments, monkeypatch
):
    # Today is July 15th, 2024. Period: 2024-07-15 00:00:00 to 23:59:59.999999

    # Session 1 for TASK-001: 10:00 to 11:00 today (1 hour)
    segments1 = [(FROZEN_NOW.replace(hour=10), FROZEN_NOW.replace(hour=11))]
    session1 = mock_session_with_segments(segments1)
    session1.task_name = "TASK-001"  # Use task_name

    # Session 2 for TASK-002: Yesterday 10:00 to 11:00 (should not be included)
    yesterday = FROZEN_NOW - timedelta(days=1)
    segments2 = [(yesterday.replace(hour=10), yesterday.replace(hour=11))]
    session2 = mock_session_with_segments(segments2)
    session2.task_name = "TASK-002"  # Use task_name

    report = generate_summary_report(sessions=[session1, session2], period_name="today")

    assert len(report) == 1
    assert "TASK-001" in report
    assert report["TASK-001"] == timedelta(hours=1)
    assert "TASK-002" not in report


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(
    FROZEN_NOW.isoformat().replace("+00:00", "Z")
)  # Monday, July 15th, 2024, 12:00
def test_generate_summary_report_this_week_multiple_tasks_aggregation(
    mock_session_with_segments, monkeypatch
):
    # This week (Mon, Jul 15 - Sun, Jul 21)
    # FROZEN_NOW is Monday, July 15th

    # TASK-001
    # Session 1 (Mon 10:00-11:00 = 1 hr)
    segments1 = [(FROZEN_NOW.replace(hour=10), FROZEN_NOW.replace(hour=11))]
    session1 = mock_session_with_segments(segments1)
    session1.task_name = "TASK-001"  # Use task_name

    # Session 2 (Wed 14:00-14:30 = 0.5 hr)
    wednesday = FROZEN_NOW + timedelta(days=2)  # July 17th
    segments2 = [(wednesday.replace(hour=14), wednesday.replace(hour=14, minute=30))]
    session2 = mock_session_with_segments(segments2)
    session2.task_name = "TASK-001"  # Use task_name

    # TASK-002
    # Session 3 (Tue 09:00-09:15 = 0.25 hr)
    tuesday = FROZEN_NOW + timedelta(days=1)  # July 16th
    segments3 = [(tuesday.replace(hour=9), tuesday.replace(hour=9, minute=15))]
    session3 = mock_session_with_segments(segments3)
    session3.task_name = "TASK-002"  # Use task_name

    # Session 4 (Last week - should not be included)
    last_week_day = FROZEN_NOW - timedelta(days=7)
    segments4 = [(last_week_day.replace(hour=10), last_week_day.replace(hour=11))]
    session4 = mock_session_with_segments(segments4)
    session4.task_name = "TASK-003"  # Use task_name

    sessions_list = [session1, session2, session3, session4]
    report = generate_summary_report(sessions=sessions_list, period_name="this_week")

    assert len(report) == 2
    assert "TASK-001" in report
    assert report["TASK-001"] == timedelta(hours=1, minutes=30)
    assert "TASK-002" in report
    assert report["TASK-002"] == timedelta(minutes=15)
    assert "TASK-003" not in report


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(FROZEN_NOW.isoformat().replace("+00:00", "Z"))
def test_generate_summary_report_session_no_task_name(
    mock_session_with_segments, monkeypatch
):  # Renamed test
    segments = [(FROZEN_NOW.replace(hour=10), FROZEN_NOW.replace(hour=11))]
    session_no_name = mock_session_with_segments(segments)
    session_no_name.task_name = None  # Use task_name, set to None

    session_with_name = mock_session_with_segments(segments)
    session_with_name.task_name = "TASK-VALID"  # Use task_name

    report = generate_summary_report(
        sessions=[session_no_name, session_with_name], period_name="today"
    )
    assert len(report) == 1
    assert "TASK-VALID" in report
    assert report["TASK-VALID"] == timedelta(hours=1)


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(
    FROZEN_NOW.isoformat().replace("+00:00", "Z")
)  # Monday, July 15th, 2024, 12:00
def test_generate_summary_report_this_month(mock_session_with_segments, monkeypatch):
    # This month is July 2024. Period: 2024-07-01 00:00 to 2024-07-31 23:59

    # Session 1 (July 1st, 10:00-11:00 = 1hr)
    july_1st = FROZEN_NOW.replace(day=1, hour=10)
    segments1 = [(july_1st, july_1st.replace(hour=11))]
    session1 = mock_session_with_segments(segments1)
    session1.task_name = "TASK-MONTHLY-1"  # Use task_name

    # Session 2 (July 15th - FROZEN_NOW, 09:00-09:30 = 0.5hr)
    segments2 = [(FROZEN_NOW.replace(hour=9), FROZEN_NOW.replace(hour=9, minute=30))]
    session2 = mock_session_with_segments(segments2)
    session2.task_name = "TASK-MONTHLY-1"  # Use task_name

    # Session 3 (June 30th - should not be included)
    june_30th = FROZEN_NOW.replace(month=6, day=30, hour=10)
    segments3 = [(june_30th, june_30th.replace(hour=11))]
    session3 = mock_session_with_segments(segments3)
    session3.task_name = "TASK-OUTSIDE"  # Use task_name

    report = generate_summary_report(
        sessions=[session1, session2, session3], period_name="this_month"
    )
    assert len(report) == 1
    assert "TASK-MONTHLY-1" in report
    assert report["TASK-MONTHLY-1"] == timedelta(hours=1, minutes=30)
    assert "TASK-OUTSIDE" not in report


@pytest.mark.skipif(
    generate_summary_report is None or TaskSession is None,
    reason="Dependencies not met",
)
@freeze_time(
    FROZEN_NOW.isoformat().replace("+00:00", "Z")
)  # Monday, July 15th, 2024, 12:00
def test_generate_summary_report_this_year(mock_session_with_segments, monkeypatch):
    # This year is 2024. Period: 2024-01-01 00:00 to 2024-12-31 23:59

    # Session 1 (Jan 10th, 10:00-12:00 = 2hr)
    jan_10th = FROZEN_NOW.replace(month=1, day=10, hour=10)
    segments1 = [(jan_10th, jan_10th.replace(hour=12))]
    session1 = mock_session_with_segments(segments1)
    session1.task_name = "TASK-YEARLY-1"  # Use task_name

    # Session 2 (July 15th - FROZEN_NOW, 08:00-08:45 = 0.75hr)
    segments2 = [(FROZEN_NOW.replace(hour=8), FROZEN_NOW.replace(hour=8, minute=45))]
    session2 = mock_session_with_segments(segments2)
    session2.task_name = "TASK-YEARLY-1"  # Use task_name

    # Session 3 (Dec 20th, 14:00-15:00 = 1hr)
    dec_20th = FROZEN_NOW.replace(month=12, day=20, hour=14)
    segments3 = [(dec_20th, dec_20th.replace(hour=15))]
    session3 = mock_session_with_segments(segments3)
    session3.task_name = "TASK-YEARLY-2"  # Use task_name

    # Session 4 (Last year - Dec 31st 2023 - should not be included)
    last_year_dec_31st = FROZEN_NOW.replace(year=2023, month=12, day=31, hour=10)
    segments4 = [(last_year_dec_31st, last_year_dec_31st.replace(hour=11))]
    session4 = mock_session_with_segments(segments4)
    session4.task_name = "TASK-OUTSIDE"  # Use task_name

    report = generate_summary_report(
        sessions=[session1, session2, session3, session4], period_name="this_year"
    )
    assert len(report) == 2
    assert "TASK-YEARLY-1" in report
    assert report["TASK-YEARLY-1"] == timedelta(hours=2, minutes=45)
    assert "TASK-YEARLY-2" in report
    assert report["TASK-YEARLY-2"] == timedelta(hours=1)
    assert "TASK-OUTSIDE" not in report
