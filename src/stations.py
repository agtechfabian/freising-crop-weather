"""List the Bavarian DWD weather stations with a long daily record.

Run from the repository folder:  python src/stations.py

It downloads the DWD station list for daily climate data (KL), keeps the
stations in Bayern whose record covers every wheat season we analyse
(season 1991 starts 1 Oct 1990, season 2025 ends 31 Jul 2025), and saves
them to results/bavaria_stations.csv.

A long record on paper does not mean a complete record: Weihenstephan
(05404) is listed from 1936 but has a gap from 2005 to 2008. The gaps are
checked in the next step, when each station's data is downloaded.
"""

import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

DWD_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/"
STATION_LIST_FILE = "KL_Tageswerte_Beschreibung_Stationen.txt"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

STATE = "Bayern"
RECORD_START_BY = pd.Timestamp("1990-10-01")  # first day of season 1991
RECORD_END_AFTER = pd.Timestamp("2025-07-31")  # last day of season 2025


def fetch_with_retry(url, attempts=4, wait_s=5):
    """Download a URL and return its bytes, retrying if the connection drops.

    The DWD server sometimes cuts the connection (WinError 10054 on Windows).
    Instead of crashing, wait a little and try again: 5 s, then 10 s, then 20 s.
    """
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except (ConnectionError, TimeoutError, urllib.error.URLError) as error:
            if attempt == attempts:
                raise  # give up and show the real error
            print(f"  Connection problem ({error}). Retry {attempt} of {attempts - 1} in {wait_s} s...")
            time.sleep(wait_s)
            wait_s *= 2


def parse_station_list(raw_bytes):
    """Turn the DWD station list text into a DataFrame, one row per station.

    The file is a fixed-width text table. Station names can contain spaces
    ("Hohenpeißenberg" is one word, "Weihenstephan-Dürnast" too, but
    "Bad Kissingen" is two), so we can't simply split every line on spaces.
    Instead we take the first six values from the left (they never contain
    spaces) and the state (and the "Abgabe" column, if present) from the
    right. Whatever is left in the middle is the station name.
    """
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")  # older DWD files use this encoding

    lines = text.splitlines()
    has_abgabe = "Abgabe" in lines[0]

    rows = []
    for line in lines[2:]:  # line 0 is the header, line 1 is a row of dashes
        parts = line.split()
        if len(parts) < 8:
            continue  # skip empty or broken lines
        if has_abgabe:
            parts = parts[:-1]  # drop the "Abgabe" value (e.g. "Frei")
        rows.append({
            "station_id": parts[0],
            "from_date": parts[1],
            "to_date": parts[2],
            "elevation_m": float(parts[3]),
            "lat": float(parts[4]),
            "lon": float(parts[5]),
            "name": " ".join(parts[6:-1]),
            "state": parts[-1],
        })

    stations = pd.DataFrame(rows)
    stations["from_date"] = pd.to_datetime(stations["from_date"], format="%Y%m%d")
    stations["to_date"] = pd.to_datetime(stations["to_date"], format="%Y%m%d")
    return stations


def long_record_stations(stations):
    """Keep the Bavarian stations whose record spans season 1991 to season 2025."""
    keep = (
        (stations["state"] == STATE)
        & (stations["from_date"] <= RECORD_START_BY)
        & (stations["to_date"] >= RECORD_END_AFTER)
    )
    selected = stations[keep].copy()
    selected["record_years"] = ((selected["to_date"] - selected["from_date"]).dt.days / 365.25).round(1)
    return selected.sort_values("name").reset_index(drop=True)


if __name__ == "__main__":
    print(f"Downloading the station list from {DWD_URL}")
    raw = fetch_with_retry(DWD_URL + STATION_LIST_FILE)

    stations = parse_station_list(raw)
    print(f"Stations in the whole list: {len(stations)}")
    print(f"Stations in {STATE}: {(stations['state'] == STATE).sum()}")

    bavaria = long_record_stations(stations)
    print(f"{STATE} stations with a record from at least {RECORD_START_BY.date()} "
          f"to at least {RECORD_END_AFTER.date()}: {len(bavaria)}")

    # Sanity check: our home station must be in the list
    if "05404" in set(bavaria["station_id"]):
        print("Check: Weihenstephan-Dürnast (05404) is in the list. Good.")
    else:
        print("WARNING: 05404 is missing. Something is wrong with the filter, tell Claude.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    target = RESULTS_DIR / "bavaria_stations.csv"
    bavaria.to_csv(target, index=False, encoding="utf-8")
    print(f"Saved {len(bavaria)} stations to {target}")
    print()
    print(bavaria[["station_id", "name", "elevation_m", "from_date", "record_years"]].to_string(index=False))
