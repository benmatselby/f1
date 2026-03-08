from datetime import datetime, timezone

import pandas as pd


def get_race_utc(event: pd.Series) -> datetime | None:
    for n in range(1, 6):
        if event.get(f"Session{n}") == "Race":
            utc = event.get(f"Session{n}DateUtc")

            if pd.notna(utc):
                return utc.to_pydatetime().replace(tzinfo=timezone.utc)

            return None

    return None
