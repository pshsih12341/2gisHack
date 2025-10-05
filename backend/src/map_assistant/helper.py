import json
import httpx
from os import getenv
from fastapi import HTTPException
from typing import Dict, List

GIS_ROUTING_URL = "https://routing.api.2gis.com/routing/7.0.0/global"
GIS_PLACES_URL = "https://catalog.api.2gis.com/3.0"
API_KEY = getenv("DGIS_API_KEY")

def _normalize_points(points: List[Dict]) -> List[Dict]:
    """Приводим точки к формату v7: только lon/lat/type=stop"""
    out = []
    for p in points:
        out.append({"type": "stop", "lon": p["lon"], "lat": p["lat"]})
    return out

async def call_routing_api(points: List[dict], additional_params: dict | None = None):
    if additional_params is None:
        additional_params = {}

    body = {
        "points": _normalize_points(points),
        "transport": "walking",
        "locale": "ru",
    }
    body.update(additional_params)

    params = {"key": API_KEY}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        print(f"DEBUG: Sending request to 2GIS Routing API: {json.dumps(body, indent=2)}")
        response = await client.post(GIS_ROUTING_URL, params=params, headers=headers, json=body)
        print(f"DEBUG: Routing API response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                data["routes"] = sorted(data["routes"], key=lambda r: r["legs"][0]["duration"]["value"])
            return data
        raise HTTPException(status_code=response.status_code, detail=f"Routing API error: {response.text}")