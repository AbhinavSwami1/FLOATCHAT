from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv

# -------------------------------
# Load ENV
# -------------------------------
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(DB_URL)

# -------------------------------
# 10 ENDPOINTS
# -------------------------------

@app.get("/get_float_data")
def get_float_data(lat: float = Query(None), lon: float = Query(None)):
    query = "SELECT * FROM argo_data"
    filters = []
    if lat: filters.append(f"LATITUDE = {lat}")
    if lon: filters.append(f"LONGITUDE = {lon}")
    if filters: query += " WHERE " + " AND ".join(filters)

    try:
        df = pd.read_sql(query, engine)
        if df.empty: raise HTTPException(404, "No data found for given location.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/time_series")
def get_time_series(lat: float, lon: float):
    query = f"""
    SELECT TIME, TEMP AS temperature, PSAL AS salinity
    FROM argo_data
    WHERE LATITUDE={lat} AND LONGITUDE={lon}
    ORDER BY TIME
    """
    try:
        df = pd.read_sql(query, engine)
        if df.empty: raise HTTPException(404, "No data found.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/temperature-trends")
def get_temperature_trends():
    try:
        query = "SELECT AVG(TEMP) AS avg_temp FROM argo_data"
        df = pd.read_sql(query, engine)
        avg_temp = df.iloc[0]['avg_temp']
        return [{"month": "Jan", "temperature": round(avg_temp, 2)}]
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/salinity-profiles")
def get_salinity_profiles():
    try:
        query = "SELECT PRES AS depth, AVG(PSAL) AS salinity FROM argo_data GROUP BY PRES ORDER BY PRES"
        df = pd.read_sql(query, engine)
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m" if pd.notna(x) else None)
        df['salinity'] = df['salinity'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/float-distribution")
def get_float_distribution():
    try:
        query = "SELECT LATITUDE, LONGITUDE FROM argo_data"
        df = pd.read_sql(query, engine)
        atlantic = df[(df['LONGITUDE'] >= -80) & (df['LONGITUDE'] <= 20)]
        pacific = df[((df['LONGITUDE'] >= 100) & (df['LONGITUDE'] <= 290)) | ((df['LONGITUDE'] >= -160) & (df['LONGITUDE'] <= -80))]
        indian = df[(df['LONGITUDE'] >= 20) & (df['LONGITUDE'] <= 100)]
        return [
            {"region": "Atlantic", "count": len(atlantic)},
            {"region": "Pacific", "count": len(pacific)},
            {"region": "Indian", "count": len(indian)},
        ]
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/argo-floats")
def get_argo_floats():
    try:
        query = "SELECT LATITUDE as lat, LONGITUDE as lng, TEMP as temperature, PSAL as salinity, PRES as depth FROM argo_data"
        df = pd.read_sql(query, engine)
        df['status'] = 'active'
        df = df.round(3)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/depth-profiles")
def get_depth_profiles():
    try:
        query = "SELECT PRES AS depth, AVG(TEMP) AS temperature FROM argo_data GROUP BY PRES ORDER BY PRES"
        df = pd.read_sql(query, engine)
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m")
        df['temperature'] = df['temperature'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/temperature-salinity")
def get_temp_salinity_relation():
    try:
        query = "SELECT TEMP, PSAL FROM argo_data WHERE TEMP IS NOT NULL AND PSAL IS NOT NULL"
        df = pd.read_sql(query, engine)
        df = df.round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/avg-conditions")
def get_avg_conditions():
    try:
        query = "SELECT AVG(TEMP) AS avg_temp, AVG(PSAL) AS avg_salinity, AVG(PRES) AS avg_depth FROM argo_data"
        df = pd.read_sql(query, engine)
        return df.round(2).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/data-coverage")
def get_data_coverage():
    try:
        query = "SELECT COUNT(*) AS total_records, COUNT(DISTINCT LATITUDE) AS unique_latitudes, COUNT(DISTINCT LONGITUDE) AS unique_longitudes FROM argo_data"
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")
