"""Download and clean DWD daily climate data for Weihenstephan (station 05404)."""

import re
import urllib.request
from pathlib import Path

DWD_URL = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


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


if __name__ == "__main__":
    download_station_zip()