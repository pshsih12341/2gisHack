import math
from typing import Tuple, List, Optional

def bearing(p1: Tuple[float,float], p2: Tuple[float,float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [p1[0], p1[1], p2[0], p2[1]])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1)*math.cos(lat2)*math.cos(dlon) + math.sin(lat1)*math.sin(lat2)
    return math.atan2(y, x)

def offset(lon: float, lat: float, distance_m: float, bearing_rad: float) -> Tuple[float, float]:
    R = 6371000.0
    δ = distance_m / R
    θ = bearing_rad
    φ1 = math.radians(lat); λ1 = math.radians(lon)
    φ2 = math.asin(math.sin(φ1)*math.cos(δ) + math.cos(φ1)*math.sin(δ)*math.cos(θ))
    λ2 = λ1 + math.atan2(math.sin(θ)*math.sin(δ)*math.cos(φ1),
                         math.cos(δ) - math.sin(φ1)*math.sin(φ2))
    return (math.degrees(λ2), math.degrees(φ2))

def haversine_m(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    R = 6371000.0
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    aa = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(aa))

def parse_wkt_line(selection: str) -> List[Tuple[float, float, Optional[float]]]:
    s = selection.strip()
    if not s.upper().startswith("LINESTRING"):
        return []
    coords_str = s[s.find("(")+1 : s.rfind(")")]
    pts = []
    for token in coords_str.split(","):
        parts = token.strip().split()
        if len(parts) >= 2:
            lon = float(parts[0]); lat = float(parts[1])
            z = float(parts[2]) if len(parts) >= 3 else None
            pts.append((lon, lat, z))
    return pts

def segment_max_slope(points: List[Tuple[float,float,Optional[float]]]):
    max_deg = 0.0; max_pair = ((0.0,0.0),(0.0,0.0)); max_idx = 0
    for i in range(len(points)-1):
        lon1, lat1, z1 = points[i]
        lon2, lat2, z2 = points[i+1]
        if z1 is None or z2 is None:
            continue
        dist = haversine_m((lon1,lat1),(lon2,lat2))
        if dist < 1e-3:
            continue
        dz_m = (z2 - z1) / 10.0
        slope = abs(math.degrees(math.atan2(dz_m, dist)))
        if slope > max_deg:
            max_deg = slope
            max_pair = ((lon1, lat1), (lon2, lat2))
            max_idx = i
    return max_deg, max_pair, max_idx

def midpoint(p1: Tuple[float,float], p2: Tuple[float,float]) -> Tuple[float,float]:
    return ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0)
