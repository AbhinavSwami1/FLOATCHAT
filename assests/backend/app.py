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

# Add CORS middleware to allow requests from your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity in development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

    try:
        df = pd.read_sql(query, engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified location.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
    try:
        df = pd.read_sql(query, engine)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the specified location.")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# -------------------------------
# New Endpoints for Frontend Data
# -------------------------------

@app.get("/api/temperature-trends")
def get_temperature_trends():
    """
    Returns monthly average temperature data for the dashboard chart.
    Since the data is for January 2025 only, it returns a single point.
    The frontend expects an array of objects with 'month' and 'temperature' keys.
    """
    try:
        query = "SELECT AVG(TEMP) AS avg_temp FROM argo_data"
        df = pd.read_sql(query, engine)
        avg_temp = df.iloc[0]['avg_temp']
        
        # We only have data for January 2025
        data = [{"month": "Jan", "temperature": round(avg_temp, 2)}]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/salinity-profiles")
def get_salinity_profiles():
    """
    Returns average salinity by depth for the dashboard chart.
    'PRES' column is used as a proxy for depth.
    The frontend expects an array of objects with 'depth' and 'salinity' keys.
    """
    try:
        query = "SELECT PRES AS depth, AVG(PSAL) AS salinity FROM argo_data GROUP BY PRES ORDER BY PRES"
        df = pd.read_sql(query, engine)
        
        # Format the depth column for the frontend chart
        df['depth'] = df['depth'].apply(lambda x: f"{int(x)}m" if pd.notna(x) else None)
        df['salinity'] = df['salinity'].round(2)

        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/float-distribution")
def get_float_distribution():
    """
    Returns the number of floats distributed by major ocean regions.
    Regions are determined by simple latitude/longitude bounding boxes.
    The frontend expects an array of objects with 'region' and 'count' keys.
    """
    try:
        # Get all unique float IDs and their locations for a more accurate count.
        query = "SELECT ID, LATITUDE, LONGITUDE FROM argo_data GROUP BY ID, LATITUDE, LONGITUDE"
        df = pd.read_sql(query, engine)

        # Simple classification based on longitude
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
    """
    Returns all ARGO float data points for the interactive map.
    This endpoint selects relevant columns and renames them to match the frontend model.
    A 'status' field is added with a default 'active' value.
    """
    try:
        query = """
        SELECT ID, LATITUDE as lat, LONGITUDE as lng, TEMP as temperature, PSAL as salinity, PRES as depth
        FROM argo_data
        """
        df = pd.read_sql(query, engine)
        
        # Add a hardcoded 'status' since the database doesn't have it
        df['status'] = 'active'
        
        # Round numerical values for cleaner display
        df['lat'] = df['lat'].round(4)
        df['lng'] = df['lng'].round(4)
        df['temperature'] = df['temperature'].round(2)
        df['salinity'] = df['salinity'].round(2)
        df['depth'] = df['depth'].round(2)

        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
