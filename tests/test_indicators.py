"""Tests for the wheat stress indicators, using tiny made-up weather data.

Each test builds a fake weather record where we already know the right
answer, then checks that the function gives exactly that answer.
"""

import math

import pandas as pd

from indicators import growing_degree_days, heat_days, late_frost_days, longest_dry_spell


def make_weather(start, end, **columns):
    """Build a fake daily weather table from start to end, every day with the same values."""
    df = pd.DataFrame({"date": pd.date_range(start, end, freq="D")})
    for name, value in columns.items():
        df[name] = value
    return df


def set_value(df, dates, column, value):
    """Change one column on the given dates, to plant a frost, a hot day or a dry day."""
    df.loc[df["date"].isin(pd.to_datetime(dates)), column] = value


# --- growing_degree_days ----------------------------------------------

def test_gdd_adds_up_warm_days_and_ignores_cold_days():
    # Season 2024 = 1 Oct 2023 to 31 Jul 2024 = 305 days (2024 is a leap year).
    df = make_weather("2023-09-01", "2024-08-31", t_mean=2.0)
    cold_days = pd.date_range("2024-01-01", "2024-01-10")  # 10 days at -5 °C earn 0, not minus
    set_value(df, cold_days, "t_mean", -5.0)
    assert growing_degree_days(df, 2024) == (305 - 10) * 2.0


def test_gdd_returns_nan_when_a_day_is_missing():
    df = make_weather("2023-09-01", "2024-08-31", t_mean=2.0)
    df = df[df["date"] != "2024-03-15"]  # one day lost, like the station gap
    assert math.isnan(growing_degree_days(df, 2024))


# --- late_frost_days --------------------------------------------------

def test_late_frost_counts_only_april_may_at_or_below_threshold():
    df = make_weather("2024-01-01", "2024-12-31", t_min=5.0)
    set_value(df, ["2024-04-10"], "t_min", -2.0)  # exactly -2 °C: counts
    set_value(df, ["2024-05-20"], "t_min", -3.0)  # colder: counts
    set_value(df, ["2024-04-11"], "t_min", -1.9)  # not cold enough: no
    set_value(df, ["2024-03-31"], "t_min", -6.0)  # before the window: no
    assert late_frost_days(df, 2024) == 2


# --- heat_days ----------------------------------------------------------

def test_heat_days_counts_only_june_above_threshold():
    df = make_weather("2024-01-01", "2024-12-31", t_max=25.0)
    set_value(df, ["2024-06-16"], "t_max", 31.0)  # above 30 °C in June: counts
    set_value(df, ["2024-06-15"], "t_max", 30.0)  # exactly 30 °C: not above, no
    set_value(df, ["2024-07-01"], "t_max", 35.0)  # after the window: no
    assert heat_days(df, 2024) == 1


# --- longest_dry_spell --------------------------------------------------

def test_longest_dry_spell_finds_the_longest_run():
    df = make_weather("2024-01-01", "2024-12-31", precip_mm=5.0)
    set_value(df, pd.date_range("2024-04-01", "2024-04-05"), "precip_mm", 0.0)  # 5 dry days
    set_value(df, pd.date_range("2024-06-21", "2024-07-05"), "precip_mm", 0.0)  # 10 in the window, 5 after it
    assert longest_dry_spell(df, 2024) == 10


def test_one_mm_of_rain_breaks_a_dry_spell():
    df = make_weather("2024-01-01", "2024-12-31", precip_mm=5.0)
    set_value(df, pd.date_range("2024-05-01", "2024-05-09"), "precip_mm", 0.5)  # under 1 mm: dry
    set_value(df, ["2024-05-05"], "precip_mm", 1.0)  # exactly 1 mm: wet, splits it into 4 + 4
    assert longest_dry_spell(df, 2024) == 4


def test_longest_dry_spell_returns_nan_when_rain_is_missing():
    df = make_weather("2024-01-01", "2024-12-31", precip_mm=5.0)
    set_value(df, ["2024-05-15"], "precip_mm", float("nan"))
    assert math.isnan(longest_dry_spell(df, 2024))