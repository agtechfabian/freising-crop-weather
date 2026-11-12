"""Wheat stress indicators for one season, using the thresholds in config.py."""

import pandas as pd

import config
from get_data import PROCESSED_DIR


def season_window(df, harvest_year, start, end):
    """Return the rows of df between two "MM-DD" dates of one season.

    If start comes later in the calendar than end (like "10-01" to "07-31"),
    the window starts in the year before the harvest year.
    """
    start_year = harvest_year - 1 if start > end else harvest_year
    start_date = pd.Timestamp(f"{start_year}-{start}")
    end_date = pd.Timestamp(f"{harvest_year}-{end}")
    expected_days = (end_date - start_date).days + 1

    window = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    return window, expected_days


def has_gaps(window, column, expected_days):
    """True if days are missing from the window or the column has empty values."""
    return len(window) < expected_days or window[column].isna().any()


def growing_degree_days(df, harvest_year):
    """Sum of daily mean temperature above the base temperature, sowing to harvest."""
    window, expected_days = season_window(df, harvest_year, config.SEASON_START, config.SEASON_END)
    if has_gaps(window, "t_mean", expected_days):
        return float("nan")
    daily_gdd = (window["t_mean"] - config.GDD_BASE_C).clip(lower=0)
    return round(float(daily_gdd.sum()), 1)


# NEW (S3)
def late_frost_days(df, harvest_year):
    """Number of days in the late-frost window with minimum air temperature at or below the threshold."""
    window, expected_days = season_window(df, harvest_year, config.FROST_START, config.FROST_END)
    if has_gaps(window, "t_min", expected_days):
        return float("nan")
    frost = window["t_min"] <= config.FROST_THRESHOLD_C
    return int(frost.sum())


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_DIR / "dwd_05404_daily_clean.csv", parse_dates=["date"])
    print("season  gdd  frost_days")  # NEW (S3)
    for year in [2004, 2006, 2020, 2021, 2022, 2023, 2024, 2025]:
        print(year, growing_degree_days(df, year), late_frost_days(df, year))  # NEW (S3)