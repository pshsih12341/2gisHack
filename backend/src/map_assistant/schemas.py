from pydantic import BaseModel
from typing import List, Optional

class Point(BaseModel):
    lon: str
    lat: str
    type: str
    start: Optional[bool] = False

class AdaptiveRequest(BaseModel):
    points: List[Point]