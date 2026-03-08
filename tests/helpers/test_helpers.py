"""Tests for the helpers module."""

from datetime import datetime, timezone

import pandas as pd

from f1.helpers.helpers import get_race_utc


class TestGetRaceUtc:
    """Tests for get_race_utc."""

    def test_returns_utc_datetime_for_race_session(self):
        event = pd.Series(
            {
                "Session1": "Practice 1",
                "Session1DateUtc": pd.Timestamp("2026-03-15 11:30:00"),
                "Session2": "Practice 2",
                "Session2DateUtc": pd.Timestamp("2026-03-15 15:00:00"),
                "Session3": "Practice 3",
                "Session3DateUtc": pd.Timestamp("2026-03-16 12:30:00"),
                "Session4": "Qualifying",
                "Session4DateUtc": pd.Timestamp("2026-03-16 16:00:00"),
                "Session5": "Race",
                "Session5DateUtc": pd.Timestamp("2026-03-17 15:00:00"),
            }
        )
        result = get_race_utc(event)
        assert result == datetime(2026, 3, 17, 15, 0, 0, tzinfo=timezone.utc)

    def test_returns_timezone_aware_datetime(self):
        event = pd.Series(
            {
                "Session1": "Race",
                "Session1DateUtc": pd.Timestamp("2026-07-05 14:00:00"),
            }
        )
        result = get_race_utc(event)
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_returns_none_when_no_race_session(self):
        event = pd.Series(
            {
                "Session1": "Practice 1",
                "Session1DateUtc": pd.Timestamp("2026-03-15 11:30:00"),
                "Session2": "Practice 2",
                "Session2DateUtc": pd.Timestamp("2026-03-15 15:00:00"),
            }
        )
        result = get_race_utc(event)
        assert result is None

    def test_returns_none_when_race_date_is_nat(self):
        event = pd.Series(
            {
                "Session1": "Race",
                "Session1DateUtc": pd.NaT,
            }
        )
        result = get_race_utc(event)
        assert result is None

    def test_finds_race_in_any_session_slot(self):
        for slot in range(1, 6):
            data = {}
            for n in range(1, 6):
                data[f"Session{n}"] = "Race" if n == slot else f"Session {n}"
                data[f"Session{n}DateUtc"] = pd.Timestamp("2026-06-01 14:00:00")
            event = pd.Series(data)
            result = get_race_utc(event)
            assert result is not None, f"Race not found in Session{slot}"

    def test_returns_none_for_empty_series(self):
        event = pd.Series(dtype=object)
        result = get_race_utc(event)
        assert result is None
