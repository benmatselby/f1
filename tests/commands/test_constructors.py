"""Tests for the constructors command."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd
from click.testing import CliRunner

from f1.commands.constructors import constructors


class TestConstructorsCommand:
    """Tests for the constructors click command."""

    @patch("f1.commands.constructors.Ergast")
    def test_displays_championship_standings(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = [
            pd.DataFrame(
                {
                    "position": [1],
                    "constructorName": "McLaren",
                    "constructorNationality": "British",
                    "wins": [9],
                    "points": [437.0],
                }
            )
        ]
        ergast.get_constructor_standings.return_value = standings_response

        runner = CliRunner()
        result = runner.invoke(constructors, ["2024"])

        assert result.exit_code == 0
        assert (
            result.output
            == """
Formula 1 2024 Constructors Championship

Pos  Team     Nationality  Pts  Wins
------------------------------------
1    McLaren  British      437  9

Total constructors: 1
"""
        )



    @patch("f1.commands.constructors.Ergast")
    def test_error_when_no_content(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast

        standings_response = MagicMock()
        standings_response.content = []
        ergast.get_constructor_standings.return_value = standings_response

        runner = CliRunner()
        result = runner.invoke(constructors, ["1900"])

        assert result.exit_code != 0
        assert "No championship data found for 1900" in result.output


    @patch("f1.commands.constructors.Ergast")
    def test_error_when_api_fails(self, mock_ergast_cls):
        ergast = MagicMock()
        mock_ergast_cls.return_value = ergast
        ergast.get_constructor_standings.side_effect = Exception("API timeout")

        runner = CliRunner()
        result = runner.invoke(constructors, ["2024"])

        assert result.exit_code != 0
        assert "Failed to fetch championship standings for 2024" in result.output

