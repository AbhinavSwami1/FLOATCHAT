import xarray as xr
import pandas as pd

# NetCDF file ka path
file_path = "../dataset/float_sample.nc"

# NetCDF load karo
ds = xr.open_dataset(file_path)

# Print dataset summary
print(ds)

# Ek DataFrame me convert karo (temperature, salinity, pressure, latitude, longitude, time)
df = ds.to_dataframe().reset_index()

print(df.head())

df.to_csv("../dataset/argo_sample.csv", index=False)
