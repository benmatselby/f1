"""Tests for the race command."""

from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd
from click.testing import CliRunner

from f1.commands.race import _fmt_grid
from f1.commands.race import _fmt_int
from f1.commands.race import _fmt_position
from f1.commands.race import _fmt_time
from f1.commands.race import race


class TestFmtPosition:
    """Tests for _fmt_position."""

    def test_returns_integer_string_for_numeric_position(self):
        assert _fmt_position(1.0, "1") == "1"

    def test_truncates_float_to_integer(self):
        assert _fmt_position(3.0, "3") == "3"

    def test_falls_back_to_classified_position_when_position_is_nan(self):
        assert _fmt_position(float("nan"), "R") == "R"

    def test_returns_dash_when_both_are_nan(self):
        assert _fmt_position(float("nan"), float("nan")) == "-"

    def test_returns_dash_when_both_are_empty(self):
        assert _fmt_position(float("nan"), "") == "-"

    def test_returns_dash_when_classified_is_none_like(self):
        assert _fmt_position(float("nan"), None) == "-"

    def test_returns_position_even_when_classified_differs(self):
        assert _fmt_position(2.0, "R") == "2"

    def test_large_position_number(self):
        assert _fmt_position(20.0, "20") == "20"


class TestFmtGrid:
    """Tests for _fmt_grid."""

    def test_returns_string_for_normal_position(self):
        assert _fmt_grid(1.0) == "1"

    def test_returns_pit_for_zero(self):
        assert _fmt_grid(0.0) == "PIT"

    def test_returns_dash_for_nan(self):
        assert _fmt_grid(float("nan")) == "-"

    def test_returns_dash_for_negative(self):
        assert _fmt_grid(-1.0) == "-"

    def test_large_grid_position(self):
        assert _fmt_grid(20.0) == "20"


class TestFmtTime:
    """Tests for _fmt_time."""

    def test_leader_time_with_hours(self):
        driver = pd.Series(
            {"Time": timedelta(hours=1, minutes=23, seconds=45, milliseconds=678)}
        )
        assert _fmt_time(driver, is_leader=True) == "1:23:45.678"

    def test_leader_time_without_hours(self):
        driver = pd.Series(
            {"Time": timedelta(minutes=45, seconds=12, milliseconds=345)}
        )
        assert _fmt_time(driver, is_leader=True) == "45:12.345"

    def test_leader_time_zero_hours(self):
        driver = pd.Series({"Time": timedelta(minutes=1, seconds=30, milliseconds=100)})
        assert _fmt_time(driver, is_leader=True) == "1:30.100"

    def test_leader_time_exact_seconds(self):
        driver = pd.Series({"Time": timedelta(minutes=5, seconds=0)})
        assert _fmt_time(driver, is_leader=True) == "5:00.000"

    def test_gap_under_sixty_seconds(self):
        driver = pd.Series({"Time": timedelta(seconds=5, milliseconds=123)})
        assert _fmt_time(driver, is_leader=False) == "+5.123s"

    def test_gap_over_sixty_seconds(self):
        driver = pd.Series({"Time": timedelta(minutes=1, seconds=12, milliseconds=345)})
        assert _fmt_time(driver, is_leader=False) == "+1:12.345"

    def test_gap_exactly_sixty_seconds(self):
        driver = pd.Series({"Time": timedelta(seconds=60)})
        assert _fmt_time(driver, is_leader=False) == "+1:00.000"

    def test_gap_small_fraction(self):
        driver = pd.Series({"Time": timedelta(seconds=0, milliseconds=5)})
        assert _fmt_time(driver, is_leader=False) == "+0.005s"

    def test_returns_status_when_time_is_nat_and_status_contains_lap(self):
        driver = pd.Series({"Time": pd.NaT, "Status": "+1 Lap"})
        assert _fmt_time(driver, is_leader=False) == "+1 Lap"

    def test_returns_status_for_multiple_laps_down(self):
        driver = pd.Series({"Time": pd.NaT, "Status": "+3 Laps"})
        assert _fmt_time(driver, is_leader=False) == "+3 Laps"

    def test_returns_empty_when_time_is_nat_and_status_has_no_lap(self):
        driver = pd.Series({"Time": pd.NaT, "Status": "Retired"})
        assert _fmt_time(driver, is_leader=False) == ""

    def test_returns_empty_when_time_is_nat_and_no_status(self):
        driver = pd.Series({"Time": pd.NaT, "Status": ""})
        assert _fmt_time(driver, is_leader=False) == ""

    def test_returns_empty_when_time_is_nat_and_status_missing(self):
        driver = pd.Series({"Time": pd.NaT})
        assert _fmt_time(driver, is_leader=False) == ""

    def test_leader_time_with_two_hours(self):
        driver = pd.Series(
            {"Time": timedelta(hours=2, minutes=0, seconds=1, milliseconds=2)}
        )
        assert _fmt_time(driver, is_leader=True) == "2:00:01.002"


class TestFmtInt:
    """Tests for _fmt_int."""

    def test_formats_integer(self):
        assert _fmt_int(57) == "57"

    def test_formats_float_as_integer(self):
        assert _fmt_int(57.0) == "57"

    def test_returns_dash_for_nan(self):
        assert _fmt_int(float("nan")) == "-"

    def test_returns_dash_for_none(self):
        assert _fmt_int(None) == "-"

    def test_formats_zero(self):
        assert _fmt_int(0) == "0"


