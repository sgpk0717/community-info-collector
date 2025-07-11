from sqlalchemy.orm import Session
from app.models.models import Schedule, ScheduleStatus
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ScheduleService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_schedule(self, schedule_data: Dict[str, Any]) -> Schedule:
        """새로운 스케줄 생성"""
        try:
            # 스케줄 생성
            schedule = Schedule(
                user_id=schedule_data.get("user_id"),
                keyword=schedule_data.get("keyword"),
                interval_minutes=schedule_data.get("interval_minutes"),
                report_length=schedule_data.get("report_length", "moderate"),
                total_reports=schedule_data.get("total_reports"),
                completed_reports=0,
                sources=schedule_data.get("sources", ["reddit", "twitter", "threads"]),
                status=ScheduleStatus.ACTIVE,
                next_run=schedule_data.get("next_run"),
                created_at=datetime.utcnow()
            )
            
            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)
            
            logger.info(f"스케줄 생성 성공: ID={schedule.id}, keyword={schedule.keyword}")
            return schedule
            
        except Exception as e:
            logger.error(f"스케줄 생성 실패: {e}")
            self.db.rollback()
            raise
    
    async def get_schedule(self, schedule_id: int) -> Schedule:
        """스케줄 조회"""
        return self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    async def update_schedule(self, schedule_id: int, update_data: Dict[str, Any]) -> Schedule:
        """스케줄 업데이트"""
        schedule = await self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"스케줄을 찾을 수 없습니다: {schedule_id}")
        
        for key, value in update_data.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        schedule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(schedule)
        
        return schedule
    
    async def get_active_schedules(self) -> List[Schedule]:
        """활성 스케줄 목록 조회"""
        return self.db.query(Schedule).filter(
            Schedule.status == ScheduleStatus.ACTIVE
        ).all()
    
    async def get_user_schedules(self, user_id: int) -> List[Schedule]:
        """사용자의 스케줄 목록 조회"""
        return self.db.query(Schedule).filter(
            Schedule.user_id == user_id
        ).order_by(Schedule.created_at.desc()).all()