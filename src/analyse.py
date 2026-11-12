"""Answer the project question: how have frost, heat and drought risk changed since 1990?

Run from the repository folder:  python src/analyse.py
It reads the clean data, works out the four indicators for every season,
and saves the results in results/.
"""

from pathlib import Path

import pandas as pd

import config
from get_data import PROCESSED_DIR
from indicators import (
    growing_degree_days,
    heat_days,
    late_frost_days,
    longest_dry_spell,
    season_window,
)

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
FIRST_SEASON = 1990
LAST_SEASON = 2025


def missing_days(df, harvest_year):
    """How many days of the season (Oct to Jul) lack any of the four weather values we use."""
    window, expected_days = season_window(df, harvest_year, config.SEASON_START, config.SEASON_END)
    complete_days = window[["t_mean", "t_min", "t_max", "precip_mm"]].notna().all(axis=1).sum()
    return int(expected_days - complete_days)


def build_season_table(df, first=FIRST_SEASON, last=LAST_SEASON):
    """One row per season with all four indicators, plus how many days are missing."""
    rows = []
    for year in range(first, last + 1):
        rows.append({
            "season": year,
            "gdd": growing_degree_days(df, year),
            "frost_days": late_frost_days(df, year),
            "heat_days": heat_days(df, year),
            "dry_spell": longest_dry_spell(df, year),
            "missing_days": missing_days(df, year),
        })
    return pd.DataFrame(rows).set_index("season")


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_DIR / "dwd_05404_daily_clean.csv", parse_dates=["date"])

    table = build_season_table(df)
    RESULTS_DIR.mkdir(exist_ok=True)
    table.to_csv(RESULTS_DIR / "season_indicators.csv")

    print(table.to_string())
    print(f"\nSaved {len(table)} seasons to {RESULTS_DIR / 'season_indicators.csv'}")