from datetime import datetime
import json
import httpx
from os import getenv
from fastapi import HTTPException
from typing import Dict, List, Tuple

GIS_ROUTING_URL = "https://routing.api.2gis.com/routing/7.0.0/global"
GIS_PLACES_URL = "https://catalog.api.2gis.com/3.0"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
API_KEY = getenv("DGIS_API_KEY")

def _normalize_points(points: List[Dict]) -> List[Dict]:
    """Приводим точки к формату v7: только lon/lat/type=stop"""
    out = []
    for p in points:
        out.append({"type": "stop", "lon": p["lon"], "lat": p["lat"]})
    return out

async def call_routing_api(points: List[dict], additional_params: dict | None = None, *, alias_routes: bool = False):
    if additional_params is None:
        additional_params = {}

    body = {
        "points": _normalize_points(points),
        "transport": "walking",
        "locale": "ru",
        "output": "detailed"
    }
    body.update(additional_params)

    params = {"key": API_KEY}
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        print(f"DEBUG: Sending request to 2GIS Routing API: {json.dumps(body, indent=2, ensure_ascii=False)}")
        resp = await client.post(GIS_ROUTING_URL, params=params, headers=headers, json=body)
        print(f"DEBUG: Routing API response status: {resp.status_code}")

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Routing API error: {resp.text}")

        data = resp.json()

        status = data.get("status")
        if status != "OK":
            msg = data.get("message") or status or "Unknown routing error"
            raise HTTPException(status_code=502, detail=f"Routing API error: {msg}")
        
        routes = data.get("result") or []
        if not isinstance(routes, list):
            raise HTTPException(status_code=502, detail="Routing API response: 'result' is not a list")

        def _dur(r: dict) -> int:
            return int(r.get("total_duration") or 10**12)

        routes.sort(key=_dur)

        data["result"] = routes

        if alias_routes:
            data["routes"] = routes

        return data
        
async def get_lit_streets_overpass(bbox: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
    """Overpass API: Ищем освещённые улицы (highway/footway lit=yes) в bbox, возвращаем midpoints как via-points"""
    min_lat, min_lon, max_lat, max_lon = bbox
    overpass_query = f"""
    [out:json][timeout:40];
    (
      way["highway"]["lit"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["footway"]["lit"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out tags geom;
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(OVERPASS_URL, data={"data": overpass_query})
        if response.status_code == 200:
            data = response.json()
            midpoints = []
            for element in data.get("elements", []):
                if "geometry" in element:
                    # Берём midpoint первой геометрии (примерно центр)
                    geom = element["geometry"][0] if element["geometry"] else None
                    if geom:
                        lon = (geom["lon"] + element["bounds"]["minlon"]) / 2
                        lat = (geom["lat"] + element["bounds"]["minlat"]) / 2
                        midpoints.append((lon, lat))
            return midpoints[:5]
        print(f"DEBUG: Overpass error: {response.text}")
        return []
    
def is_open_now(schedule: Dict) -> bool:
    """Проверяем, открыт ли объект сейчас по schedule (2GIS формат)"""
    if not schedule:
        return False
    now = datetime.now()
    if schedule.get("is_24_7"):
        return True
    for interval in schedule.get("work_hours", []):
        from_h, to_h = interval["from"].split(":"), interval["to"].split(":")
        if int(from_h[0]) <= now.hour <= int(to_h[0]):
            return True
    return False

async def get_open_places_2gis(bbox: str) -> List[Tuple[float, float]]:
    """2GIS Places API: Ищем открытые заведения (shops/restaurants) в bbox, возвращаем midpoints"""
    params = {
        "bbox": bbox,  # lon1,lat1,lon2,lat2
        "categories": "shops,restaurants",
        "limit": 10
    }
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = await client.get(f"{GIS_PLACES_URL}/places/search", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            midpoints = []
            for item in data.get("items", []):
                if is_open_now(item.get("schedule", {})):
                    lon, lat = item["lon"], item["lat"]
                    midpoints.append((lon, lat))
            return midpoints[:5]
        print(f"DEBUG: Places API error: {response.text}")
        return []

def extract_bbox_from_route(route_data: Dict) -> Tuple[float, float, float, float]:
    """Извлекаем bbox из первого leg маршрута"""
    legs = route_data.get("routes", [{}])[0].get("legs", [{}])[0]
    bbox = legs.get("bbox", [[0,0],[0,0]])
    return bbox[0][1], bbox[0][0], bbox[1][1], bbox[1][0]