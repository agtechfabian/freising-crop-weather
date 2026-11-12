"""Answer the project question: how have frost, heat and drought risk changed since 1990?

Run from the repository folder:  python src/analyse.py
It reads the clean data, works out the four indicators for every season,
and saves the results in results/.
"""

from pathlib import Path

import matplotlib.pyplot as plt  # NEW (S2)
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

# NEW (S2): what each indicator column means, for chart titles and axis labels
INDICATORS = {
    "gdd": ("Growing degree days (Oct to Jul)", "°C days"),
    "frost_days": (f"Late frost days (Apr to May, min ≤ {config.FROST_THRESHOLD_C} °C)", "days"),
    "heat_days": (f"Heat days (June, max > {config.HEAT_THRESHOLD_C} °C)", "days"),
    "dry_spell": ("Longest dry spell (Apr to Jun)", "days"),
}


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


# NEW (S2)
def plot_indicators(table, window=10):
    """Draw each indicator per season with its rolling mean, four panels in one figure."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, (column, (title, unit)) in zip(axes.flat, INDICATORS.items()):
        values = table[column]
        # min_periods=7: the mean still shows if up to 3 of the 10 seasons are missing
        rolling = values.rolling(window, min_periods=7).mean()
        # grey band behind each season with no value, so "missing" never looks like "zero"
        for year in values[values.isna()].index:
            ax.axvspan(year - 0.5, year + 0.5, color="#e6e6e6", linewidth=0)
        if column == "gdd":
            # dots, not bars: GDD never goes near zero, so bars would hide the change
            ax.plot(table.index, values, "o", color="#9db8d2", label="each season")
        else:
            ax.bar(table.index, values, color="#9db8d2", label="each season")
        ax.plot(table.index, rolling, color="#1f4e79", linewidth=2.5, label=f"{window}-season mean")
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(unit)
        ax.grid(axis="y", alpha=0.3)
    axes[0, 0].legend(loc="upper left")
    for ax in axes[1]:
        ax.set_xlabel("Season (harvest year)")
    fig.suptitle("Winter wheat weather risk at Weihenstephan, Freising (DWD station 05404)", fontsize=13)
    fig.text(0.5, 0.005, "Grey band = season left out because of missing data (station gap 2005 to 2008).",
             ha="center", fontsize=9, color="gray")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    target = RESULTS_DIR / "indicators_over_time.png"
    fig.savefig(target, dpi=150)
    plt.close(fig)
    return target


if __name__ == "__main__":
    df = pd.read_csv(PROCESSED_DIR / "dwd_05404_daily_clean.csv", parse_dates=["date"])

    table = build_season_table(df)
    RESULTS_DIR.mkdir(exist_ok=True)
    table.to_csv(RESULTS_DIR / "season_indicators.csv")

    print(table.to_string())
    print(f"\nSaved {len(table)} seasons to {RESULTS_DIR / 'season_indicators.csv'}")

    chart = plot_indicators(table)  # NEW (S2)
    print(f"Saved the chart to {chart}")  # NEW (S2)