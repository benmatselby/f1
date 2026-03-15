"""Tests for the formatting helpers module."""

from click.testing import CliRunner

import click

from f1.helpers.formatting import print_table, fmt_points, render_table


class TestFmtPoints:
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


class TestRenderTable:
    def test_returns_empty_list_for_no_rows(self):
        assert render_table(("A", "B"), []) == []

    def test_basic_two_column_table(self):
        headers = ("Name", "Pts")
        rows = [("Alice", "10"), ("Bob", "5")]
        lines = render_table(headers, rows)

        assert len(lines) == 4  # header + separator + 2 data rows
        # Header line contains both headers
        assert "Name" in lines[0]
        assert "Pts" in lines[0]
        # Separator is all dashes
        assert set(lines[1]) == {"-"}
        # Data rows contain the values
        assert "Alice" in lines[2]
        assert "10" in lines[2]
        assert "Bob" in lines[3]
        assert "5" in lines[3]

    def test_columns_sized_to_widest_value(self):
        headers = ("X",)
        rows = [("short",), ("a much longer value",)]
        lines = render_table(headers, rows)

        # The header line should be at least as wide as the longest data value
        assert len(lines[0]) >= len("a much longer value")

    def test_last_column_has_no_trailing_padding(self):
        headers = ("A", "B")
        rows = [("1", "2")]
        lines = render_table(headers, rows)

        # Last column value should not have trailing spaces
        assert not lines[2].endswith(" ")

    def test_separator_matches_total_width(self):
        headers = ("Col1", "Col2", "Col3")
        rows = [("a", "bb", "ccc")]
        lines = render_table(headers, rows)

        header_len = len(lines[0])
        separator_len = len(lines[1])
        assert separator_len == header_len

    def test_header_wider_than_data(self):
        headers = ("VeryLongHeader",)
        rows = [("x",)]
        lines = render_table(headers, rows)

        assert len(lines[0]) >= len("VeryLongHeader")

    def test_single_row(self):
        headers = ("Pos", "Driver")
        rows = [("1", "Verstappen")]
        lines = render_table(headers, rows)

        assert len(lines) == 3
        assert "Verstappen" in lines[2]

    def test_many_columns(self):
        headers = ("A", "B", "C", "D", "E")
        rows = [("1", "2", "3", "4", "5")]
        lines = render_table(headers, rows)

        assert len(lines) == 3
        for val in ("1", "2", "3", "4", "5"):
            assert val in lines[2]


class TestEchoTable:
    def test_echoes_title_and_table(self):
        @click.command()
        def cmd():
            print_table(
                "My Title",
                ("Name", "Score"),
                [("Alice", "10"), ("Bob", "5")],
            )

        runner = CliRunner()
        result = runner.invoke(cmd)

        assert result.exit_code == 0
        assert "My Title" in result.output
        assert "Name" in result.output
        assert "Alice" in result.output
        assert "---" in result.output

    def test_echoes_nothing_for_empty_rows(self):
        @click.command()
        def cmd():
            print_table("Title", ("A",), [])

        runner = CliRunner()
        result = runner.invoke(cmd)

        assert result.exit_code == 0
        assert "Title" in result.output
        # No table lines beyond the title
        lines = result.output.strip().split("\n")
        assert len(lines) == 1
