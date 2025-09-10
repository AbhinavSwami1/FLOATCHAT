

from fastapi import FastAPI, Query
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

# -------------------------------
# Load ENV
# -------------------------------
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")  # Render / Local DB URL

app = FastAPI()

# DB connection
engine = create_engine(DB_URL)

@app.get("/get_float_data")
def get_float_data(lat: float = Query(None), lon: float = Query(None)):
    """
    Get float data filtered by lat/lon
    """
    query = "SELECT * FROM argo_data"
    filters = []
    
    if lat:
        filters.append(f"LATITUDE = {lat}")
    if lon:
        filters.append(f"LONGITUDE = {lon}")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")


@app.get("/time_series")
def get_time_series(lat: float, lon: float):
    """
    Return time series of salinity/temp at given location
    """
    query = f"""
    SELECT TIME, TEMP, PSAL 
    FROM argo_data 
    WHERE LATITUDE={lat} AND LONGITUDE={lon}
    ORDER BY TIME
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")
