
import pandas as pd

# Load NASA data
data = pd.read_csv("nasa_radiation.csv")

# Convert timestamp
data["timestamp"] = pd.to_datetime(data["timestamp"])

# Sort separately by instrument
data = data.sort_values(
    ["instrument_id", "timestamp"]
)

# Provisional threshold:
# NASA documents 300 seconds for DosTel instruments.
# We use 2x that cadence as an initial warning threshold.
EXPECTED_CADENCE = 300
GAP_THRESHOLD = EXPECTED_CADENCE * 2

all_gaps = []

print("\n========== RADCONTEXT GAP DETECTION ==========")

for instrument, group in data.groupby("instrument_id"):

    group = group.copy()

    # Calculate time difference
    group["gap_seconds"] = (
        group["timestamp"].diff().dt.total_seconds()
    )

    # Select intervals exceeding threshold
    gaps = group[group["gap_seconds"] > GAP_THRESHOLD]

    print("\nInstrument:", instrument)

    print("Total readings:", len(group))

    print("Median interval:",
          group["gap_seconds"].median(), "seconds")

    print("Maximum interval:",
          group["gap_seconds"].max(), "seconds")

    print("Long gaps detected:", len(gaps))

    if len(gaps) > 0:

        for _, row in gaps.iterrows():

            print("\nWARNING: Long interval detected")

            print("Instrument:", instrument)

            print("Time:", row["timestamp"])

            print("Gap:", row["gap_seconds"], "seconds")

            all_gaps.append({
                "instrument_id": instrument,
                "timestamp": row["timestamp"],
                "gap_seconds": row["gap_seconds"],
                "gap_minutes": row["gap_seconds"] / 60
            })

# Save gap report
gap_report = pd.DataFrame(all_gaps)

gap_report.to_csv("gap_report.csv", index=False)

print("\n========== FINAL REPORT ==========")

print("Total long gaps:", len(gap_report))

print("Report saved as gap_report.csv")
