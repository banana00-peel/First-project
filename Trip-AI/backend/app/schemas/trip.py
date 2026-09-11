"""行程相关 schema"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------- 请求 ----------
class TripRequest(BaseModel):
    city: str = Field(min_length=1, max_length=32)
    start_date: str
    end_date: str
    travel_days: int = Field(ge=1, le=30)
    transportation: str = "公共交通"
    accommodation: str = "经济型酒店"
    preferences: List[str] = Field(default_factory=list)
    free_text: str = ""


class TripSaveRequest(TripRequest):
    """保存行程：除请求字段外，附带生成的计划"""
    plan: dict = Field(default_factory=dict)


# ---------- 计划结构 ----------
class Location(BaseModel):
    name: str
    address: str = ""
    longitude: float = 0.0
    latitude: float = 0.0


class Attraction(BaseModel):
    name: str
    description: str = ""
    address: str = ""
    location: Optional[Location] = None
    suggested_duration: str = ""
    image_url: str = ""


class Meal(BaseModel):
    name: str
    description: str = ""
    cuisine: str = ""
    price_range: str = ""


class Hotel(BaseModel):
    name: str
    address: str = ""
    price_range: str = ""
    rating: str = ""
    location: Optional[Location] = None


class RouteSegment(BaseModel):
    """每日行程中相邻景点之间的交通路线（由 enrich 节点确定性生成）"""
    from_name: str = ""
    to_name: str = ""
    mode: str = ""              # walking / driving / transit
    distance_m: int = 0
    duration_s: int = 0
    summary: str = ""
    steps: List[str] = Field(default_factory=list)


class WeatherInfo(BaseModel):
    date: str
    weather: str = ""
    temperature: str = ""
    wind: str = ""
    humidity: str = ""

    @field_validator("temperature", mode="before")
    @classmethod
    def strip_celsius(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.replace("°C", "").replace("℃", "").strip()
        return v


class Budget(BaseModel):
    total: str = ""
    breakdown: dict = Field(default_factory=dict)


class DayPlan(BaseModel):
    day: int
    date: str = ""
    title: str = ""
    attractions: List[Attraction] = Field(default_factory=list)
    meals: List[Meal] = Field(default_factory=list)
    hotel: Optional[Hotel] = None
    transportation_tips: str = ""
    routes: List[RouteSegment] = Field(default_factory=list)
    notes: str = ""


class TripPlan(BaseModel):
    city: str
    start_date: str
    end_date: str
    travel_days: int
    overview: str = ""
    days: List[DayPlan] = Field(default_factory=list)
    weather: List[WeatherInfo] = Field(default_factory=list)
    budget: Optional[Budget] = None
    tips: List[str] = Field(default_factory=list)


# ---------- 响应 ----------
class TripSummary(BaseModel):
    id: int
    city: str
    start_date: str
    end_date: str
    travel_days: int
    status: str
    created_at: str

    class Config:
        from_attributes = True

    @field_validator("created_at", mode="before")
    @classmethod
    def _serialize_dt(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)


class TripDetail(TripSummary):
    transportation: str = ""
    accommodation: str = ""
    preferences: List[str] = Field(default_factory=list)
    free_text: str = ""
    plan: dict = Field(default_factory=dict)


class PlanResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[TripPlan] = None
