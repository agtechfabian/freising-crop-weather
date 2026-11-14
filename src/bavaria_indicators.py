"""Work out how wheat weather risk changed at every Bavarian station.

Run from the repository folder:  python src/bavaria_indicators.py

For every station that downloaded fine in bavaria.py, it:
  1. calculates the four indicators for every season 1991-2025, with the same
     build_season_table() you wrote for Freising,
  2. compares 1991-2000 with 2016-2025 using your compare_decades(),
  3. keeps a change only if BOTH decades have at least 7 seasons with a value
     for THAT indicator. Each indicator is judged on its own: a missing rain
     day in May no longer throws away the station's heat days in June.

It saves one row per station to results/bavaria_change.csv, with lat/lon
so QGIS can put every station on a map.
"""

import pandas as pd

from analyse import INDICATORS, RESULTS_DIR, build_season_table, compare_decades
from get_data import PROCESSED_DIR

MIN_SEASONS = 7  # seasons with a value needed in each decade, as in bavaria.py
WEATHER_COLUMNS = ["t_mean", "t_min", "t_max", "precip_mm"]


def empty_columns(df):
    """Names of the weather columns that have no value at all since 1990.

    Some stations never measured one of the four values (for example no
    temperature, or no rain). That explains a station with 0 complete seasons.
    """
    recent = df[df["date"] >= "1990-01-01"]
    return [col for col in WEATHER_COLUMNS if recent[col].isna().all()]


def station_change(df):
    """One dict per station: early mean, late mean and change for each indicator."""
    comparison = compare_decades(build_season_table(df))
    row = {}
    for ind in INDICATORS:
        early, late, n_early, n_late, change, _ = comparison.loc[ind]
        enough = n_early >= MIN_SEASONS and n_late >= MIN_SEASONS
        row[f"{ind}_early"] = early if enough else None
        row[f"{ind}_late"] = late if enough else None
        row[f"{ind}_change"] = change if enough else None
        row[f"{ind}_seasons"] = f"{int(n_early)}+{int(n_late)}"  # e.g. "10+9" = seasons used early+late
    return row


if __name__ == "__main__":
    coverage = pd.read_csv(RESULTS_DIR / "bavaria_coverage.csv", dtype={"station_id": str})
    ok = coverage[coverage["status"] == "ok"]

    rows = []
    for i, station in enumerate(ok.itertuples(), start=1):
        sid = station.station_id
        print(f"[{i}/{len(ok)}] {sid} {station.name}")
        df = pd.read_csv(PROCESSED_DIR / f"dwd_{sid}_daily_clean.csv", parse_dates=["date"])
        rows.append({
            "station_id": sid,
            "name": station.name,
            "lat": station.lat,
            "lon": station.lon,
            "elevation_m": station.elevation_m,
            "empty_columns": " ".join(empty_columns(df)),
            **station_change(df),
        })

    table = pd.DataFrame(rows)
    target = RESULTS_DIR / "bavaria_change.csv"
    table.to_csv(target, index=False, encoding="utf-8")
    print(f"\nSaved {len(table)} stations to {target}")

    # How many stations have a usable change, per indicator
    print("\nStations with a change value (at least 7 seasons in both decades):")
    for ind in INDICATORS:
        print(f"  {ind:<11} {table[f'{ind}_change'].notna().sum()} of {len(table)}")

    # Stations missing a whole weather value
    gaps = table[table["empty_columns"] != ""]
    if len(gaps):
        print("\nStations that never measured one of the values since 1990:")
        print(gaps[["station_id", "name", "empty_columns"]].to_string(index=False))

    # First look at the answer: where did heat and drought rise the most?
    show = ["station_id", "name", "elevation_m"]
    for ind, label in [("heat_days", "heat days"), ("dry_spell", "longest dry spell")]:
        col = f"{ind}_change"
        top = table.dropna(subset=[col]).sort_values(col, ascending=False).head(10)
        print(f"\nTop 10 stations: biggest rise in {label} (2016-2025 minus 1991-2000)")
        print(top[show + [f"{ind}_early", f"{ind}_late", col]].to_string(index=False))

    # Freising as the anchor: these numbers must match your decade_comparison.csv
    home = table[table["station_id"] == "05404"]
    if len(home):
        print("\nCheck: Weihenstephan (05404) should match results/decade_comparison.csv")
        print(home[[f"{ind}_change" for ind in INDICATORS]].to_string(index=False))
