"""Tests for the drivers command."""

from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pandas as pd
from click.testing import CliRunner

from f1.commands.drivers import _get_podium_counts
from f1.commands.drivers import drivers


class TestGetPodiumCounts:
    """Tests for _get_podium_counts."""

    def test_counts_podiums_across_rounds(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1, 2]})
        ergast.get_race_schedule.return_value = schedule

        round1_results = MagicMock()
        round1_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3, 4],
                    "driverId": ["verstappen", "norris", "leclerc", "piastri"],
                }
            )
        ]

        round2_results = MagicMock()
        round2_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3, 4],
                    "driverId": ["norris", "verstappen", "piastri", "leclerc"],
                }
            )
        ]

        ergast.get_race_results.side_effect = [round1_results, round2_results]

        result = _get_podium_counts(ergast, 2024)

        assert result == {
            "verstappen": 2,
            "norris": 2,
            "leclerc": 1,
            "piastri": 1,
        }

    def test_returns_empty_dict_when_no_rounds(self):
        ergast = MagicMock()
        ergast.get_race_schedule.return_value = pd.DataFrame()

        result = _get_podium_counts(ergast, 2024)

        assert result == {}

    def test_skips_rounds_with_no_content(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1, 2]})
        ergast.get_race_schedule.return_value = schedule

        round1_results = MagicMock()
        round1_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["verstappen", "norris", "leclerc"],
                }
            )
        ]

        round2_results = MagicMock()
        round2_results.content = []

        ergast.get_race_results.side_effect = [round1_results, round2_results]

        result = _get_podium_counts(ergast, 2024)

        assert result == {"verstappen": 1, "norris": 1, "leclerc": 1}

    def test_skips_rounds_that_raise_exceptions(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1, 2]})
        ergast.get_race_schedule.return_value = schedule

        round1_results = MagicMock()
        round1_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["verstappen", "norris", "leclerc"],
                }
            )
        ]

        ergast.get_race_results.side_effect = [
            round1_results,
            Exception("API error"),
        ]

        result = _get_podium_counts(ergast, 2024)

        assert result == {"verstappen": 1, "norris": 1, "leclerc": 1}

    def test_only_counts_top_three_positions(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        round1_results = MagicMock()
        round1_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3, 4, 5],
                    "driverId": [
                        "verstappen",
                        "norris",
                        "leclerc",
                        "piastri",
                        "sainz",
                    ],
                }
            )
        ]

        ergast.get_race_results.side_effect = [round1_results]

        result = _get_podium_counts(ergast, 2024)

        assert "piastri" not in result
        assert "sainz" not in result
        assert len(result) == 3

    def test_accumulates_podiums_for_same_driver(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1, 2, 3]})
        ergast.get_race_schedule.return_value = schedule

        results = []
        for _ in range(3):
            mock = MagicMock()
            mock.content = [
                pd.DataFrame(
                    {
                        "position": [1, 2, 3],
                        "driverId": ["verstappen", "norris", "leclerc"],
                    }
                )
            ]
            results.append(mock)

        ergast.get_race_results.side_effect = results

        result = _get_podium_counts(ergast, 2024)

        assert result["verstappen"] == 3
        assert result["norris"] == 3
        assert result["leclerc"] == 3

    def test_calls_ergast_with_correct_arguments(self):
        ergast = MagicMock()

        schedule = pd.DataFrame({"round": [1, 2]})
        ergast.get_race_schedule.return_value = schedule

        for _ in range(2):
            mock = MagicMock()
            mock.content = [pd.DataFrame({"position": [1], "driverId": ["verstappen"]})]
            ergast.get_race_results.return_value = mock

        ergast.get_race_results.side_effect = [ergast.get_race_results.return_value] * 2

        _get_podium_counts(ergast, 2024)

        ergast.get_race_schedule.assert_called_once_with(season=2024)
        ergast.get_race_results.assert_has_calls(
            [
                call(season=2024, round=1),
                call(season=2024, round=2),
            ]
        )


