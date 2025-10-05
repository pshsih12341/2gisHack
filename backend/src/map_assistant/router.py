from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from .reroute import reroute_with_slope_limit

from .schemas import AdaptiveRequest
from .helper import API_KEY, GIS_PLACES_URL, call_routing_api, extract_bbox_from_route, get_lit_streets_overpass, get_open_places_2gis, route_metrics
from ..chatbot import MapAssistant, RoutePoint, RouteResponse, RouteSegment, Route, RouteStage, EnhancedRouteResponse


router = APIRouter(prefix="/map", tags=["Map Assistant"])


def convert_point_type_to_api_type(point_type: str) -> str:
    """Convert internal point_type to 2GIS API type."""
    if point_type in ["start", "end"]:
        return "stop"
    elif point_type == "waypoint":
        return "pref"
    else:
        return "stop"  # Default fallback


class RouteRequest(BaseModel):
    """Request model for route planning."""
    query: str
    region_id: Optional[str] = "moscow"


class RoutePointResponse(BaseModel):
    """Response model for route point."""
    name: str
    latitude: float
    longitude: float
    type: str  # Changed from point_type to type
    description: Optional[str] = None
    address: Optional[str] = None
    start: Optional[bool] = None  # Added start field


class RouteSegmentResponse(BaseModel):
    """Response model for route segment."""
    segment_type: str
    distance: int
    duration: int
    transport_type: Optional[str] = None
    route_name: Optional[str] = None
    description: Optional[str] = None


class RouteModel(BaseModel):
    """Response model for individual route."""
    route_id: str
    total_distance: int
    total_duration: int
    transfer_count: int
    transport_types: List[str]
    segments: List[RouteSegmentResponse]
    summary: str
    raw_data: Optional[Dict[str, Any]] = None  # Raw data from 2GIS API


class RouteStageResponse(BaseModel):
    """Response model for route stage."""
    stage_id: str
    start_point: Optional[RoutePointResponse] = None
    end_point: Optional[RoutePointResponse] = None
    waypoints: Optional[List[RoutePointResponse]] = None
    transport_preference: str
    route_preference: Optional[str] = None
    routes: Optional[List[RouteModel]] = None
    description: str


class EnhancedRouteResponseModel(BaseModel):
    """Enhanced response model for route planning."""
    points: List[RoutePointResponse]
    routes: Optional[List[RouteModel]] = None
    stages: Optional[List[RouteStageResponse]] = None
    text: str
    success: bool
    error_message: Optional[str] = None


