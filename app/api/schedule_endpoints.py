"""
스케줄링 관련 API 엔드포인트
사용자가 설정한 주기에 따라 자동으로 보고서를 생성하고 알림을 발송
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.base import get_db
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    NotificationResponse, ScheduleStatusEnum
)
from app.models.models import User, Schedule, ScheduleStatus, Notification
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedule", tags=["schedule"])

# 사용자 관련 엔드포인트
@router.post("/users", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    새 사용자 등록 또는 기존 사용자 정보 반환
    """
    # 기존 사용자 확인
    existing_user = db.query(User).filter(User.device_id == user_data.device_id).first()
    
    if existing_user:
        # 푸시 토큰 업데이트
        if user_data.push_token:
            existing_user.push_token = user_data.push_token
            db.commit()
            db.refresh(existing_user)
        return existing_user
    
    # 새 사용자 생성
    new_user = User(
        device_id=user_data.device_id,
        name=user_data.name,
        push_token=user_data.push_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.put("/users/{device_id}", response_model=UserResponse)
async def update_user(
    device_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    사용자 정보 업데이트 (이름, 푸시 토큰)
    """
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.push_token is not None:
        user.push_token = user_update.push_token
    
    db.commit()
    db.refresh(user)
    return user

# 스케줄 관련 엔드포인트
@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    device_id: str,
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db)
):
    """
    새로운 스케줄 생성
    
    - **device_id**: 사용자 디바이스 ID
    - **keyword**: 분석할 키워드
    - **interval_minutes**: 실행 주기 (분)
    - **report_length**: 보고서 길이 (simple, moderate, detailed)
    - **total_reports**: 총 보고 횟수
    """
    # 사용자 확인
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 다음 실행 시간 계산
    next_run = datetime.utcnow() + timedelta(minutes=schedule_data.interval_minutes)
    
    # 스케줄 생성
    new_schedule = Schedule(
        user_id=user.id,
        keyword=schedule_data.keyword,
        interval_minutes=schedule_data.interval_minutes,
        report_length=schedule_data.report_length,
        total_reports=schedule_data.total_reports,
        next_run=next_run
    )
    
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    logger.info(f"Created schedule {new_schedule.id} for user {user.device_id}")
    
    return new_schedule

@router.get("/schedules", response_model=List[ScheduleResponse])
async def get_user_schedules(
    device_id: str,
    status: Optional[ScheduleStatusEnum] = None,
    db: Session = Depends(get_db)
):
    """
    사용자의 모든 스케줄 조회
    
    - **device_id**: 사용자 디바이스 ID
    - **status**: 필터링할 상태 (active, paused, completed, cancelled)
    """
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Schedule).filter(Schedule.user_id == user.id)
    
    if status:
        query = query.filter(Schedule.status == status)
    
    schedules = query.order_by(Schedule.created_at.desc()).all()
    return schedules

@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    특정 스케줄 상세 정보 조회
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule

@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_update: ScheduleUpdate,
    db: Session = Depends(get_db)
):
    """
    스케줄 수정 (상태 변경, 주기 변경 등)
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # 상태 변경
    if schedule_update.status is not None:
        schedule.status = ScheduleStatus(schedule_update.status)
        
        # 취소된 경우 다음 실행 시간 제거
        if schedule_update.status == ScheduleStatusEnum.cancelled:
            schedule.next_run = None
    
    # 주기 변경
    if schedule_update.interval_minutes is not None:
        schedule.interval_minutes = schedule_update.interval_minutes
        # 다음 실행 시간 재계산
        if schedule.status == ScheduleStatus.ACTIVE:
            schedule.next_run = datetime.utcnow() + timedelta(minutes=schedule_update.interval_minutes)
    
    # 총 보고 횟수 변경
    if schedule_update.total_reports is not None:
        schedule.total_reports = schedule_update.total_reports
    
    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    
    return schedule

@router.delete("/schedules/{schedule_id}")
async def cancel_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    스케줄 취소 (soft delete - 상태를 cancelled로 변경)
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.status = ScheduleStatus.CANCELLED
    schedule.next_run = None
    schedule.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Schedule {schedule_id} has been cancelled"}

@router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    스케줄 일시정지
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.status != ScheduleStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Schedule is not active")
    
    schedule.status = ScheduleStatus.PAUSED
    schedule.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Schedule {schedule_id} has been paused"}

@router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """
    일시정지된 스케줄 재개
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule.status != ScheduleStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Schedule is not paused")
    
    schedule.status = ScheduleStatus.ACTIVE
    # 다음 실행 시간 재설정
    schedule.next_run = datetime.utcnow() + timedelta(minutes=schedule.interval_minutes)
    schedule.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Schedule {schedule_id} has been resumed"}

# 알림 관련 엔드포인트
@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    device_id: str,
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    사용자의 알림 목록 조회
    """
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Notification).filter(Notification.user_id == user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(Notification.sent_at.desc()).limit(limit).all()
    return notifications

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """
    알림을 읽음으로 표시
    """
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@router.get("/schedules/stats/{device_id}")
async def get_schedule_stats(device_id: str, db: Session = Depends(get_db)):
    """
    사용자의 스케줄 통계 조회
    """
    user = db.query(User).filter(User.device_id == device_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 활성 스케줄 수
    active_schedules = db.query(Schedule).filter(
        Schedule.user_id == user.id,
        Schedule.status == ScheduleStatus.ACTIVE
    ).count()
    
    # 완료된 스케줄 수
    completed_schedules = db.query(Schedule).filter(
        Schedule.user_id == user.id,
        Schedule.status == ScheduleStatus.COMPLETED
    ).count()
    
    # 총 생성된 보고서 수
    total_reports = db.query(Schedule).filter(
        Schedule.user_id == user.id
    ).with_entities(db.func.sum(Schedule.completed_reports)).scalar() or 0
    
    return {
        "active_schedules": active_schedules,
        "completed_schedules": completed_schedules,
        "total_reports_generated": total_reports,
        "user_since": user.created_at
    }