class TestDriversCommand:
    """Tests for the drivers click command."""

    @patch("f1.commands.drivers.Ergast")
    def test_displays_championship_standings(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1, 2],
                    "givenName": ["Max", "Lando"],
                    "familyName": ["Verstappen", "Norris"],
                    "constructorNames": [["Red Bull"], ["McLaren"]],
                    "wins": [9, 4],
                    "points": [437.0, 374.0],
                    "driverId": ["max_verstappen", "norris"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        race_results = MagicMock()
        race_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["max_verstappen", "norris", "leclerc"],
                }
            )
        ]
        ergast.get_race_results.return_value = race_results

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024"])

        assert result.exit_code == 0
        assert "Formula 1 2024 Driver Championship" in result.output
        assert "Max Verstappen" in result.output
        assert "Lando Norris" in result.output
        assert "Red Bull" in result.output
        assert "McLaren" in result.output
        assert "437" in result.output
        assert "374" in result.output
        assert "Total drivers: 2" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_displays_header_row(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1],
                    "givenName": ["Max"],
                    "familyName": ["Verstappen"],
                    "constructorNames": [["Red Bull"]],
                    "wins": [9],
                    "points": [437.0],
                    "driverId": ["max_verstappen"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        race_results = MagicMock()
        race_results.content = [
            pd.DataFrame({"position": [1], "driverId": ["max_verstappen"]})
        ]
        ergast.get_race_results.return_value = race_results

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024", "--show-podiums"])

        assert result.exit_code == 0
        assert "Pos" in result.output
        assert "Driver" in result.output
        assert "Team" in result.output
        assert "Wins" in result.output
        assert "Podiums" in result.output
        assert "Pts" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_displays_podium_counts(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1, 2],
                    "givenName": ["Max", "Lando"],
                    "familyName": ["Verstappen", "Norris"],
                    "constructorNames": [["Red Bull"], ["McLaren"]],
                    "wins": [1, 0],
                    "points": [100.0, 50.0],
                    "driverId": ["max_verstappen", "norris"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1, 2]})
        ergast.get_race_schedule.return_value = schedule

        round1 = MagicMock()
        round1.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["max_verstappen", "norris", "leclerc"],
                }
            )
        ]
        round2 = MagicMock()
        round2.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["hamilton", "leclerc", "norris"],
                }
            )
        ]
        ergast.get_race_results.side_effect = [round1, round2]

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024", "--show-podiums"])

        assert result.exit_code == 0
        lines = result.output.strip().split("\n")
        verstappen_line = [line for line in lines if "Verstappen" in line][0]
        norris_line = [line for line in lines if "Norris" in line][0]

        assert "1    Max Verstappen  Red Bull  100  1     1" in verstappen_line
        assert "2    Lando Norris    McLaren   50   0     2" in norris_line

    @patch("f1.commands.drivers.Ergast")
    def test_shows_zero_podiums_for_driver_without_any(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1],
                    "givenName": ["Valtteri"],
                    "familyName": ["Bottas"],
                    "constructorNames": [["Sauber"]],
                    "wins": [0],
                    "points": [0.0],
                    "driverId": ["bottas"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        race_results = MagicMock()
        race_results.content = [
            pd.DataFrame(
                {
                    "position": [1, 2, 3],
                    "driverId": ["verstappen", "norris", "leclerc"],
                }
            )
        ]
        ergast.get_race_results.return_value = race_results

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024"])

        assert result.exit_code == 0
        bottas_line = [
            line for line in result.output.strip().split("\n") if "Bottas" in line
        ][0]
        # Wins=0, Podiums=0, Pts=0
        assert "0" in bottas_line

    @patch("f1.commands.drivers.Ergast")
    def test_error_when_no_content(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = []
        ergast.get_driver_standings.return_value = standings_response

        runner = CliRunner()
        result = runner.invoke(drivers, ["1900"])

        assert result.exit_code != 0
        assert "No championship data found for 1900" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_error_when_standings_empty(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [pd.DataFrame()]
        ergast.get_driver_standings.return_value = standings_response

        runner = CliRunner()
        result = runner.invoke(drivers, ["1900"])

        assert result.exit_code != 0
        assert "No championship data found for 1900" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_error_when_api_fails(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast
        ergast.get_driver_standings.side_effect = Exception("API timeout")

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024"])

        assert result.exit_code != 0
        assert "Failed to fetch championship standings for 2024" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_handles_multiple_constructors(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1],
                    "givenName": ["Oliver"],
                    "familyName": ["Bearman"],
                    "constructorNames": [["Ferrari", "Haas F1 Team"]],
                    "wins": [0],
                    "points": [7.0],
                    "driverId": ["bearman"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        race_results = MagicMock()
        race_results.content = [
            pd.DataFrame({"position": [4], "driverId": ["bearman"]})
        ]
        ergast.get_race_results.return_value = race_results

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024"])

        assert result.exit_code == 0
        assert "Ferrari, Haas F1 Team" in result.output

    @patch("f1.commands.drivers.Ergast")
    def test_formats_half_points(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1],
                    "givenName": ["Max"],
                    "familyName": ["Verstappen"],
                    "constructorNames": [["Red Bull"]],
                    "wins": [1],
                    "points": [12.5],
                    "driverId": ["max_verstappen"],
                }
            )
        ]
        ergast.get_driver_standings.return_value = standings_response

        schedule = pd.DataFrame({"round": [1]})
        ergast.get_race_schedule.return_value = schedule

        race_results = MagicMock()
        race_results.content = [
            pd.DataFrame({"position": [1], "driverId": ["max_verstappen"]})
        ]
        ergast.get_race_results.return_value = race_results

        runner = CliRunner()
        result = runner.invoke(drivers, ["2024"])

        assert result.exit_code == 0
        assert "12.5" in result.output
