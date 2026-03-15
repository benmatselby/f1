"""Shared formatting utilities for CLI output."""

import click
import pandas as pd


def fmt_points(value) -> str:
    """Format points, showing integers where possible.

    Returns "0" for NaN/missing values.  Whole-number floats like 25.0 are
    displayed without decimals ("25"), while fractional values like 12.5 are
    kept as-is.
    """
    if pd.notna(value):
        pts = float(value)
        return str(int(pts)) if pts == int(pts) else str(pts)

    return "0"


def render_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    """Build a list of formatted table lines from *headers* and *rows*.

    Each column is left-aligned and padded to fit the widest value (header or
    data) plus two spaces of gutter.  The last column omits trailing padding.

    Returns a list of strings: the header row, a dash separator sized to the
    total table width, and one line per data row.  The caller is responsible
    for printing a title before and a summary after.
    """
    if not rows:
        return []

    col_widths: list[int] = []
    for i, header in enumerate(headers):
        max_data = max((len(r[i]) for r in rows), default=0)
        col_widths.append(max(len(header), max_data) + 2)

    # Last column doesn't need trailing padding.
    col_widths[-1] = max(len(headers[-1]), max(len(r[-1]) for r in rows))

    total_width = sum(col_widths)

    lines: list[str] = []
    lines.append("".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)))
    lines.append("-" * total_width)

    for row in rows:
        lines.append(
            "".join(
                f"{val:<{col_widths[i]}}" if i < len(row) - 1 else f"{val}"
                for i, val in enumerate(row)
            )
        )

    return lines


def print_table(
    title: str, headers: tuple[str, ...], rows: list[tuple[str, ...]]
) -> None:
    """Render and print a formatted table with a title.

    Convenience wrapper around :func:`render_table` that echoes the title
    followed by the table lines via :func:`click.echo`.
    """
    click.echo(f"\n{title}\n")
    for line in render_table(headers, rows):
        click.echo(line)
