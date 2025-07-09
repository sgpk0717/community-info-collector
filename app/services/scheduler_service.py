"""
백그라운드 스케줄러 서비스
APScheduler를 사용하여 주기적으로 보고서를 생성하고 알림을 발송
"""
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.models import Schedule, ScheduleStatus, Report, Notification, SearchQuery, CollectedPost
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.reddit_service = RedditService()
        self.llm_service = LLMService()
        self.notification_service = NotificationService()
        self.is_running = False
        
    def start(self):
        """스케줄러 시작"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Scheduler service started")
            
            # 기존 활성 스케줄 복원
            self._restore_active_schedules()
    
    def stop(self):
        """스케줄러 중지"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler service stopped")
    
    def _restore_active_schedules(self):
        """서버 재시작 시 활성 스케줄 복원"""
        db = SessionLocal()
        try:
            active_schedules = db.query(Schedule).filter(
                Schedule.status == ScheduleStatus.ACTIVE,
                Schedule.next_run.isnot(None)
            ).all()
            
            for schedule in active_schedules:
                self.add_schedule(schedule.id)
                logger.info(f"Restored schedule {schedule.id}")
                
        except Exception as e:
            logger.error(f"Error restoring schedules: {e}")
        finally:
            db.close()
    
    def add_schedule(self, schedule_id: int):
        """새로운 스케줄 추가"""
        job_id = f"schedule_{schedule_id}"
        
        # 이미 존재하는 job이면 제거
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        db = SessionLocal()
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                return
            
            # 인터벌 트리거 생성
            trigger = IntervalTrigger(
                minutes=schedule.interval_minutes,
                start_date=schedule.next_run or datetime.utcnow()
            )
            
            # job 추가
            self.scheduler.add_job(
                self._execute_schedule,
                trigger=trigger,
                id=job_id,
                args=[schedule_id],
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Added schedule job {job_id}")
            
        except Exception as e:
            logger.error(f"Error adding schedule: {e}")
        finally:
            db.close()
    
    def remove_schedule(self, schedule_id: int):
        """스케줄 제거"""
        job_id = f"schedule_{schedule_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed schedule job {job_id}")
    
    async def _execute_schedule(self, schedule_id: int):
        """스케줄 실행 - 보고서 생성 및 알림 발송"""
        db = SessionLocal()
        try:
            # 스케줄 조회
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule or schedule.status != ScheduleStatus.ACTIVE:
                return
            
            logger.info(f"Executing schedule {schedule_id} for keyword: {schedule.keyword}")
            
            # 1. Reddit에서 데이터 수집
            posts = await self.reddit_service.search_posts(schedule.keyword)
            
            if not posts:
                logger.warning(f"No posts found for keyword: {schedule.keyword}")
                return
            
            # 2. 검색 쿼리 저장
            search_query = SearchQuery(query_text=schedule.keyword)
            db.add(search_query)
            db.commit()
            db.refresh(search_query)
            
            # 3. 수집된 포스트 저장
            for post_data in posts:
                post = CollectedPost(
                    source=post_data.source,
                    post_id=post_data.post_id,
                    author=post_data.author,
                    title=post_data.title,
                    content=post_data.content,
                    url=post_data.url,
                    search_query_id=search_query.id
                )
                db.add(post)
            db.commit()
            
            # 4. LLM으로 보고서 생성 (보고서 길이 고려)
            report_data = await self.llm_service.generate_report(
                schedule.keyword, 
                posts,
                report_length=schedule.report_length
            )
            
            # 5. 보고서 저장
            report = Report(
                search_query_id=search_query.id,
                summary=report_data["summary"],
                full_report=report_data["full_report"],
                schedule_id=schedule.id,
                user_id=schedule.user.device_id
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            
            # 6. 완료된 보고서 수 증가
            schedule.completed_reports += 1
            schedule.last_run = datetime.utcnow()
            
            # 7. 다음 실행 시간 설정 또는 완료 처리
            if schedule.completed_reports >= schedule.total_reports:
                # 총 보고 횟수 도달 - 스케줄 완료
                schedule.status = ScheduleStatus.COMPLETED
                schedule.next_run = None
                self.remove_schedule(schedule_id)
                
                # 완료 알림
                notification = Notification(
                    user_id=schedule.user_id,
                    title=f"스케줄 완료: {schedule.keyword}",
                    body=f"'{schedule.keyword}'에 대한 {schedule.total_reports}개의 보고서가 모두 생성되었습니다.",
                    data={"schedule_id": schedule_id, "type": "schedule_completed"}
                )
                db.add(notification)
                
                logger.info(f"Schedule {schedule_id} completed all reports")
            else:
                # 다음 실행 예약
                schedule.next_run = datetime.utcnow() + timedelta(minutes=schedule.interval_minutes)
                
                # 보고서 생성 알림
                notification = Notification(
                    user_id=schedule.user_id,
                    title=f"새 보고서: {schedule.keyword}",
                    body=f"'{schedule.keyword}'에 대한 새로운 분석 보고서가 생성되었습니다.",
                    data={
                        "schedule_id": schedule_id,
                        "report_id": report.id,
                        "type": "new_report"
                    }
                )
                db.add(notification)
            
            db.commit()
            
            # 8. 푸시 알림 발송
            if schedule.user.push_token:
                await self.notification_service.send_push_notification(
                    schedule.user.push_token,
                    notification.title,
                    notification.body,
                    notification.data
                )
            
            logger.info(f"Successfully executed schedule {schedule_id}")
            
        except Exception as e:
            logger.error(f"Error executing schedule {schedule_id}: {e}")
            
            # 에러 발생 시 재시도를 위해 다음 실행 시간 설정
            if schedule:
                schedule.next_run = datetime.utcnow() + timedelta(minutes=schedule.interval_minutes)
                db.commit()
                
        finally:
            db.close()

# 전역 스케줄러 인스턴스
scheduler_service = SchedulerService()