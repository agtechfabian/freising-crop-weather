"""Wheat season dates and stress thresholds for Freising winter wheat.

Every number the indicator functions use lives here, so an assumption
can be changed in one place and everything rerun.
Dates are "MM-DD" text. A season is named by its harvest year:
season 2024 = 1 Oct 2023 to 31 Jul 2024.
"""

# --- Season -----------------------------------------------------------
SEASON_START = "10-01"  # winter wheat in Bavaria is mostly sown late Sept to mid Oct
SEASON_END = "07-31"    # harvest around Freising is usually finished by end of July

# --- Growing degree days ----------------------------------------------
GDD_BASE_C = 0.0  # wheat keeps developing slowly down to about 0 °C, the usual base for wheat

# --- Late frost -------------------------------------------------------
FROST_START = "04-01"     # from stem elongation the growing point is above ground and exposed
FROST_END = "05-31"       # after May, frost in Freising is very rare
FROST_THRESHOLD_C = -2.0  # air minimum at or below -2 °C can damage ears at booting and heading

# --- Heat around flowering --------------------------------------------
HEAT_START = "06-01"     # wheat around Freising usually flowers in early to mid June
HEAT_END = "06-30"       # covers flowering and the start of grain fill
HEAT_THRESHOLD_C = 30.0  # above about 30 °C at flowering, pollen fails and fewer grains set

# --- Drought ----------------------------------------------------------
DRY_START = "04-01"    # April to June is when wheat uses the most water
DRY_END = "06-30"
DRY_DAY_MAX_MM = 1.0   # under 1 mm of rain mostly evaporates, so the day counts as dry