
import requests
import pandas as pd
from io import StringIO

url = "https://visualization.osdr.nasa.gov/radlab/api/"

params = {
    "spacecraft": "ISS",
    "instrument": "DosTel",
    "timestamp>": "2022-04-01T23:00",
    "timestamp<": "2022-04-02T01:05",
    "absorbed_dose_rate": "",
    "format": "csv"
}

response = requests.get(url, params=params, timeout=60)

print("Status:", response.status_code)

response.raise_for_status()

data = pd.read_csv(StringIO(response.text))

print("\nFirst five records:")
print(data.head())

print("\nAvailable columns:")
print(data.columns.tolist())

# Save downloaded data
data.to_csv("nasa_radiation.csv", index=False)

print("\nNASA data saved successfully!")
