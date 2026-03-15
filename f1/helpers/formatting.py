"""Shared formatting utilities for CLI output."""

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
