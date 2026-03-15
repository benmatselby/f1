"""Show the driver championship standings for a given F1 season."""

from collections import Counter

import click
from fastf1.ergast import Ergast

from f1.helpers.formatting import fmt_points
from f1.helpers.formatting import print_table


@click.command()
@click.argument("year", type=int)
def drivers(year: int):
    """Show the driver championship standings for a given F1 season.

    Displays drivers ranked by points with their team, wins, podiums, and
    points total.

    YEAR is the championship year (e.g. 2024).
    """
    try:
        ergast = Ergast()
        response = ergast.get_driver_standings(season=year)
    except Exception as e:
        raise click.ClickException(
            f"Failed to fetch championship standings for {year}: {e}"
        ) from e

    if not response.content:
        raise click.ClickException(f"No championship data found for {year}.")

    standings = response.content[0]
    if standings.empty:
        raise click.ClickException(f"No championship data found for {year}.")

    podium_counts = _get_podium_counts(ergast, year)

    rows: list[tuple[str, str, str, str, str, str]] = []
    for _, driver in standings.iterrows():
        pos = str(int(driver["position"]))
        name = f"{driver['givenName']} {driver['familyName']}"
        team = ", ".join(driver["constructorNames"])
        wins = str(int(driver["wins"]))
        podiums = str(podium_counts.get(driver["driverId"], 0))
        points = fmt_points(driver["points"])
        rows.append((pos, name, team, wins, podiums, points))

    headers = ("Pos", "Driver", "Team", "Wins", "Podiums", "Pts")
    print_table(f"Formula 1 {year} Driver Championship", headers, rows)

    click.echo(f"\nTotal drivers: {len(rows)}")


def _get_podium_counts(ergast, year: int) -> dict[str, int]:
    """Count podium finishes (P1-P3) per driver for the season."""
    counts: Counter[str] = Counter()
    schedule = ergast.get_race_schedule(season=year)
    total_rounds = len(schedule)

    for rnd in range(1, total_rounds + 1):
        try:
            results = ergast.get_race_results(season=year, round=rnd)
            if not results.content:
                continue
            df = results.content[0]
            top3 = df[df["position"] <= 3]
            for _, row in top3.iterrows():
                counts[row["driverId"]] += 1
        except Exception:
            continue

    return dict(counts)
