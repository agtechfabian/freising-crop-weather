"""Download and clean DWD daily climate data for Weihenstephan (station 05404)."""

import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DWD_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"  # NEW (S4)

# DWD column codes -> readable names
COLUMN_NAMES = {
    "MESS_DATUM": "date",
    "TMK": "t_mean",
    "TXK": "t_max",
    "TNK": "t_min",
    "TGK": "t_ground_min",
    "RSK": "precip_mm",
    "SDK": "sunshine_h",
    "SHK_TAG": "snow_cm",
    "UPM": "humidity_pct",
}


def download_station_zip(station_id="05404"):
    """Find the station's zip on the DWD server, save it in data/raw/ and return its path."""
    with urllib.request.urlopen(DWD_URL) as response:
        listing = response.read().decode("utf-8")

    pattern = rf"tageswerte_KL_{station_id}_\d{{8}}_\d{{8}}_hist\.zip"
    match = re.search(pattern, listing)
    if match is None:
        raise ValueError(f"No zip file found for station {station_id}")
    filename = match.group(0)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    target = RAW_DIR / filename
    urllib.request.urlretrieve(DWD_URL + filename, target)
    print(f"Downloaded {filename} to {target}")
    return target


def load_and_clean(zip_path):
    """Read the daily data file inside the zip and return a clean DataFrame."""
    with zipfile.ZipFile(zip_path) as z:
        data_files = [name for name in z.namelist() if name.startswith("produkt_klima_tag_")]
        if not data_files:
            raise ValueError(f"No data file found in {zip_path}")
        with z.open(data_files[0]) as f:
            df = pd.read_csv(f, sep=";", skipinitialspace=True)

    df = df.rename(columns=COLUMN_NAMES)
    df = df.drop(columns=["eor"])
    df = df.replace(-999, np.nan)
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    return df


# NEW (S4)
def save_processed(df, station_id="05404"):
    """Save the clean DataFrame as a CSV in data/processed/ and return its path."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    target = PROCESSED_DIR / f"dwd_{station_id}_daily_clean.csv"
    df.to_csv(target, index=False)
    print(f"Saved {len(df)} rows to {target}")
    return target


if __name__ == "__main__":
    zip_path = download_station_zip()
    df = load_and_clean(zip_path)
    save_processed(df)  # NEW (S4)