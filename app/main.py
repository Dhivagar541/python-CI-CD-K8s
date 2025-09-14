from fastapi import FastAPI, Query, HTTPException
import httpx
from datetime import datetime
import pytz

app = FastAPI(title="Weather & Time API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/time")
def get_time(timezone: str = "UTC"):
    try:
        tz = pytz.timezone(timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")
    now = datetime.now(tz)
    return {"timezone": timezone, "time": now.strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/weather")
def get_weather(city: str = Query(..., description="City name")):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    try:
        geo_resp = httpx.get(geo_url, timeout=5)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        if "results" not in geo_data or not geo_data["results"]:
            raise HTTPException(status_code=404, detail="City not found")
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {e}")

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
    )
    try:
        weather_resp = httpx.get(weather_url, timeout=5)
        weather_resp.raise_for_status()
        data = weather_resp.json()
        current = data.get("current_weather", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {e}")

    return {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": current.get("temperature"),
        "windspeed": current.get("windspeed"),
        "weather_code": current.get("weathercode"),
    }
