
import pandas as pd

# 1. Load downloaded NASA data
data = pd.read_csv("nasa_radiation.csv")

# 2. Convert timestamp into datetime format
data["timestamp"] = pd.to_datetime(data["timestamp"])

# 3. Convert radiation readings into numbers
data["absorbed_dose_rate"] = pd.to_numeric(
    data["absorbed_dose_rate"],
    errors="coerce"
)

# 4. Sort readings by instrument and time
data = data.sort_values(
    ["instrument_id", "timestamp"]
)

print("\n========== DATA OVERVIEW ==========")

print("Total records:", len(data))

print("\nInstruments found:")
print(data["instrument_id"].value_counts())

# 5. Check missing values
print("\n========== MISSING VALUES ==========")
print(data.isnull().sum())

# 6. Check duplicate timestamps
print("\n========== DUPLICATE TIMESTAMPS ==========")

duplicates = data.duplicated(
    subset=["instrument_id", "timestamp"],
    keep=False
)

print(data[duplicates])

# 7. Analyse each instrument separately
print("\n========== TIME INTERVAL ANALYSIS ==========")

for instrument, group in data.groupby("instrument_id"):

    group = group.sort_values("timestamp").copy()

    # Difference between consecutive readings
    group["time_gap_seconds"] = (
        group["timestamp"].diff().dt.total_seconds()
    )

    print("\nInstrument:", instrument)

    print("Number of readings:", len(group))

    print("Average dose rate:",
          group["absorbed_dose_rate"].mean())

    print("Minimum dose rate:",
          group["absorbed_dose_rate"].min())

    print("Maximum dose rate:",
          group["absorbed_dose_rate"].max())

    print("Median time interval:",
          group["time_gap_seconds"].median(),
          "seconds")

    print("Maximum time interval:",
          group["time_gap_seconds"].max(),
          "seconds")

    print("\nFirst five time intervals:")
    print(group[["timestamp", "time_gap_seconds"]].head())

print("\nAnalysis completed!")
