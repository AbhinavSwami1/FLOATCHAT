# backend/fetch_indian_data.py

import requests
from bs4 import BeautifulSoup
import xarray as xr
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO

# -------------------------------
# CONFIG
# -------------------------------
BASE_URL = "https://data-argo.ifremer.fr/geo/indian_ocean/2025/01/"
DB_URL = "postgresql://postgres:floatchat@localhost:5432/floatchat"
TABLE_NAME = "argo_data"

# -------------------------------
# Step 1: Get all .nc file URLs
# -------------------------------
resp = requests.get(BASE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

file_urls = [
    BASE_URL + link.get("href")
    for link in soup.find_all("a")
    if link.get("href", "").endswith(".nc")
]

print(f"✅ Found {len(file_urls)} .nc files")

# -------------------------------
# Step 2: Load datasets as DataFrames
# -------------------------------
dataframes = []
for url in file_urls:
    try:
        print(f"⏳ Loading {url} ...")
        response = requests.get(url, timeout=60)
        ds = xr.open_dataset(BytesIO(response.content), engine="scipy")

        # Drop extra coordinates that cause alignment issues
        ds = ds.reset_coords(drop=True)

        # Convert each dataset to pandas DataFrame
        df_part = ds.to_dataframe().reset_index()

        dataframes.append(df_part)
        print(f"✅ Loaded: {url}")
    except Exception as e:
        print(f"⚠ Could not load {url}: {e}")

if not dataframes:
    raise Exception("❌ No data loaded. Check URLs or network!")

# -------------------------------
# Step 3: Combine all DataFrames
# -------------------------------
df = pd.concat(dataframes, ignore_index=True)
print("✅ All datasets combined into one DataFrame")
print(df.head())

# -------------------------------
# Step 4: Push DataFrame to PostgreSQL
# -------------------------------
engine = create_engine(DB_URL)

# Write to Postgres (in chunks to avoid memory issues)
df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False, chunksize=1000)

print(f"✅ Data pushed to PostgreSQL table '{TABLE_NAME}'")
