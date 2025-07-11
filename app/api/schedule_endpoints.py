"""
스케줄링 관련 API 엔드포인트
사용자가 설정한 주기에 따라 자동으로 보고서를 생성하고 알림을 발송
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas.schemas import (
    UserCreate, UserUpdate, UserResponse,
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    NotificationResponse, ScheduleStatusEnum
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedule", tags=["schedule"])

# 사용자 관련 엔드포인트
@router.post("/users", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """
    새 사용자 등록 또는 기존 사용자 정보 반환
    """
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

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

# =============================================================================
# 새로운 닉네임 기반 스케줄링 API 엔드포인트
# =============================================================================

@router.post("/schedules", response_model=dict)
async def create_new_schedule(
    schedule_data: dict,
    db: Session = Depends(get_db)
):
    """
    새로운 스케줄 생성 (닉네임 기반)
    """
    try:
        from app.services.supabase_service import supabase_service
        
        # 사용자 닉네임으로 조회
        user_nickname = schedule_data.get("user_nickname")
        if not user_nickname:
            raise HTTPException(status_code=400, detail="사용자 닉네임이 필요합니다.")
        
        # 기존 SQLite 방식 유지
        schedule = Schedule(
            user_nickname=user_nickname,  # 직접 nickname 사용
            keyword=schedule_data.get("keyword"),
            interval_minutes=schedule_data.get("interval_minutes"),
            total_reports=schedule_data.get("total_reports", 1),
            completed_reports=0,
            report_length="moderate",  # 기본값
            status="active",
            notification_enabled=schedule_data.get("notification_enabled", False),
            next_run=datetime.fromisoformat(schedule_data.get("start_time").replace('Z', '+00:00'))
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        # 스케줄러에 등록
        from app.services.scheduler_service import scheduler_service
        scheduler_service.add_schedule(schedule.id)
        
        logger.info(f"새 스케줄 생성: {schedule.id} (사용자: {user_nickname})")
        
        return {
            "success": True,
            "data": {
                "id": schedule.id,
                "keyword": schedule.keyword,
                "interval_minutes": schedule.interval_minutes,
                "total_reports": schedule.total_reports,
                "status": schedule.status.value,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "created_at": schedule.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 생성 오류: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="스케줄 생성에 실패했습니다.")

@router.get("/schedules/user/{user_nickname}", response_model=dict)
async def get_user_schedules_by_nickname(
    user_nickname: str,
    db: Session = Depends(get_db)
):
    """
    사용자의 스케줄 목록 조회 (닉네임 기반)
    """
    try:
        # 기존 SQLite 방식: user_nickname으로 직접 조회
        schedules = db.query(Schedule).filter(
            Schedule.user_nickname == user_nickname
        ).order_by(Schedule.created_at.desc()).all()
        
        schedule_list = []
        for schedule in schedules:
            schedule_list.append({
                "id": schedule.id,
                "keyword": schedule.keyword,
                "interval_minutes": schedule.interval_minutes,
                "total_reports": schedule.total_reports,
                "completed_reports": schedule.completed_reports,
                "status": schedule.status.value,
                "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
                "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                "created_at": schedule.created_at.isoformat()
            })
        
        return {
            "success": True,
            "schedules": schedule_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 목록 조회에 실패했습니다.")

@router.delete("/schedules/{schedule_id}", response_model=dict)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
):
    """
    스케줄 삭제
    """
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다.")
        
        # 스케줄러에서 제거
        from app.services.scheduler_service import scheduler_service
        scheduler_service.remove_schedule(schedule_id)
        
        # 데이터베이스에서 상태 변경 (soft delete)
        schedule.status = ScheduleStatus.CANCELLED
        schedule.next_run = None
        db.commit()
        
        logger.info(f"스케줄 삭제: {schedule_id}")
        
        return {
            "success": True,
            "message": "스케줄이 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 삭제에 실패했습니다.")

@router.patch("/schedules/{schedule_id}/status", response_model=dict)
async def update_schedule_status(
    schedule_id: int,
    status_data: dict,
    db: Session = Depends(get_db)
):
    """
    스케줄 상태 변경 (일시정지/재개)
    """
    try:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="스케줄을 찾을 수 없습니다.")
        
        action = status_data.get("action")
        
        if action == "pause":
            if schedule.status != ScheduleStatus.ACTIVE:
                raise HTTPException(status_code=400, detail="활성 상태인 스케줄만 일시정지할 수 있습니다.")
            
            schedule.status = ScheduleStatus.PAUSED
            
            # 스케줄러에서 제거
            from app.services.scheduler_service import scheduler_service
            scheduler_service.remove_schedule(schedule_id)
            
        elif action == "resume":
            if schedule.status != ScheduleStatus.PAUSED:
                raise HTTPException(status_code=400, detail="일시정지된 스케줄만 재개할 수 있습니다.")
            
            schedule.status = ScheduleStatus.ACTIVE
            schedule.next_run = datetime.utcnow() + timedelta(minutes=schedule.interval_minutes)
            
            # 스케줄러에 다시 등록
            from app.services.scheduler_service import scheduler_service
            scheduler_service.add_schedule(schedule_id)
            
        else:
            raise HTTPException(status_code=400, detail="올바르지 않은 액션입니다. 'pause' 또는 'resume'을 사용하세요.")
        
        db.commit()
        
        logger.info(f"스케줄 상태 변경: {schedule_id} -> {action}")
        
        return {
            "success": True,
            "message": f"스케줄이 {action}되었습니다.",
            "status": schedule.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 상태 변경 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 상태 변경에 실패했습니다.")