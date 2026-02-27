# f1

A CLI tool for viewing Formula 1 season schedules, powered by [Fast-F1](https://github.com/theOehrly/Fast-F1).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Installation

```shell
git clone https://github.com/benmatselby/f1.git
cd f1
uv sync
```

## Usage

```shell
# Show the 2025 season schedule
uv run f1 season 2025

# Include pre-season testing events
uv run f1 season 2025 --include-testing

# View an older season
uv run f1 season 2019
```

Race times are displayed in your machine's local timezone.

### Example output

```
Formula 1 2025 Season

Rnd  Event                      Location                          Date & Time (GMT)
-----------------------------------------------------------------------------------
1    Australian Grand Prix      Melbourne, Australia              2025-03-16  04:00
2    Chinese Grand Prix         Shanghai, China                   2025-03-23  07:00
3    Japanese Grand Prix        Suzuka, Japan                     2025-04-06  05:00
...
24   Abu Dhabi Grand Prix       Yas Island, United Arab Emirates  2025-12-07  13:00

Total events: 24
```

## Data

Schedule data is provided by the [Fast-F1](https://github.com/theOehrly/Fast-F1) library. Full session times are available from the 2018 season onwards. Older seasons (back to 1950) are supported via the Ergast API fallback, but only race dates are available (no session times).
