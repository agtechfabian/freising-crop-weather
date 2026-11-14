# Freising Crop-Season Weather Toolkit

**Question:** How have frost, heat and drought risk for winter wheat in Freising changed since 1990?

**Who cares:** Wheat farmers and advisers around Freising deciding on sowing dates, variety choice and irrigation, and anyone asking how climate change is already showing up in Bavarian fields.

## Result

![Four winter wheat weather indicators per season, 1990 to 2025, with a 10-season mean](results/indicators_over_time.png)

Between 1991–2000 and 2016–2025, the winter wheat season at Weihenstephan became about 16% warmer, June days above 30 °C rose from 0.6 to 2.1 per season, and the longest April to June dry spell grew from 11.7 to 15.9 days. Late frost days did not fall (2.3 vs 2.9, driven mostly by the cold April of 2021), and because the crop now reaches its frost-sensitive stages earlier, each spring frost may do more harm.

| Indicator (season average)                | 1991–2000 | 2016–2025 | Change                               |
| :---------------------------------------- | :-------: | :-------: | :----------------------------------- |
| Growing degree days, Oct to Jul (°C days) |   2287    |   2649    | +362 (+16%)                          |
| Late frost days, Apr to May (min ≤ −2 °C) |    2.3    |    2.9    | +0.6 (≈ flat without 2021)           |
| Heat days, June (max > 30 °C)             |    0.6    |    2.1    | +1.5 days                            |
| Longest dry spell, Apr to Jun (days)      |   11.7    |   15.9    | +4.2 days (9 seasons in late decade) |

Full numbers: `results/decade_comparison.csv` and `results/season_indicators.csv`.

## Bavaria-wide (new in v0.2)

The same pipeline now runs on **68 long-record DWD stations across Bavaria**. A station gets a change value for an indicator only if it has at least 7 seasons with a value in each decade, which gives 54 to 57 stations per indicator.

- **The warming is everywhere.** Growing degree days rose at all 56 stations with data (median +308 °C days).
- **Heat at flowering rose most in the low, warm valleys of Franconia and the Danube.** June heat days rose at 55 of 57 stations (median +1.6). The biggest rises were Möhrendorf-Kleinseebach near Erlangen (+4.7), Kitzingen (+4.2, from 2.9 to 7.1 days), Kahl am Main (+4.1) and Regensburg (+3.4). High stations barely changed (Großer Arber and Zugspitze: 0), and the lower the station, the bigger the rise (correlation with elevation −0.5).
- **Spring drought grew most from Lower Franconia through the Altmühl valley.** The longest April to June dry spell grew at 49 of 54 stations (median +2.4 days). The biggest rises were Weißenburg-Emetzheim (+7.9), Altomünster-Pipinsried (+7.4), Bad Königshofen (+7.2) and Eichstätt-Landershofen (+6.8). It shrank slightly at a few stations near the Alps.
- **The heat and drought hotspots are mostly different places.** Only Kitzingen and Nürnberg-Netzstall are in both top 10s.
- **Freising sits in the middle for heat (rank 32 of 57) and in the upper third for drought (rank 14 of 54).**

Full numbers: `results/bavaria_change.csv` (one row per station, with coordinates). A QGIS map of these changes comes in v1.0.

## Data

- **Source:** Deutscher Wetterdienst (DWD), Climate Data Center, daily climate observations (KL), station 05404 Weihenstephan-Dürnast, Freising.
- **Licence:** Open data under the DWD terms of use (CC BY 4.0). Source: Deutscher Wetterdienst.
- **Bavaria:** every DWD daily (KL) station in Bayern with a record from before 1 Oct 1990 to after 31 Jul 2025 (68 stations, list in `results/bavaria_stations.csv`).
- **Downloaded:** Weihenstephan on 2026-11-12, the Bavarian stations on 2026-11-14. The raw data is not stored in this repository; the scripts fetch it.

## Method

1. Download the station's daily record from DWD and clean it: readable column names, missing values (`−999`) turned into empty cells (`src/get_data.py`).
2. Split the record into wheat seasons named by harvest year: season 2024 runs from 1 Oct 2023 to 31 Jul 2024.
3. Calculate four indicators per season (`src/indicators.py`, thresholds in `src/config.py`): growing degree days above 0 °C; late frost days in April and May with a minimum at or below −2 °C; June heat days above 30 °C; the longest run of days under 1 mm of rain from April to June.
4. Leave a season out of an indicator if any day in its window is missing, so a gap never looks like "no frost" or "no rain".
5. Plot every season with a 10-season rolling mean, and compare the averages of 1991–2000 and 2016–2025 (`src/analyse.py`).
6. For Bavaria: list the long-record stations (`src/stations.py`), download and gap-check each one (`src/bavaria.py`), then run steps 2 to 5 on every station and keep an indicator's change only where both decades have at least 7 seasons (`src/bavaria_indicators.py`). Downloads retry automatically when the DWD server drops the connection.

## Limitations

- **Calendar, not crop stage.** The windows are fixed dates. In warmer years the crop reaches stem elongation and flowering earlier, which these indicators can't see.
- **Station gap.** DWD has no data for this station from 1 Jan 2005 to 7 Nov 2008, so seasons 2005 to 2008 are missing.
- **Point stations.** Each station stands for its surroundings, not for every field. Bavaria has 68 long-record stations, so whole regions rest on one or two of them.
- **Missing values.** Three stations never measured any of the four values and drop out. Others lose seasons to gaps, which is why each indicator has a different number of stations.
- **Ten seasons are few.** One extreme year moves a decade average a lot (2021 for frost). The changes are described, not tested for statistical significance.
- **Weather risk is not yield.** This shows how often stressful weather happened, not how much yield it cost.

## How to reproduce it

After making and activating a virtual environment (`python -m venv .venv`, then `.venv\Scripts\activate` on Windows):

```bash
pip install -r requirements.txt
python src/get_data.py
python src/analyse.py
```

For the Bavaria-wide results (downloads about 70 stations, takes 10 to 20 minutes the first time):

```bash
python src/stations.py
python src/bavaria.py
python src/bavaria_indicators.py
```

The results appear in `results/`. Run `pytest` to check the indicator functions (7 tests).

## Done when

- [x] Daily DWD data for Weihenstephan downloaded and cleaned (1990 to today)
- [x] Frost, heat and drought indicators defined for winter wheat (fixed calendar windows for now)
- [x] Trends calculated and plotted for each indicator
- [x] Results summarised in plain language for a farmer
- [x] Code reproducible: anyone can run it from requirements.txt

- [x] Same analysis for 68 stations across Bavaria (v0.2)

**What comes next (v1.0):** map the Bavarian changes in QGIS, and turn the analysis into a command-line tool any station can be run through.

## Licence

Code: MIT, see [LICENSE](LICENSE). Data: © Deutscher Wetterdienst, CC BY 4.0.