@router.post("/plan-route", response_model=EnhancedRouteResponseModel)
async def plan_route(request: RouteRequest):
    """
    Планирование маршрута на основе естественного языка с поддержкой различных видов транспорта.
    
    Примеры запросов:
    - "Хочу построить маршрут от Красной площади до Тверской улицы"
    - "По дороге зайти в кафе Starbucks"
    - "Хочу только такси до аэропорта"
    - "Добраться максимально быстро до центра"
    - "Только наземный транспорт, без метро"
    - "Пешком через парк"
    - "Хочу доехать от метро Бунинская аллея погулять в какой-нибудь парк на юге Москвы, доехать исключительно на автобусах. Потом хочу зайти там в ресторан русской кухни и поехать домой исключительно на метро"
    """
    try:
        # Инициализируем ассистента
        assistant = MapAssistant()
        
        # Обрабатываем запрос
        response: EnhancedRouteResponse = await assistant.process_route_request(request.query)
        
        # Конвертируем точки в формат ответа
        points_response = []
        for i, point in enumerate(response.points):
            api_type = convert_point_type_to_api_type(point.point_type)
            is_start = point.point_type == "start" or (i == 0 and point.point_type == "end")
            
            points_response.append(RoutePointResponse(
                name=point.name,
                latitude=point.latitude,
                longitude=point.longitude,
                type=api_type,
                description=point.description,
                address=point.address,
                start=is_start
            ))
        
        # Конвертируем маршруты в формат ответа
        routes_response = None
        if response.routes:
            routes_response = []
            for route in response.routes:
                segments_response = [
                    RouteSegmentResponse(
                        segment_type=segment.segment_type,
                        distance=segment.distance,
                        duration=segment.duration,
                        transport_type=segment.transport_type,
                        route_name=segment.route_name,
                        description=segment.description
                    )
                    for segment in route.segments
                ]
                
                routes_response.append(RouteModel(
                    route_id=route.route_id,
                    total_distance=route.total_distance,
                    total_duration=route.total_duration,
                    transfer_count=route.transfer_count,
                    transport_types=route.transport_types,
                    segments=segments_response,
                    summary=route.summary,
                    raw_data=route.raw_data
                ))
        
        # Конвертируем этапы в формат ответа
        stages_response = None
        if response.stages:
            stages_response = []
            for stage in response.stages:
                # Конвертируем точки этапа
                stage_start_point = None
                if stage.start_point:
                    stage_start_point = RoutePointResponse(
                        name=stage.start_point.name,
                        latitude=stage.start_point.latitude,
                        longitude=stage.start_point.longitude,
                        type=convert_point_type_to_api_type(stage.start_point.point_type),
                        description=stage.start_point.description,
                        address=stage.start_point.address,
                        start=True
                    )
                
                stage_end_point = None
                if stage.end_point:
                    stage_end_point = RoutePointResponse(
                        name=stage.end_point.name,
                        latitude=stage.end_point.latitude,
                        longitude=stage.end_point.longitude,
                        type=convert_point_type_to_api_type(stage.end_point.point_type),
                        description=stage.end_point.description,
                        address=stage.end_point.address,
                        start=False
                    )
                
                stage_waypoints = None
                if stage.waypoints:
                    stage_waypoints = [
                        RoutePointResponse(
                            name=wp.name,
                            latitude=wp.latitude,
                            longitude=wp.longitude,
                            type=convert_point_type_to_api_type(wp.point_type),
                            description=wp.description,
                            address=wp.address,
                            start=False
                        )
                        for wp in stage.waypoints
                    ]
                
                # Конвертируем маршруты этапа
                stage_routes = None
                if stage.routes:
                    stage_routes = []
                    for route in stage.routes:
                        segments_response = [
                            RouteSegmentResponse(
                                segment_type=segment.segment_type,
                                distance=segment.distance,
                                duration=segment.duration,
                                transport_type=segment.transport_type,
                                route_name=segment.route_name,
                                description=segment.description
                            )
                            for segment in route.segments
                        ]
                        
                        stage_routes.append(RouteModel(
                            route_id=route.route_id,
                            total_distance=route.total_distance,
                            total_duration=route.total_duration,
                            transfer_count=route.transfer_count,
                            transport_types=route.transport_types,
                            segments=segments_response,
                            summary=route.summary,
                            raw_data=route.raw_data
                        ))
                
                stages_response.append(RouteStageResponse(
                    stage_id=stage.stage_id,
                    start_point=stage_start_point,
                    end_point=stage_end_point,
                    waypoints=stage_waypoints,
                    transport_preference=stage.transport_preference,
                    route_preference=stage.route_preference,
                    routes=stage_routes,
                    description=stage.description
                ))
        
        return EnhancedRouteResponseModel(
            points=points_response,
            routes=routes_response,
            stages=stages_response,
            text=response.text,
            success=response.success,
            error_message=response.error_message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке запроса: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Проверка работоспособности сервиса."""
    return {
        "status": "healthy",
        "service": "Map Assistant",
        "version": "1.0.0"
    }

@router.post("/route/wheelchair")
async def wheelchair_route(request: AdaptiveRequest):
    points_dict = [p.model_dump() for p in request.points]
    params = {
        "filters": ["ban_stairway", "dirt_road", "ferry", "highway", "toll_road"],
        "need_altitudes": True,
        "route_mode": "shortest"
    }

    try:
        data = await call_routing_api(points_dict, params)
        if data.get("status") != "OK" or "result" not in data:
            raise HTTPException(status_code=502, detail=f"Routing API error: {data.get('message') or data.get('status')}")

        routes = data.get("result") or []
        if not routes:
            raise HTTPException(status_code=404, detail="No routes found")

        route = routes[0]
        alt = route.get("altitudes_info") or {}
        try:
            max_angle = float(alt.get("max_road_angle") or 0.0)
        except (TypeError, ValueError):
            max_angle = 0.0

        if max_angle > 5.0:
            rebuilt, tries, info = await reroute_with_slope_limit(points_dict, params, max_angle_deg=5.0, max_tries=24)
            if rebuilt:
                return rebuilt
            raise HTTPException(status_code=400, detail=f"No safe route (<=5°) after {tries} attempts")

        disallowed_styles = {"undergroundway", "archway", "stairway"}
        disallowed_zlevels = {"zlevel-negative"}
        for man in (route.get("maneuvers") or []):
            path = man.get("outcoming_path") or {}
            for g in (path.get("geometry") or []):
                if isinstance(g, dict):
                    if g.get("style") in disallowed_styles:
                        raise HTTPException(status_code=400, detail=f"Inaccessible segment style: {g.get('style')}")
                    if g.get("zlevel") in disallowed_zlevels:
                        raise HTTPException(status_code=400, detail=f"Inaccessible segment zlevel: {g.get('zlevel')}")

        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post('/route/safely')
async def safely_router(request: AdaptiveRequest):
    points_dict = [p.model_dump() for p in request.points]
    
    base_params = {
        "filters": ["ban_stairway"],
        "need_altitudes": True,
        "route_mode": "shortest",
        "output": "detailed"
    }

    try:
        base_result = await call_routing_api(points_dict, base_params)
        if base_result.get("status") != "OK" or not (base_result.get("result") or []):
            raise HTTPException(status_code=502, detail="Routing API error (base)")
        
        base_route = base_result["result"][0]
        base_met = route_metrics(base_route)

        min_lat, min_lon, max_lat, max_lon = extract_bbox_from_route(base_result)
        if (min_lat, min_lon, max_lat, max_lon) == (0.0, 0.0, 0.0, 0.0):
            # фолбэк: построим bbox по старт/финиш
            start = (float(points_dict[0]["lat"]), float(points_dict[0]["lon"]))
            end   = (float(points_dict[-1]["lat"]), float(points_dict[-1]["lon"]))
            min_lat = min(start[0], end[0]); max_lat = max(start[0], end[0])
            min_lon = min(start[1], end[1]); max_lon = max(start[1], end[1])

        bbox_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        lit_midpoints = await get_lit_streets_overpass((min_lat, min_lon, max_lat, max_lon))
        open_places   = await get_open_places_2gis(bbox_str)

        all_via = []
        for a, b in zip(lit_midpoints, open_places):
            all_via.extend([a, b])
        if len(lit_midpoints) > len(open_places):
            all_via.extend(lit_midpoints[len(open_places):])
        elif len(open_places) > len(lit_midpoints):
            all_via.extend(open_places[len(lit_midpoints):])

        enhanced_points = points_dict + [
            {"type": "via", "lon": str(lon), "lat": str(lat)} for lon, lat in all_via
        ]

        safe_result = await call_routing_api(enhanced_points, base_params)
        if safe_result.get("status") != "OK" or not (safe_result.get("result") or []):
            # если не удалось — возвращаем базовый, но помечаем в заголовке
            headers = {
                "X-Route-mode": "safely",
                "X-Route-lit-bbox": bbox_str,
                "X-Route-lit-count": str(len(lit_midpoints)),
                "X-Route-open-places": str(len(open_places)),
                "X-Route-via-count": str(len(all_via)),
                "X-Route-time-base": f"{base_met['duration_s']}",
                "X-Route-time-safe": "NA",
                "X-Route-angle-base": f"{base_met['max_angle_deg']:.1f}",
                "X-Route-angle-safe": "NA",
                "X-Route-selected": "base",
            }
            return JSONResponse(content=base_result, headers=headers)
        
        safe_route = safe_result["result"][0]
        safe_met = route_metrics(safe_route)

        selected = "safe" if safe_met["max_angle_deg"] <= base_met["max_angle_deg"] else "base"
        response_payload = safe_result if selected == "safe" else base_result

        headers = {
            "X-Route-mode": "safely",
            "X-Route-lit-bbox": bbox_str,
            "X-Route-lit-count": str(len(lit_midpoints)),
            "X-Route-open-places": str(len(open_places)),
            "X-Route-via-count": str(len(all_via)),
            "X-Route-time-base": f"{base_met['duration_s']}",
            "X-Route-time-safe": f"{safe_met['duration_s']}",
            "X-Route-angle-base": f"{base_met['max_angle_deg']:.1f}",
            "X-Route-angle-safe": f"{safe_met['max_angle_deg']:.1f}",
            "X-Route-selected": selected,
        }

        return JSONResponse(content=response_payload, headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG: Ошибка в safely_router: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
