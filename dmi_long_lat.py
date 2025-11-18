import requests

# Your request URL
url = "https://dmigw.govcloud.dk/v1/forecastedr/collections/wam_nsb/position"
params = {
    "coords": "POINT(6.76 58.1)",
    "crs": "crs84",
    "parameter-name": "wind-speed,wind-dir,significant-wave-height,dominant-wave-period,mean-wave-period,mean-zerocrossing-period,mean-wave-dir,significant-windwave-height,mean-windwave-period,mean-windwave-dir,significant-totalswell-height,mean-totalswell-period,mean-totalswell-dir,benjamin-feir-index",
    "api-key": "ae501bfc-112e-400e-89df-77a2a6b9af72",
    "f": "GeoJSON"
}

response = requests.get(url, params=params)
data = response.json()

# Check the coordinates the API actually returned
if "features" in data and len(data["features"]) > 0:
    coords = data["features"][0]["geometry"]["coordinates"]
    print("Data is actually for longitude, latitude:", coords)
else:
    print("No data returned")

