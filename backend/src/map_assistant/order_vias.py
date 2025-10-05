# app/map/order_vias.py
import math
from typing import List, Tuple, Dict

def _parse_wkt_line_xy(selection: str) -> List[Tuple[float, float]]:
    s = selection.strip()
    if not s.upper().startswith("LINESTRING"):
        return []
    body = s[s.find("(")+1:s.rfind(")")]
    pts = []
    for tok in body.split(","):
        pr = tok.strip().split()
        if len(pr) >= 2:
            pts.append((float(pr[0]), float(pr[1])))  # lon, lat
    return pts

def _haversine_m(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    R = 6371000.0
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2-lon1, lat2-lat1
    aa = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(aa))

def _project_on_segment(p: Tuple[float,float], a: Tuple[float,float], b: Tuple[float,float]):
    # локальная эквирект. проекция — достаточно точно на городских дистанциях
    lon_p, lat_p = map(math.radians, p)
    lon_a, lat_a = map(math.radians, a)
    lon_b, lat_b = map(math.radians, b)
    R = 6371000.0
    k = math.cos((lat_a+lat_b)/2)
    x_p = (lon_p - lon_a) * k * R; y_p = (lat_p - lat_a) * R
    x_b = (lon_b - lon_a) * k * R; y_b = (lat_b - lat_a) * R
    denom = x_b*x_b + y_b*y_b or 1e-9
    t = (x_p*x_b + y_p*y_b) / denom
    t = max(0.0, min(1.0, t))
    x_proj = t * x_b; y_proj = t * y_b
    lon_proj = (x_proj / (k * R)) + lon_a
    lat_proj = (y_proj / R) + lat_a
    return (math.degrees(lon_proj), math.degrees(lat_proj)), t

def _polyline_from_route_v7(route: Dict) -> List[Tuple[float,float]]:
    line: List[Tuple[float,float]] = []
    for man in (route.get("maneuvers") or []):
        path = man.get("outcoming_path") or {}
        for g in (path.get("geometry") or []):
            if not isinstance(g, dict): 
                continue
            sel = g.get("selection")
            if not sel: 
                continue
            pts = _parse_wkt_line_xy(sel)
            if not pts: 
                continue
            if line and pts and pts[0] == line[-1]:
                line.extend(pts[1:])
            else:
                line.extend(pts)
    return line

def _cum_lengths(poly: List[Tuple[float,float]]) -> List[float]:
    L = [0.0]
    for i in range(1, len(poly)):
        L.append(L[-1] + _haversine_m(poly[i-1], poly[i]))
    return L

def _project_on_polyline(point: Tuple[float,float], poly, L) -> Tuple[float, float]:
    best_s, best_d = 0.0, float("inf")
    if len(poly) < 2: 
        return best_s, best_d
    for i in range(len(poly)-1):
        a, b = poly[i], poly[i+1]
        proj, t = _project_on_segment(point, a, b)
        s_here = L[i] + t * (L[i+1] - L[i])
        d_here = _haversine_m(point, proj)
        if d_here < best_d:
            best_d, best_s = d_here, s_here
    return best_s, best_d

def order_and_filter_vias_along_route(
    route: Dict,
    candidates: List[Tuple[float,float]],
    *,
    max_lateral_m: int = 120,
    min_step_m: int = 350,
    max_vias: int = 6,
) -> List[Tuple[float,float]]:
    """Отбирает via-точки близко к базовому маршруту, сортирует по «прогрессу» и разрежает по шагу."""
    poly = _polyline_from_route_v7(route)
    if len(poly) < 2:
        return []

    L = _cum_lengths(poly)
    scored = []
    for lon, lat in candidates:
        s, d = _project_on_polyline((lon, lat), poly, L)
        if d <= max_lateral_m:
            scored.append((s, lon, lat))

    scored.sort(key=lambda x: x[0])

    picked: List[Tuple[float,float]] = []
    last_s: float | None = None
    for s, lon, lat in scored:
        if last_s is None or (s - last_s) >= min_step_m:
            picked.append((lon, lat))
            last_s = s
            if len(picked) >= max_vias:
                break
    return picked
