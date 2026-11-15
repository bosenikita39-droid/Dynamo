
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("nasa_radiation.csv")

data["timestamp"] = pd.to_datetime(data["timestamp"])

# Plot each instrument separately
for instrument, group in data.groupby("instrument_id"):

    group = group.sort_values("timestamp")

    plt.figure(figsize=(12, 5))

    plt.plot(
        group["timestamp"],
        group["absorbed_dose_rate"],
        marker=".",
        linewidth=1
    )

    plt.title("Radiation Dose Rate - " + instrument)

    plt.xlabel("Time")

    plt.ylabel("Absorbed Dose Rate (µGy/hour)")

    plt.xticks(rotation=45)

    plt.grid()

    plt.tight_layout()

    plt.show()
