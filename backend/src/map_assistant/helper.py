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

async def get_green_places_2gis_labeled(
    bbox: Tuple[float, float, float, float],
    limit: int = 20
) -> List[Dict]:
    """
    2GIS Catalog API: ищем «зелёные» места и возвращаем список с метками.
    Каждый элемент: {
        "lon": float, "lat": float,
        "name": str, "category": str, "address": str,
        "place_id": str
    }
    """
    bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"  # lon1,lat1,lon2,lat2

    params = {
        "bbox": bbox_str,
        "categories": "park,garden,boulevard,embankment,promenade,waterfront",
        "limit": limit,
        "key": API_KEY,
        "locale": "ru",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{GIS_PLACES_URL}/places/search", params=params)
        if resp.status_code != 200:
            print(f"DEBUG: Places API error (green labeled): {resp.text}")
            return []
        data: Dict = resp.json()

    out: List[Dict] = []
    seen = set()
    for item in data.get("items", []):
        try:
            lon = float(item.get("lon") or 0.0)
            lat = float(item.get("lat") or 0.0)
            if not lon or not lat:
                continue
            key = (round(lon, 5), round(lat, 5))
            if key in seen:
                continue
            seen.add(key)

            # Название/адрес/категория — берём максимально «живые» поля, с фолбэками
            name = item.get("name") or item.get("full_name") or "Без названия"
            address = item.get("address_name") or item.get("address") or ""
            category = ""
            if "categories" in item and isinstance(item["categories"], list) and item["categories"]:
                category = item["categories"][0].get("name") or item["categories"][0].get("slug") or ""
            elif "rubrics" in item and isinstance(item["rubrics"], list) and item["rubrics"]:
                category = item["rubrics"][0].get("name") or item["rubrics"][0].get("alias") or ""

            out.append({
                "lon": lon,
                "lat": lat,
                "name": name,
                "category": category or "green_place",
                "address": address,
                "place_id": item.get("id") or item.get("place_id") or "",
            })
            if len(out) >= limit:
                break
        except Exception:
            continue
    return out

async def get_toilets_osm(bbox: Tuple[float, float, float, float], limit: int = 12) -> List[Dict]:
    """
    Возвращает туалеты из OSM в bbox как список словарей:
    { "lon": float, "lat": float, "name": str, "source": "osm" }
    """
    min_lat, min_lon, max_lat, max_lon = bbox
    query = f"""
    [out:json][timeout:40];
    (
      node["amenity"="toilets"]({min_lat},{min_lon},{max_lat},{max_lon});
      way["amenity"="toilets"]({min_lat},{min_lon},{max_lat},{max_lon});
      relation["amenity"="toilets"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out center;
    """
    async with httpx.AsyncClient() as client:
        r = await client.post(OVERPASS_URL, data={"data": query})
        if r.status_code != 200:
            print("DEBUG: Overpass toilets error:", r.text)
            return []
        data = r.json()

    out, seen = [], set()
    for el in data.get("elements", []):
        if el.get("type") == "node":
            lon, lat = float(el["lon"]), float(el["lat"])
        else:
            center = el.get("center")
            if not center:
                continue
            lon, lat = float(center["lon"]), float(center["lat"])
        key = (round(lon, 5), round(lat, 5))
        if key in seen:
            continue
        seen.add(key)
        name = el.get("tags", {}).get("name") or "Туалет"
        out.append({"lon": lon, "lat": lat, "name": name, "source": "osm"})
        if len(out) >= limit:
            break
    return out

def _bbox_tuple_to_str(bbox: Tuple[float,float,float,float]) -> str:
    min_lat,min_lon,max_lat,max_lon = bbox
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"

async def get_hotspots_2gis(bbox: Tuple[float,float,float,float], limit: int = 40) -> List[Dict]:
    bbox_str = _bbox_tuple_to_str(bbox)
    cats = ",".join([
        "metro_stations","shopping_mall","market","bazaar",
        "stadium","sports_complex","arena",
        "railway_station","bus_station",
        "tourist_attraction","museum","exhibition_center",
        "fastfood","food_court",
    ])
    params = {
        "bbox": bbox_str,
        "categories": cats,
        "q": "метро|торговый центр|рынок|стадион|вокзал|музей|аттракцион",
        "limit": limit,
        "key": API_KEY,
        "locale": "ru",
        "fields": "items.point,items.geometry.centroid,items.categories,items.rubrics,items.name_ex",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{GIS_PLACES_URL}/places/search", params=params)
        if r.status_code != 200:
            print("DEBUG: Places hotspots error:", r.text)
            return []
        data = r.json()

    out, seen = [], set()
    for it in data.get("items", []):
        # координаты: point > geometry.centroid
        pt = it.get("point") or ((it.get("geometry") or {}).get("centroid")) or {}
        try:
            lon = float(pt.get("lon") or 0.0)
            lat = float(pt.get("lat") or 0.0)
            if not lon or not lat:
                continue
        except Exception:
            continue

        key = (round(lon,5), round(lat,5))
        if key in seen:
            continue
        seen.add(key)

        # имя/категория
        name = it.get("name") or (it.get("name_ex") or {}).get("primary") or "Hotspot"
        cat  = ""
        if isinstance(it.get("categories"), list) and it["categories"]:
            cat = it["categories"][0].get("name") or it["categories"][0].get("slug") or ""
        elif isinstance(it.get("rubrics"), list) and it["rubrics"]:
            cat = it["rubrics"][0].get("name") or it["rubrics"][0].get("alias") or ""

        out.append({
            "lon": lon, "lat": lat, "name": name,
            "category": cat or "hotspot",
            "place_id": it.get("id") or it.get("place_id") or "",
        })
        if len(out) >= limit:
            break
    print(f"DEBUG[hotspots]: bbox={bbox_str}, count={len(out)}")
    return out