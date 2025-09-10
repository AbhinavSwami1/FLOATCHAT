# backend/fetch_indian_data_updated.py

import os
import requests
from bs4 import BeautifulSoup
import xarray as xr
import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO
from dotenv import load_dotenv
import numpy as np

# -------------------------------
# Load ENV
# -------------------------------
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")  # Render DB URL
TABLE_NAME = "argo_data"

# -------------------------------
# CONFIG
# -------------------------------
BASE_URL = "https://data-argo.ifremer.fr/geo/indian_ocean/2025/01/"

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
# Step 2: Load datasets and extract variables
# -------------------------------
dataframes = []
for url in file_urls:
    try:
        print(f"⏳ Loading {url} ...")
        response = requests.get(url, timeout=60)
        ds = xr.open_dataset(BytesIO(response.content), engine="scipy")
        
        # Extract variables manually
        # Only include variables useful for your backend endpoints
        lat = ds['LATITUDE'].values.flatten() if 'LATITUDE' in ds else np.array([])
        lon = ds['LONGITUDE'].values.flatten() if 'LONGITUDE' in ds else np.array([])
        temp = ds['TEMP'].values.flatten() if 'TEMP' in ds else np.array([])
        psal = ds['PSAL'].values.flatten() if 'PSAL' in ds else np.array([])
        time = ds['JULD'].values.flatten() if 'JULD' in ds else np.array([])

        # Ensure all arrays are same length
        min_len = min(len(lat), len(lon), len(temp), len(psal), len(time))
        if min_len == 0:
            print(f"⚠ Skipping {url}, no valid data found")
            continue

        df_part = pd.DataFrame({
            'LATITUDE': lat[:min_len],
            'LONGITUDE': lon[:min_len],
            'TEMP': temp[:min_len],
            'PSAL': psal[:min_len],
            'TIME': time[:min_len]
        })
        dataframes.append(df_part)
        print(f"✅ Loaded: {url} ({len(df_part)} rows)")
    except Exception as e:
        print(f"⚠ Could not load {url}: {e}")

if not dataframes:
    raise Exception("❌ No data loaded. Check URLs or network!")

# -------------------------------
# Step 3: Combine DataFrames
# -------------------------------
df = pd.concat(dataframes, ignore_index=True)
print(f"✅ All datasets combined into one DataFrame ({len(df)} rows)")
print(df.head())

# -------------------------------
# Step 4: Push to Render Postgres
# -------------------------------
engine = create_engine(DB_URL)
df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False, chunksize=1000)
print(f"✅ Data pushed to PostgreSQL table '{TABLE_NAME}' on Render DB")
