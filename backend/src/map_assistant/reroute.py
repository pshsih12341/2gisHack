from typing import List, Tuple, Optional
from .helper import call_routing_api
from .geo import bearing, offset, parse_wkt_line, segment_max_slope, midpoint

def _extract_worst_segment(route: dict) -> Optional[Tuple[Tuple[float,float], Tuple[float,float]]]:
    maneuvers = route.get("maneuvers") or []
    best = (0.0, None)
    for man in maneuvers:
        path = man.get("outcoming_path") or {}
        geoms = path.get("geometry") or []
        for g in geoms:
            if not isinstance(g, dict):
                continue
            sel = g.get("selection")
            if not sel:
                continue
            pts = parse_wkt_line(sel)
            if len(pts) < 2:
                continue
            deg, pair, _ = segment_max_slope(pts)
            if deg > best[0]:
                best = (deg, pair)
    return best[1]

def _candidate_vias(worst_pair: Tuple[Tuple[float,float], Tuple[float,float]]) -> List[Tuple[float,float]]:
    p1, p2 = worst_pair
    mid = midpoint(p1, p2)
    brg = bearing(p1, p2)
    bearings = [brg + 1.5708, brg - 1.5708, brg + 0.7854, brg - 0.7854]  # ±90°, ±45° (рад)
    radii = [80, 120, 160, 200, 250]
    vias = []
    for r in radii:
        for b in bearings:
            vias.append(offset(mid[0], mid[1], r, b))
    return vias

async def reroute_with_slope_limit(points_dict: List[dict], base_params: dict, *, max_angle_deg: float = 5.0, max_tries: int = 24):
    data = await call_routing_api(points_dict, base_params)
    if data.get("status") == "OK" and (data.get("result") or []):
        r0 = data["result"][0]
        alt = r0.get("altitudes_info") or {}
        try:
            mx = float(alt.get("max_road_angle") or 0.0)
        except (TypeError, ValueError):
            mx = 0.0
        if mx <= max_angle_deg:
            return data, 0, []

    base_route = (data.get("result") or [None])[0] if data else None
    worst_seg = _extract_worst_segment(base_route) if base_route else None
    if not worst_seg and len(points_dict) >= 2:
        p1 = (points_dict[0]["lon"], points_dict[0]["lat"])
        p2 = (points_dict[-1]["lon"], points_dict[-1]["lat"])
        worst_seg = (p1, p2)

    via_candidates = _candidate_vias(worst_seg) if worst_seg else []
    tries = 0
    last_exc = None

    # одиночные via
    for via in via_candidates:
        tries += 1
        if tries > max_tries:
            break
        pts = [*points_dict[:-1], {"lat": via[1], "lon": via[0], "type": "via"}, points_dict[-1]]
        try:
            d = await call_routing_api(pts, base_params)
            if d.get("status") == "OK" and (d.get("result") or []):
                r = d["result"][0]
                alt = r.get("altitudes_info") or {}
                mx = float(alt.get("max_road_angle") or 0.0)
                if mx <= max_angle_deg:
                    return d, tries, [via]
        except Exception as e:
            last_exc = e

    # пары via (ограниченная комбинаторика)
    for i in range(min(len(via_candidates), 6)):
        for j in range(i+1, min(len(via_candidates), 10)):
            tries += 1
            if tries > max_tries:
                break
            v1 = via_candidates[i]; v2 = via_candidates[j]
            pts = [points_dict[0],
                   {"lat": v1[1], "lon": v1[0], "type": "via"},
                   {"lat": v2[1], "lon": v2[0], "type": "via"},
                   points_dict[-1]]
            try:
                d = await call_routing_api(pts, base_params)
                if d.get("status") == "OK" and (d.get("result") or []):
                    r = d["result"][0]
                    alt = r.get("altitudes_info") or {}
                    mx = float(alt.get("max_road_angle") or 0.0)
                    if mx <= max_angle_deg:
                        return d, tries, [v1, v2]
            except Exception as e:
                last_exc = e

    return None, tries, last_exc
