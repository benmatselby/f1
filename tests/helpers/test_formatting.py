"""Tests for the formatting helpers module."""

from f1.helpers.formatting import fmt_points


class TestFmtPoints:
    """Tests for fmt_points."""

    def test_formats_integer_points(self):
        assert fmt_points(25.0) == "25"

    def test_formats_zero_points(self):
        assert fmt_points(0.0) == "0"

    def test_formats_half_points(self):
        assert fmt_points(12.5) == "12.5"

    def test_formats_large_integer_points(self):
        assert fmt_points(437.0) == "437"

    def test_formats_integer_value(self):
        assert fmt_points(10) == "10"

    def test_returns_zero_for_nan(self):
        assert fmt_points(float("nan")) == "0"

    def test_returns_zero_for_none(self):
        assert fmt_points(None) == "0"
