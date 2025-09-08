import requests
import xarray as xr

# Metadata download and save in dataset folder
url = "https://data-argo.ifremer.fr/ar_index_global_meta.txt"
resp = requests.get(url)
with open("../dataset/ar_index_global_meta.txt", "wb") as f:
    f.write(resp.content)

# Sample NetCDF file download
file_url = "https://data-argo.ifremer.fr/dac/incois/2902746/profiles/D2902746_001.nc"
r = requests.get(file_url)
with open("../dataset/float_sample.nc", "wb") as f:
    f.write(r.content)

# Read NetCDF file
ds = xr.open_dataset("../dataset/float_sample.nc")
print(ds)
