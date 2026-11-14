"""Download every Bavarian station from results/bavaria_stations.csv and check its gaps.

Run from the repository folder:  python src/bavaria.py

For each station it:
  1. downloads the station's daily zip from DWD into data/raw/ (skipped if
     the zip is already there, so a rerun after a crash only fetches what's missing),
  2. cleans it with the same load_and_clean() you wrote for Freising and saves
     it to data/processed/dwd_<id>_daily_clean.csv,
  3. counts the missing days in every wheat season from 1991 to 2025.

It saves one row per station to results/bavaria_coverage.csv and tells you
which stations have enough complete seasons to compare 1991-2000 with 2016-2025.
"""

import re
import time

import pandas as pd

from analyse import RESULTS_DIR, missing_days
from get_data import DWD_URL, RAW_DIR, load_and_clean, save_processed
from stations import fetch_with_retry

FIRST_SEASON = 1991
LAST_SEASON = 2025
EARLY = (1991, 2000)
LATE = (2016, 2025)
MIN_COMPLETE_PER_DECADE = 7  # same rule as the 10-season rolling mean in analyse.py


def find_zip_names(station_ids):
    """Read the DWD folder listing once and return {station_id: zip file name}."""
    listing = fetch_with_retry(DWD_URL).decode("utf-8")
    names = {}
    for station_id in station_ids:
        match = re.search(rf"tageswerte_KL_{station_id}_\d{{8}}_\d{{8}}_hist\.zip", listing)
        if match:
            names[station_id] = match.group(0)
    return names


def get_station_zip(station_id, zip_name):
    """Return the path of the station's zip in data/raw/, downloading it only if needed."""
    target = RAW_DIR / zip_name
    if target.exists():
        return target, "already here"
    target.write_bytes(fetch_with_retry(DWD_URL + zip_name))
    time.sleep(1)  # a short pause between downloads, to be polite to the DWD server
    return target, "downloaded"


def coverage(df):
    """Count complete seasons (no missing day) overall and in each comparison decade."""
    missing = {year: missing_days(df, year) for year in range(FIRST_SEASON, LAST_SEASON + 1)}
    complete = [year for year, n in missing.items() if n == 0]
    return {
        "complete_seasons": len(complete),
        "complete_early": sum(EARLY[0] <= y <= EARLY[1] for y in complete),
        "complete_late": sum(LATE[0] <= y <= LATE[1] for y in complete),
        "total_missing_days": sum(missing.values()),
    }


if __name__ == "__main__":
    stations = pd.read_csv(RESULTS_DIR / "bavaria_stations.csv", dtype={"station_id": str})
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading the DWD folder listing for {len(stations)} stations...")
    zip_names = find_zip_names(stations["station_id"])

    rows = []
    for i, station in enumerate(stations.itertuples(), start=1):
        sid, name = station.station_id, station.name
        print(f"[{i}/{len(stations)}] {sid} {name}")

        if sid not in zip_names:
            print("    no zip on the DWD server, skipped")
            rows.append({"station_id": sid, "name": name, "status": "no zip"})
            continue

        try:
            zip_path, how = get_station_zip(sid, zip_names[sid])
            df = load_and_clean(zip_path)
        except Exception as error:  # one broken station must not stop the other 70
            print(f"    FAILED ({error})")
            rows.append({"station_id": sid, "name": name, "status": f"failed: {error}"})
            continue

        save_processed(df, sid)  # prints its own "Saved ..." line
        result = coverage(df)
        print(f"    {how}, {result['complete_seasons']} of {LAST_SEASON - FIRST_SEASON + 1} seasons complete")
        rows.append({"station_id": sid, "name": name, "status": "ok", **result})

    table = pd.DataFrame(rows).merge(
        stations[["station_id", "lat", "lon", "elevation_m"]], on="station_id"
    )
    table["usable"] = (
        (table["status"] == "ok")
        & (table["complete_early"] >= MIN_COMPLETE_PER_DECADE)
        & (table["complete_late"] >= MIN_COMPLETE_PER_DECADE)
    )
    target = RESULTS_DIR / "bavaria_coverage.csv"
    table.to_csv(target, index=False, encoding="utf-8")

    print()
    print(f"Saved {len(table)} stations to {target}")
    print(f"Usable (at least {MIN_COMPLETE_PER_DECADE} complete seasons in both "
          f"{EARLY[0]}-{EARLY[1]} and {LATE[0]}-{LATE[1]}): {table['usable'].sum()} of {len(table)}")
    print()
    print("Stations that did NOT make it, and why:")
    not_usable = table[~table["usable"]]
    cols = ["station_id", "name", "status", "complete_early", "complete_late"]
    print(not_usable[cols].to_string(index=False) if len(not_usable) else "  none")