class TestRaceCommand:
    """Tests for the race click command."""

    def _make_mock_session(self, event_name="FORMULA 1 GRAND PRIX"):
        """Build a mock session with realistic results."""
        mock_session = MagicMock()
        mock_session.event = pd.Series(
            {
                "OfficialEventName": event_name,
                "EventName": "Test GP",
            }
        )
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0, 2.0, 3.0],
                "ClassifiedPosition": ["1", "2", "3"],
                "FullName": ["Max Verstappen", "Lewis Hamilton", "Charles Leclerc"],
                "Abbreviation": ["VER", "HAM", "LEC"],
                "TeamName": ["Red Bull", "Mercedes", "Ferrari"],
                "GridPosition": [1.0, 3.0, 2.0],
                "Time": [
                    timedelta(hours=1, minutes=30, seconds=0, milliseconds=123),
                    timedelta(seconds=5, milliseconds=456),
                    timedelta(seconds=10, milliseconds=789),
                ],
                "Status": ["Finished", "Finished", "Finished"],
                "Laps": [57.0, 57.0, 57.0],
                "Points": [25.0, 18.0, 15.0],
            }
        )
        return mock_session

    @patch("f1.commands.race.fastf1.get_session")
    def test_displays_race_results(self, mock_get_session):
        mock_session = self._make_mock_session()
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "FORMULA 1 GRAND PRIX" in result.output
        assert "Max Verstappen" in result.output
        assert "Lewis Hamilton" in result.output
        assert "Charles Leclerc" in result.output
        assert "Red Bull" in result.output
        assert "Mercedes" in result.output
        assert "Ferrari" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_displays_header_row(self, mock_get_session):
        mock_session = self._make_mock_session()
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        for header in (
            "Pos",
            "Driver",
            "Team",
            "Grid",
            "Time/Gap",
            "Status",
            "Laps",
            "Pts",
        ):
            assert header in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_displays_classified_count(self, mock_get_session):
        mock_session = self._make_mock_session()
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "Classified: 3" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_displays_points(self, mock_get_session):
        mock_session = self._make_mock_session()
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "25" in result.output
        assert "18" in result.output
        assert "15" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_error_when_results_empty(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.results = pd.DataFrame()
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code != 0
        assert "No results found for 'monza' 2024" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_error_when_api_fails(self, mock_get_session):
        mock_get_session.side_effect = Exception("Network error")

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code != 0
        assert "Failed to load race data" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_falls_back_to_event_name_when_no_official_name(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"EventName": "Australian Grand Prix"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0],
                "ClassifiedPosition": ["1"],
                "FullName": ["Max Verstappen"],
                "Abbreviation": ["VER"],
                "TeamName": ["Red Bull"],
                "GridPosition": [1.0],
                "Time": [timedelta(hours=1, minutes=30)],
                "Status": ["Finished"],
                "Laps": [57.0],
                "Points": [25.0],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "australia"])

        assert result.exit_code == 0
        assert "Australian Grand Prix" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_handles_retired_driver(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"OfficialEventName": "Test GP"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0, float("nan")],
                "ClassifiedPosition": ["1", "R"],
                "FullName": ["Max Verstappen", "Carlos Sainz"],
                "Abbreviation": ["VER", "SAI"],
                "TeamName": ["Red Bull", "Ferrari"],
                "GridPosition": [1.0, 5.0],
                "Time": [timedelta(hours=1, minutes=30), pd.NaT],
                "Status": ["Finished", "Retired"],
                "Laps": [57.0, 30.0],
                "Points": [25.0, 0.0],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "Carlos Sainz" in result.output
        assert "Classified: 1" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_handles_lapped_driver(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"OfficialEventName": "Test GP"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0, 2.0],
                "ClassifiedPosition": ["1", "2"],
                "FullName": ["Max Verstappen", "Lewis Hamilton"],
                "Abbreviation": ["VER", "HAM"],
                "TeamName": ["Red Bull", "Mercedes"],
                "GridPosition": [1.0, 3.0],
                "Time": [timedelta(hours=1, minutes=30), pd.NaT],
                "Status": ["Finished", "+1 Lap"],
                "Laps": [57.0, 56.0],
                "Points": [25.0, 18.0],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "+1 Lap" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_handles_pit_lane_start(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"OfficialEventName": "Test GP"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0],
                "ClassifiedPosition": ["1"],
                "FullName": ["Max Verstappen"],
                "Abbreviation": ["VER"],
                "TeamName": ["Red Bull"],
                "GridPosition": [0.0],
                "Time": [timedelta(hours=1, minutes=30)],
                "Status": ["Finished"],
                "Laps": [57.0],
                "Points": [25.0],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "PIT" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_formats_half_points(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"OfficialEventName": "Test GP"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0],
                "ClassifiedPosition": ["1"],
                "FullName": ["Max Verstappen"],
                "Abbreviation": ["VER"],
                "TeamName": ["Red Bull"],
                "GridPosition": [1.0],
                "Time": [timedelta(hours=1, minutes=30)],
                "Status": ["Finished"],
                "Laps": [57.0],
                "Points": [12.5],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "12.5" in result.output

    @patch("f1.commands.race.fastf1.get_session")
    def test_uses_abbreviation_when_full_name_empty(self, mock_get_session):
        mock_session = MagicMock()
        mock_session.event = pd.Series({"OfficialEventName": "Test GP"})
        mock_session.results = pd.DataFrame(
            {
                "Position": [1.0],
                "ClassifiedPosition": ["1"],
                "FullName": [""],
                "Abbreviation": ["VER"],
                "TeamName": ["Red Bull"],
                "GridPosition": [1.0],
                "Time": [timedelta(hours=1, minutes=30)],
                "Status": ["Finished"],
                "Laps": [57.0],
                "Points": [25.0],
            }
        )
        mock_get_session.return_value = mock_session

        runner = CliRunner()
        result = runner.invoke(race, ["2024", "monza"])

        assert result.exit_code == 0
        assert "VER" in result.output
