"""行程路由"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from app.agents.graph import run_planner
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import PlanResponse, TripDetail, TripPlan, TripRequest, TripSaveRequest, TripSummary

router = APIRouter(prefix="/trips", tags=["行程"])


def _serialize_created_at(trip: Trip) -> str:
    return trip.created_at.isoformat() if trip.created_at else ""


@router.post("/generate", response_model=PlanResponse, summary="生成旅行计划（不保存）")
async def generate_trip(request: TripRequest):
    """调用 LangGraph 生成计划，但不入库（用于首页即时预览）"""
    try:
        state = {
            "city": request.city,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "travel_days": request.travel_days,
            "transportation": request.transportation,
            "accommodation": request.accommodation,
            "preferences": request.preferences,
            "free_text": request.free_text,
        }
        result = await run_planner(state)
        plan_dict = result.get("plan")
        if not plan_dict:
            raise ValueError("LLM 未返回有效计划")
        return PlanResponse(success=True, message="旅行计划生成成功", data=TripPlan.model_validate(plan_dict))
    except Exception as e:
        logger.exception("生成计划失败")
        raise HTTPException(status_code=500, detail=f"生成旅行计划失败: {str(e)}")


@router.post("", response_model=TripSummary, summary="保存行程")
def save_trip(request: TripSaveRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = Trip(
        user_id=user.id,
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        travel_days=request.travel_days,
        transportation=request.transportation,
        accommodation=request.accommodation,
        preferences=request.preferences,
        free_text=request.free_text,
        plan=request.plan,
        status="completed",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return TripSummary.model_validate(trip)


@router.get("", response_model=List[TripSummary], summary="我的行程列表")
def list_trips(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trips = db.query(Trip).filter(Trip.user_id == user.id).order_by(Trip.created_at.desc()).all()
    return [TripSummary.model_validate(t) for t in trips]


@router.get("/{trip_id}", response_model=TripDetail, summary="行程详情")
def get_trip(trip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    return TripDetail.model_validate(trip)


@router.delete("/{trip_id}", summary="删除行程")
def delete_trip(trip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    db.delete(trip)
    db.commit()
    return {"success": True, "message": "行程已删除"}
