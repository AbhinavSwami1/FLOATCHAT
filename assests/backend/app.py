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
    allow_origins=["*"],  # For dev; restrict in prod
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
    if lat: filters.append(f"latitude = {lat}")
    if lon: filters.append(f"longitude = {lon}")
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
    SELECT time, temp AS temperature, psal AS salinity
    FROM argo_data
    WHERE latitude={lat} AND longitude={lon}
    ORDER BY time
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
        query = "SELECT AVG(temp) AS avg_temp FROM argo_data"
        df = pd.read_sql(query, engine)
        avg_temp = df.iloc[0]['avg_temp']
        return [{"month": "Jan", "temperature": round(avg_temp, 2)}]
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/salinity-profiles")
def get_salinity_profiles():
    try:
        query = "SELECT pres AS depth, AVG(psal) AS salinity FROM argo_data GROUP BY pres ORDER BY pres"
        df = pd.read_sql(query, engine)
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m" if pd.notna(x) else None)
        df['salinity'] = df['salinity'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/float-distribution")
def get_float_distribution():
    try:
        query = "SELECT latitude, longitude FROM argo_data"
        df = pd.read_sql(query, engine)
        atlantic = df[(df['longitude'] >= -80) & (df['longitude'] <= 20)]
        pacific = df[((df['longitude'] >= 100) & (df['longitude'] <= 290)) | ((df['longitude'] >= -160) & (df['longitude'] <= -80))]
        indian = df[(df['longitude'] >= 20) & (df['longitude'] <= 100)]
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
        query = "SELECT latitude as lat, longitude as lng, temp as temperature, psal as salinity, pres as depth FROM argo_data"
        df = pd.read_sql(query, engine)
        df['status'] = 'active'
        df = df.round(3)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/depth-profiles")
def get_depth_profiles():
    try:
        query = "SELECT pres AS depth, AVG(temp) AS temperature FROM argo_data GROUP BY pres ORDER BY pres"
        df = pd.read_sql(query, engine)
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m")
        df['temperature'] = df['temperature'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/temperature-salinity")
def get_temp_salinity_relation():
    try:
        query = "SELECT temp, psal FROM argo_data WHERE temp IS NOT NULL AND psal IS NOT NULL"
        df = pd.read_sql(query, engine)
        df = df.round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/avg-conditions")
def get_avg_conditions():
    try:
        query = "SELECT AVG(temp) AS avg_temp, AVG(psal) AS avg_salinity, AVG(pres) AS avg_depth FROM argo_data"
        df = pd.read_sql(query, engine)
        return df.round(2).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")


@app.get("/api/data-coverage")
def get_data_coverage():
    try:
        query = "SELECT COUNT(*) AS total_records, COUNT(DISTINCT latitude) AS unique_latitudes, COUNT(DISTINCT longitude) AS unique_longitudes FROM argo_data"
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")
