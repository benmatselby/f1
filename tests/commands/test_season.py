"""Tests for the season command helpers."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd

from f1.commands.season import _format_location, _get_pole_sitter, _progress_bar


class TestProgressBar:
    """Tests for _progress_bar."""

    def test_returns_empty_string_when_total_is_zero(self):
        assert _progress_bar(0, 0) == ""

    def test_no_races_completed(self):
        result = _progress_bar(0, 24)
        assert result == "[------------------------------] 0/24 (0%)"

    def test_all_races_completed(self):
        result = _progress_bar(24, 24)
        assert result == "[##############################] 24/24 (100%)"

    def test_half_completed(self):
        result = _progress_bar(12, 24)
        assert result == "[###############---------------] 12/24 (50%)"

    def test_one_of_many_completed(self):
        result = _progress_bar(1, 24)
        assert "[#" in result
        assert "1/24" in result

    def test_custom_width(self):
        result = _progress_bar(5, 10, width=10)
        assert result == "[#####-----] 5/10 (50%)"

    def test_custom_width_full(self):
        result = _progress_bar(10, 10, width=10)
        assert result == "[##########] 10/10 (100%)"

    def test_percentage_rounds_to_nearest_integer(self):
        result = _progress_bar(1, 3)
        assert "(33%)" in result

    def test_single_race_season_completed(self):
        result = _progress_bar(1, 1)
        assert result == "[##############################] 1/1 (100%)"

    def test_single_race_season_not_completed(self):
        result = _progress_bar(0, 1)
        assert result == "[------------------------------] 0/1 (0%)"


class TestFormatLocation:
    """Tests for _format_location."""

    def test_location_and_country(self):
        event = pd.Series({"Location": "Silverstone", "Country": "United Kingdom"})
        assert _format_location(event) == "Silverstone, United Kingdom"

    def test_location_only(self):
        event = pd.Series({"Location": "Monaco", "Country": ""})
        assert _format_location(event) == "Monaco"

    def test_country_only(self):
        event = pd.Series({"Location": "", "Country": "Italy"})
        assert _format_location(event) == "Italy"

    def test_neither_location_nor_country(self):
        event = pd.Series({"Location": "", "Country": ""})
        assert _format_location(event) == "TBC"

    def test_missing_both_keys(self):
        event = pd.Series({"EventName": "Test GP"})
        assert _format_location(event) == "TBC"

    def test_missing_location_key(self):
        event = pd.Series({"Country": "Australia"})
        assert _format_location(event) == "Australia"

    def test_missing_country_key(self):
        event = pd.Series({"Location": "Melbourne"})
        assert _format_location(event) == "Melbourne"


class TestGetPoleSitter:
    """Tests for _get_pole_sitter."""

    def test_returns_empty_for_future_race(self):
        now = datetime(2024, 3, 1, tzinfo=timezone.utc)
        event = pd.Series(
            {
                "RoundNumber": 1,
                "Session5DateUtc": pd.Timestamp("2024-06-01"),
                "Session5": "Race",
            }
        )
        assert _get_pole_sitter(now, 2024, event) == ""

    @patch("f1.commands.season.fastf1.get_session")
    def test_returns_pole_sitter_full_name(self, mock_get_session):
        now = datetime(2024, 12, 1, tzinfo=timezone.utc)
        event = pd.Series(
            {
                "RoundNumber": 1,
                "Session5DateUtc": pd.Timestamp("2024-03-01"),
                "Session5": "Race",
            }
        )

        mock_session = MagicMock()
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0, 2.0],
                "FullName": ["Max Verstappen", "Lewis Hamilton"],
                "Abbreviation": ["VER", "HAM"],
            }
        )
        mock_get_session.return_value = mock_session

        result = _get_pole_sitter(now, 2024, event)
        assert result == "Max Verstappen"
        mock_get_session.assert_called_once_with(2024, 1, "Q")

    @patch("f1.commands.season.fastf1.get_session")
    def test_returns_empty_when_results_empty(self, mock_get_session):
        now = datetime(2024, 12, 1, tzinfo=timezone.utc)
        event = pd.Series(
            {
                "RoundNumber": 1,
                "Session5DateUtc": pd.Timestamp("2024-03-01"),
                "Session5": "Race",
            }
        )

        mock_session = MagicMock()
        mock_session.results = pd.DataFrame()
        mock_get_session.return_value = mock_session

        assert _get_pole_sitter(now, 2024, event) == ""

    @patch("f1.commands.season.fastf1.get_session")
    def test_returns_empty_on_exception(self, mock_get_session):
        now = datetime(2024, 12, 1, tzinfo=timezone.utc)
        event = pd.Series(
            {
                "RoundNumber": 1,
                "Session5DateUtc": pd.Timestamp("2024-03-01"),
                "Session5": "Race",
            }
        )

        mock_get_session.side_effect = Exception("API error")

        assert _get_pole_sitter(now, 2024, event) == ""

    @patch("f1.commands.season.fastf1.get_session")
    def test_returns_abbreviation_when_no_full_name(self, mock_get_session):
        now = datetime(2024, 12, 1, tzinfo=timezone.utc)
        event = pd.Series(
            {
                "RoundNumber": 1,
                "Session5DateUtc": pd.Timestamp("2024-03-01"),
                "Session5": "Race",
            }
        )

        mock_session = MagicMock()
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0],
                "FullName": [""],
                "Abbreviation": ["VER"],
            }
        )
        mock_get_session.return_value = mock_session

        assert _get_pole_sitter(now, 2024, event) == "VER"
