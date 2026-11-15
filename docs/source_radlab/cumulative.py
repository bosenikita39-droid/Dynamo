
import pandas as pd
import numpy as np

# Load radiation data
df = pd.read_csv("nasa_radiation.csv")

# Configuration: change these names to match your CSV
TIME_COL = "timestamp"
ID_COL = "instrument_id"
RATE_COL = "absorbed_dose_rate"
# Maximum accepted interval (use the same threshold
# configured in your gap_detection.py)
MAX_GAP_SECONDS = 300

# Conversion for dose rate expressed in µGy/hour
RATE_TO_DOSE_FACTOR = 1 / 3600

df[TIME_COL] = pd.to_datetime(df[TIME_COL], errors="coerce")
df[RATE_COL] = pd.to_numeric(df[RATE_COL], errors="coerce")

df = df.dropna(subset=[TIME_COL, ID_COL, RATE_COL])
df = df.sort_values([ID_COL, TIME_COL])

intervals = []
summaries = []

for instrument, group in df.groupby(ID_COL):

    group = group.reset_index(drop=True)

    total_dose = 0.0
    valid_intervals = 0
    excluded_intervals = 0

    for i in range(len(group) - 1):

        t1 = group.loc[i, TIME_COL]
        t2 = group.loc[i + 1, TIME_COL]

        r1 = group.loc[i, RATE_COL]
        r2 = group.loc[i + 1, RATE_COL]

        dt = (t2 - t1).total_seconds()

        # Reject invalid or unusually long intervals
        if dt <= 0 or dt > MAX_GAP_SECONDS or r1 < 0 or r2 < 0:

            excluded_intervals += 1

            intervals.append({
                "instrument_id": instrument,
                "start_time": t1,
                "end_time": t2,
                "interval_seconds": dt,
                "dose": np.nan,
                "status": "Excluded"
            })

            continue

        # Trapezoidal integration
        dose = ((r1 + r2) / 2) * dt * RATE_TO_DOSE_FACTOR

        total_dose += dose
        valid_intervals += 1

        intervals.append({
            "instrument_id": instrument,
            "start_time": t1,
            "end_time": t2,
            "interval_seconds": dt,
            "dose": dose,
            "status": "Valid"
        })

    summaries.append({
        "instrument_id": instrument,
        "cumulative_dose": total_dose,
        "valid_intervals": valid_intervals,
        "excluded_intervals": excluded_intervals
    })

# Save reports
interval_report = pd.DataFrame(intervals)
dose_report = pd.DataFrame(summaries)

interval_report.to_csv("dose_intervals.csv", index=False)
dose_report.to_csv("cumulative_dose_report.csv", index=False)

print("\n======= CUMULATIVE DOSE REPORT =======")
print(dose_report.to_string(index=False))

print("\nReports saved successfully.")
