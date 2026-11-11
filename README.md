# Freising Crop-Season Weather Toolkit

**Question:** How have frost, heat and drought risk for winter wheat in Freising changed since 1990?

Data: German Weather Service (DWD) daily observations, Weihenstephan station.

## Done when

- [x] Daily DWD data for Weihenstephan downloaded and cleaned (1990 to today)
- [ ] Frost, heat and drought indicators defined for winter wheat growth stages
- [ ] Trends calculated and plotted for each indicator
- [ ] Results summarised in plain language for a farmer
- [x] Code reproducible: anyone can run it from requirements.txt

## How to get the data

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src/get_data.py
```

This downloads the DWD daily climate record for Weihenstephan-Dürnast (station 05404) into `data/raw/` and saves a cleaned table to `data/processed/dwd_05404_daily_clean.csv`.
