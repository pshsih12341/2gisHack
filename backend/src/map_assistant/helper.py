from datetime import datetime
import json
from math import inf
from zoneinfo import ZoneInfo
import httpx
from os import getenv
from fastapi import HTTPException
from typing import Dict, List, Tuple

GIS_ROUTING_URL = "https://routing.api.2gis.com/routing/7.0.0/global"
GIS_PLACES_URL = "https://catalog.api.2gis.com/3.0"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
API_KEY = getenv("DGIS_API_KEY")

def _parse_wkt_coords(selection: str) -> list[tuple[float, float]]:
    # "LINESTRING(lon lat [z], lon lat [z], ...)"
    s = selection.strip()
    if not s.upper().startswith("LINESTRING"):
        return []
    body = s[s.find("(")+1 : s.rfind(")")]
    pts = []
    for token in body.split(","):
        parts = token.strip().split()
        if len(parts) >= 2:
            lon = float(parts[0]); lat = float(parts[1])
            pts.append((lon, lat))
    return pts

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
    """
    Ищем освещённые ways и возвращаем «средние точки» как кандидаты via.
    """
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
        resp = await client.post(OVERPASS_URL, data={"data": overpass_query})
        if resp.status_code != 200:
            print(f"DEBUG: Overpass error: {resp.text}")
            return []
        data = resp.json()

    midpoints: list[tuple[float, float]] = []
    for el in data.get("elements", []):
        geom = el.get("geometry") or []
        if not geom:
            continue
        sum_lon = sum(p["lon"] for p in geom)
        sum_lat = sum(p["lat"] for p in geom)
        lon = sum_lon / len(geom)
        lat = sum_lat / len(geom)
        midpoints.append((lon, lat))

    seen = set()
    uniq = []
    for lon, lat in midpoints:
        key = (round(lon, 5), round(lat, 5))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((lon, lat))
        if len(uniq) >= 8:
            break
    return uniq

    
def is_open_now(schedule: Dict, *, tz: str = "Europe/Moscow") -> bool:
    """
    Универсальная проверка:
    - поддерживает is_24_7
    - учитывает день недели
    - учитывает минуты и интервалы, пересекающие полночь
    Ожидаемые формы:
    - {"is_24_7": true}
    - {"work_hours": [{"days": ["mon","tue",...], "from": "09:00", "to": "18:00"}, ...]}
      или [{"from":"09:00","to":"22:00"}]  # ежедневно
    """
    if not schedule:
        return False
    if schedule.get("is_24_7"):
        return True

    now = datetime.now(ZoneInfo(tz))
    dow = ["mon","tue","wed","thu","fri","sat","sun"][now.weekday()]
    hhmm = now.hour * 60 + now.minute

    intervals = schedule.get("work_hours") or []
    if not isinstance(intervals, list):
        return False

    def _parse_hhmm(s: str) -> int:
        try:
            h, m = s.split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return -1

    for it in intervals:
        days = it.get("days")
        if days and dow not in [d.lower()[:3] for d in days]:
            continue
        start = _parse_hhmm(it.get("from", "00:00"))
        end   = _parse_hhmm(it.get("to",   "23:59"))

        if start == -1 or end == -1:
            continue

        if end >= start:
            # обычный интервал в пределах дня
            if start <= hhmm <= end:
                return True
        else:
            # «через полночь»: открыт, если сейчас >= start ИЛИ сейчас <= end
            if hhmm >= start or hhmm <= end:
                return True
    return False

async def get_open_places_2gis(bbox: str) -> List[Tuple[float, float]]:
    """
    2GIS Places API: ищем открытые заведения в bbox.
    Важно: используем query-параметр key=..., а не Bearer.
    """
    params = {
        "bbox": bbox,  # "lon1,lat1,lon2,lat2"
        "categories": "shops,restaurants",
        "limit": 20,
        "key": API_KEY,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{GIS_PLACES_URL}/places/search", params=params)
        if resp.status_code != 200:
            print(f"DEBUG: Places API error: {resp.text}")
            return []
        data = resp.json()

    midpoints = []
    for item in data.get("items", []):
        if is_open_now(item.get("schedule", {}), tz="Europe/Moscow"):
            lon = float(item.get("lon") or 0.0)
            lat = float(item.get("lat") or 0.0)
            if lon and lat:
                midpoints.append((lon, lat))

    # лёгкая дедупликация
    seen = set(); out = []
    for lon, lat in midpoints:
        key = (round(lon, 5), round(lat, 5))
        if key in seen:
            continue
        seen.add(key); out.append((lon, lat))
        if len(out) >= 8:
            break
    return out

def route_metrics(route: dict) -> dict:
    alt = route.get("altitudes_info") or {}
    return {
        "route_id": route.get("id") or route.get("route_id"),
        "distance_m": int(route.get("total_distance") or 0),
        "duration_s": int(route.get("total_duration") or 0),
        "max_angle_deg": float(alt.get("max_road_angle") or 0.0),
    }

def extract_bbox_from_route(route_data: Dict) -> Tuple[float, float, float, float]:
    """
    Извлекаем bbox из ПЕРВОГО маршрута (v7): проходим по maneuvers -> outcoming_path.geometry -> selection (WKT).
    Возвращаем (min_lat, min_lon, max_lat, max_lon).
    """
    routes = route_data.get("result") or []
    if not routes:
        return 0.0, 0.0, 0.0, 0.0

    route = routes[0]
    min_lon = inf; min_lat = inf
    max_lon = -inf; max_lat = -inf

    for man in route.get("maneuvers", []) or []:
        path = man.get("outcoming_path") or {}
        for g in path.get("geometry", []) or []:
            if not isinstance(g, dict):
                continue
            sel = g.get("selection")
            if not sel:
                continue
            for lon, lat in _parse_wkt_coords(sel):
                min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
                min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)

    # фолбэк на waypoints, если по какой-то причине геометрия пустая
    if min_lon is inf:
        wps = route.get("waypoints") or []
        for w in wps:
            p = w.get("projected_point") or w.get("original_point") or {}
            lat = float(p.get("lat") or 0.0); lon = float(p.get("lon") or 0.0)
            min_lon = min(min_lon, lon); max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat); max_lat = max(max_lat, lat)

    if min_lon is inf:
        return 0.0, 0.0, 0.0, 0.0

    # немного расширим bbox (50 м), чтобы захватить соседние объекты
    # грубо переведём 50 м в градусы широты/долготы для Москвы
    pad_deg = 50 / 111320.0
    return (min_lat - pad_deg, min_lon - pad_deg, max_lat + pad_deg, max_lon + pad_deg)