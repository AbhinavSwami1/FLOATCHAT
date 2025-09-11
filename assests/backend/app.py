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
DB_URL = os.getenv("DATABASE_URL")  # Render / Local DB URL

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB connection
engine = create_engine(DB_URL)

# -------------------------------
# Endpoints
# -------------------------------

@app.get("/get_float_data")
def get_float_data(lat: float = Query(None), lon: float = Query(None)):
    query = "SELECT * FROM argo_data"
    filters = []

    if lat:
        filters.append(f"LATITUDE = {lat}")
    if lon:
        filters.append(f"LONGITUDE = {lon}")

    if filters:
        query += " WHERE " + " AND ".join(filters)

    try:
        df = pd.read_sql(query, engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified location.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified location.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/temperature-trends")
def get_temperature_trends():
    try:
        query = "SELECT AVG(TEMP) AS avg_temp FROM argo_data"
        df = pd.read_sql(query, engine)
        avg_temp = df.iloc[0]['avg_temp']
        data = [{"month": "Jan", "temperature": round(avg_temp, 2)}]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/salinity-profiles")
def get_salinity_profiles():
    try:
        query = "SELECT PRES AS depth, AVG(PSAL) AS salinity FROM argo_data GROUP BY PRES ORDER BY PRES"
        df = pd.read_sql(query, engine)
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m" if pd.notna(x) else None)
        df['salinity'] = df['salinity'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/float-distribution")
def get_float_distribution():
    try:
        # Using CONFIG_MISSION_NUMBER as unique float identifier
        query = "SELECT CONFIG_MISSION_NUMBER, LATITUDE, LONGITUDE FROM argo_data GROUP BY CONFIG_MISSION_NUMBER, LATITUDE, LONGITUDE"
        df = pd.read_sql(query, engine)

        atlantic_floats = df[(df['LONGITUDE'] >= -80) & (df['LONGITUDE'] <= 20)]
        pacific_floats = df[((df['LONGITUDE'] >= 100) & (df['LONGITUDE'] <= 290)) | ((df['LONGITUDE'] >= -160) & (df['LONGITUDE'] <= -80))]
        indian_floats = df[(df['LONGITUDE'] >= 20) & (df['LONGITUDE'] <= 100)]

        data = [
            {"region": "Atlantic", "count": len(atlantic_floats)},
            {"region": "Pacific", "count": len(pacific_floats)},
            {"region": "Indian", "count": len(indian_floats)},
        ]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/argo-floats")
def get_argo_floats():
    try:
        query = """
        SELECT CONFIG_MISSION_NUMBER as id, LATITUDE as lat, LONGITUDE as lng, TEMP as temperature, PSAL as salinity, PRES as depth
        FROM argo_data
        """
        df = pd.read_sql(query, engine)
        df['status'] = 'active'
        df['lat'] = df['lat'].round(4)
        df['lng'] = df['lng'].round(4)
        df['temperature'] = df['temperature'].round(2)
        df['salinity'] = df['salinity'].round(2)
        df['depth'] = df['depth'].round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
