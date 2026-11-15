
import pandas as pd
import numpy as np

# ==========================================
# 1. LOAD NASA RADIATION DATA
# ==========================================

df = pd.read_csv("nasa_radiation.csv")

TIME_COL = "timestamp"
ID_COL = "instrument_id"
RATE_COL = "absorbed_dose_rate"

# Optional measurement uncertainty column.
# Add this column to your CSV if calibration data provides it.
UNCERTAINTY_COL = "absorbed_dose_rate_uncertainty"

MAX_GAP_SECONDS = 300

# Assumes radiation rate is measured in µGy/hour.
RATE_TO_DOSE_FACTOR = 1 / 3600


# ==========================================
# 2. DATA PREPARATION
# ==========================================

df[TIME_COL] = pd.to_datetime(
    df[TIME_COL], errors="coerce"
)

df[RATE_COL] = pd.to_numeric(
    df[RATE_COL], errors="coerce"
)

has_uncertainty = UNCERTAINTY_COL in df.columns

if has_uncertainty:
    df[UNCERTAINTY_COL] = pd.to_numeric(
        df[UNCERTAINTY_COL], errors="coerce"
    )

df = df.dropna(
    subset=[TIME_COL, ID_COL, RATE_COL]
)

df = df.sort_values(
    [ID_COL, TIME_COL]
)


# ==========================================
# 3. UNCERTAINTY CALCULATION
# ==========================================

reports = []

for instrument, group in df.groupby(ID_COL):

    group = group.reset_index(drop=True)

    n = len(group)

    coefficients = np.zeros(n)

    total_dose = 0.0
    valid_time = 0.0
    total_time = 0.0

    valid_intervals = 0
    excluded_intervals = 0

    # Process consecutive readings
    for i in range(n - 1):

        r1 = group.loc[i, RATE_COL]
        r2 = group.loc[i + 1, RATE_COL]

        dt = (
            group.loc[i + 1, TIME_COL]
            - group.loc[i, TIME_COL]
        ).total_seconds()

        if dt > 0:
            total_time += dt

        # Exclude invalid intervals and long gaps
        if (
            dt <= 0
            or dt > MAX_GAP_SECONDS
            or r1 < 0
            or r2 < 0
        ):

            excluded_intervals += 1
            continue

        # Trapezoidal integration
        factor = (
            dt * RATE_TO_DOSE_FACTOR / 2
        )

        dose = factor * (r1 + r2)

        total_dose += dose

        # Coefficients for uncertainty propagation
        coefficients[i] += factor
        coefficients[i + 1] += factor

        valid_time += dt
        valid_intervals += 1


    # ======================================
    # 4. MEASUREMENT UNCERTAINTY
    # ======================================

    dose_uncertainty = np.nan
    relative_uncertainty = np.nan

    lower_95 = np.nan
    upper_95 = np.nan

    uncertainty_status = "Not available"

    if has_uncertainty:

        u = group[UNCERTAINTY_COL].to_numpy()

        if (
            np.all(np.isfinite(u))
            and np.all(u >= 0)
        ):

            # Independent measurement errors
            dose_uncertainty = np.sqrt(
                np.sum((coefficients * u) ** 2)
            )

            if total_dose > 0:

                relative_uncertainty = (
                    dose_uncertainty / total_dose
                ) * 100

            # Approximate 95% uncertainty interval
            lower_95 = (
                total_dose - 2 * dose_uncertainty
            )

            upper_95 = (
                total_dose + 2 * dose_uncertainty
            )

            uncertainty_status = "Calculated"

        else:
            uncertainty_status = (
                "Missing or invalid uncertainty values"
            )


    # ======================================
    # 5. DATA COVERAGE
    # ======================================

    if total_time > 0:

        coverage = (
            valid_time / total_time
        ) * 100

    else:
        coverage = np.nan


    # ======================================
    # 6. STORE RESULTS
    # ======================================

    reports.append({

        "instrument_id": instrument,

        "cumulative_dose": total_dose,

        "measurement_uncertainty": dose_uncertainty,

        "relative_uncertainty_percent":
            relative_uncertainty,

        "lower_95": lower_95,

        "upper_95": upper_95,

        "valid_intervals": valid_intervals,

        "excluded_intervals": excluded_intervals,

        "data_coverage_percent": coverage,

        "uncertainty_status": uncertainty_status

    })


# ==========================================
# 7. GENERATE FINAL REPORT
# ==========================================

report = pd.DataFrame(reports)

report.to_csv(
    "uncertainty_report.csv",
    index=False
)

print("\n========== UNCERTAINTY REPORT ==========")

print(report.to_string(index=False))

print("\nTotal instruments:", len(report))

print("\nReport saved as uncertainty_report.csv")

print("\n========== PROCESS COMPLETED ==========")
