"""
Router for Map Assistant API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from ..chatbot import MapAssistant, RoutePoint, RouteResponse, RouteSegment, Route, RouteStage, EnhancedRouteResponse


router = APIRouter(prefix="/map", tags=["Map Assistant"])


class RouteRequest(BaseModel):
    """Request model for route planning."""
    query: str
    region_id: Optional[str] = "moscow"


class RoutePointResponse(BaseModel):
    """Response model for route point."""
    name: str
    latitude: float
    longitude: float
    point_type: str
    description: Optional[str] = None
    address: Optional[str] = None


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
        points_response = [
            RoutePointResponse(
                name=point.name,
                latitude=point.latitude,
                longitude=point.longitude,
                point_type=point.point_type,
                description=point.description,
                address=point.address
            )
            for point in response.points
        ]
        
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
                        point_type=stage.start_point.point_type,
                        description=stage.start_point.description,
                        address=stage.start_point.address
                    )
                
                stage_end_point = None
                if stage.end_point:
                    stage_end_point = RoutePointResponse(
                        name=stage.end_point.name,
                        latitude=stage.end_point.latitude,
                        longitude=stage.end_point.longitude,
                        point_type=stage.end_point.point_type,
                        description=stage.end_point.description,
                        address=stage.end_point.address
                    )
                
                stage_waypoints = None
                if stage.waypoints:
                    stage_waypoints = [
                        RoutePointResponse(
                            name=wp.name,
                            latitude=wp.latitude,
                            longitude=wp.longitude,
                            point_type=wp.point_type,
                            description=wp.description,
                            address=wp.address
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
