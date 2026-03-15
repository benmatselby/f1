"""Show the driver championship standings for a given F1 season."""

import click
from fastf1.ergast import Ergast

from f1.helpers.formatting import fmt_points
from f1.helpers.formatting import print_table


@click.command()
@click.argument("year", type=int)
def constructors(year: int):
    """Show the constructors championship standings for a given F1 season.

    YEAR is the championship year (e.g. 2024).
    """
    try:
        ergast = Ergast()
        response = ergast.get_constructor_standings(season=year)
    except Exception as e:
        raise click.ClickException(
            f"Failed to fetch championship standings for {year}: {e}"
        ) from e

    standings = getattr(response, "content", [])
    if not standings:
        raise click.ClickException(f"No championship data found for {year}.")

    rows = []
    for _, constructor in standings[0].iterrows():
        pos = str(int(constructor["position"]))
        team = constructor["constructorName"]
        nationality = constructor["constructorNationality"]
        wins = str(int(constructor["wins"]))
        points = fmt_points(constructor["points"])
        row = [pos, team, nationality, points, wins]
        rows.append(row)

    headers = ("Pos", "Team", "Nationality", "Pts", "Wins")

    print_table(f"Formula 1 {year} Constructors Championship", headers, rows)

    click.echo(f"\nTotal constructors: {len(rows)}")
