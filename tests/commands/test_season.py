"""Tests for the season command helpers."""

from f1.commands.season import _progress_bar


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
