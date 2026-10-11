"""行程路由"""
from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.context import request_id_var
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.errors import BizError, ErrorCode
from app.core.ratelimit import limiter
from app.models.generation_task import GenerationTask
from app.models.trip import Trip
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.trip import (
    TaskAcceptedResponse,
    TaskStatusResponse,
    TripDetail,
    TripRequest,
    TripSaveRequest,
    TripSummary,
)

router = APIRouter(prefix="/trips", tags=["行程"])


@router.post(
    "/generate",
    response_model=TaskAcceptedResponse,
    status_code=202,
    summary="提交生成任务（异步）",
)
@limiter.limit(lambda: get_settings().rate_limit_generate)
def generate_trip(request: Request, payload: TripRequest, db: Session = Depends(get_db)):
    """创建生成任务并入队，立即返回 task_id 供前端轮询，不再同步等待。

    用 send_task 按名字入队：web 进程无需导入 LangChain/MCP 栈，保持轻量；
    任务实现只在 worker 侧加载。该接口是 LLM/MCP 长任务的入口，按 IP 限流防刷。
    """
    from app.core.celery_app import celery_app

    task = GenerationTask(request=payload.model_dump(), request_id=request_id_var.get())
    db.add(task)
    db.commit()
    db.refresh(task)
    celery_app.send_task("app.tasks.generate.generate_trip_task", args=[task.id])
    return TaskAcceptedResponse(task_id=task.id, status=task.status)


@router.get("/generate/{task_id}", response_model=TaskStatusResponse, summary="查询生成任务状态")
def get_generate_task(task_id: str, db: Session = Depends(get_db)):
    """轮询生成任务，返回状态与（完成时）计划。"""
    task = db.get(GenerationTask, task_id)
    if task is None:
        raise BizError(ErrorCode.GENERATION_TASK_NOT_FOUND)
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        plan=task.plan,  # type: ignore[arg-type]
        error=task.error,
    )


@router.post("", response_model=TripSummary, summary="保存行程")
def save_trip(
    request: TripSaveRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
        raise BizError(ErrorCode.TRIP_NOT_FOUND)
    return TripDetail.model_validate(trip)


@router.delete("/{trip_id}", response_model=MessageResponse, summary="删除行程")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        raise BizError(ErrorCode.TRIP_NOT_FOUND)
    db.delete(trip)
    db.commit()
    return MessageResponse(success=True, message="行程已删除")
