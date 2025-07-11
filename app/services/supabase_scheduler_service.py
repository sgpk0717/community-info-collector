#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수파베이스 기반 스케줄러 서비스
"""
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.supabase_schedule_service import supabase_schedule_service
from app.services.reddit_service import RedditService
from app.services.llm_service import LLMService
from app.services.supabase_reports_service import supabase_reports_service
from app.services.verified_analysis_service import VerifiedAnalysisService
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

class SupabaseSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.reddit_service = RedditService()
        self.llm_service = LLMService()
        self.verified_analysis_service = VerifiedAnalysisService()
        # 메모리 기반 실행 추적 (서버 재시작 시 초기화됨)
        self._executing_schedules = set()
        self._is_running = False
        
    def get_executing_schedules(self):
        """현재 실행 중인 스케줄 ID 목록 반환 (int 타입으로 보장)"""
        return list(self._executing_schedules)
        
    async def start(self):
        """스케줄러 시작"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
            
        # 서버 시작 시 모든 is_executing 플래그 초기화
        await self._reset_all_executing_flags()
        
        # 1분마다 실행되는 job 추가
        self.scheduler.add_job(
            self._check_and_execute_schedules,
            IntervalTrigger(minutes=1),
            id="check_schedules",
            name="Check and execute schedules",
            replace_existing=True
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info("🚀 스케줄러 서비스 시작 | 체크 주기: 1분")
        
    async def stop(self):
        """스케줄러 중지"""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            # 중지 시 모든 is_executing 플래그 초기화
            await self._reset_all_executing_flags()
            logger.info("Supabase Scheduler service stopped")
            
    async def _reset_all_executing_flags(self):
        """모든 스케줄의 is_executing 플래그를 false로 초기화"""
        try:
            result = await supabase_schedule_service.reset_all_executing_flags()
            if result["success"]:
                logger.info(f"🔄 실행 플래그 초기화 완료 | 리셋된 스케줄: {result['reset_count']}개")
            else:
                logger.error(f"Failed to reset executing flags: {result['message']}")
        except Exception as e:
            logger.error(f"Error resetting executing flags: {e}")
            
    async def _check_and_execute_schedules(self):
        """실행해야 할 스케줄 확인 및 실행"""
        current_time = datetime.utcnow()
        # 한국 시간으로 표시
        import pytz
        kst = pytz.timezone('Asia/Seoul')
        current_kst = current_time.replace(tzinfo=pytz.UTC).astimezone(kst)
        logger.debug(f"⏰ 스케줄 체크 시작 | 시간: {current_kst.strftime('%H:%M:%S')} KST (UTC: {current_time.strftime('%H:%M:%S')})")
        if self.get_executing_schedules():
            logger.debug(f"   현재 실행 중: {self.get_executing_schedules()}")
        
        try:
            # 실행 대기 중인 스케줄 조회 (is_executing=False인 것만)
            schedules = await supabase_schedule_service.get_schedules_to_execute()
            
            if schedules:
                logger.info(f"📋 검사할 스케줄: {len(schedules)}개")
                
                for schedule in schedules:
                    schedule_id = int(schedule["id"])
                    
                    # 이미 실행 중인지 메모리에서도 확인
                    if schedule_id in self._executing_schedules:
                        logger.debug(f"⚠️ 스케줄 {schedule_id} 이미 실행 중 (메모리 체크)")
                        continue
                    
                    # 실행 시간이 되었는지 확인
                    next_run = datetime.fromisoformat(schedule["next_run"].replace("Z", ""))
                    if next_run <= current_time:
                        # DB 레벨에서 원자적으로 락 획득 시도
                        lock_acquired = await supabase_schedule_service.try_acquire_schedule_lock(schedule_id)
                        
                        if lock_acquired:
                            logger.info(f"🔒 스케줄 {schedule_id} 락 획득 성공 | 키워드: {schedule.get('keyword')}")
                            # 메모리에도 추가
                            self._executing_schedules.add(schedule_id)
                            # 비동기로 실행
                            asyncio.create_task(self._execute_schedule_with_lock(schedule))
                        else:
                            logger.debug(f"⏳ 스케줄 {schedule_id} 다른 곳에서 실행 중")
                    else:
                        # 한국 시간으로 표시
                        next_run_kst = next_run.replace(tzinfo=pytz.UTC).astimezone(kst)
                        logger.debug(f"⏱️ 스케줄 {schedule_id} 아직 실행 시간 아님 | 예정: {next_run_kst.strftime('%H:%M')} KST")
                        
        except Exception as e:
            logger.error(f"[SCHEDULER] Error checking schedules: {e}")
            
    async def _execute_schedule_with_lock(self, schedule):
        """락을 획득한 스케줄 실행 (락 해제 보장)"""
        schedule_id = int(schedule["id"])
        
        try:
            await self._execute_schedule(schedule)
        finally:
            # 항상 락 해제
            await supabase_schedule_service.release_schedule_lock(schedule_id)
            # 메모리에서도 제거
            self._executing_schedules.discard(schedule_id)
            logger.info(f"🔓 스케줄 {schedule_id} 락 해제 완료")
            
    async def _execute_schedule(self, schedule):
        """스케줄 실행"""
        max_retries = 3
        retry_count = 0
        execution_successful = False
        
        while retry_count < max_retries and not execution_successful:
            try:
                schedule_id = int(schedule["id"])
                logger.info(f"🚀 스케줄 실행 시작 | ID: {schedule_id} | 시도: {retry_count + 1}/{max_retries}")
                
                # 진행 상태 세션 ID 생성
                session_id = f"schedule_{schedule_id}_{uuid.uuid4().hex[:8]}"
                
                # 1. Reddit 데이터 수집
                logger.info(f"🔍 Reddit 데이터 수집 중 | 키워드: '{schedule['keyword']}'")
                posts = await self.reddit_service.collect_reddit_posts(schedule["keyword"])
                
                if not posts:
                    logger.warning(f"[SCHEDULER] No posts found for schedule {schedule_id}")
                    # 데이터가 없어도 실행은 성공으로 처리
                    execution_successful = True
                    break
                
                logger.info(f"   수집 완료: {len(posts)}개 게시물")
                
                # 2. 보고서 생성
                logger.info(f"📝 AI 보고서 생성 중...")
                report_result = await self.verified_analysis_service.generate_verified_report(
                    query=schedule["keyword"],
                    posts=posts,
                    report_length=schedule.get("report_length", "moderate"),
                    session_id=session_id
                )
                
                # 3. 보고서 저장
                report_data = {
                    "query_text": schedule["keyword"],  # search_query 대신 query_text 사용
                    "summary": report_result.get("summary", "요약 없음"),
                    "full_report": report_result.get("full_report", "보고서 없음"),
                    "search_metadata": {
                        "sources": ["reddit"],
                        "posts_count": len(posts),
                        "schedule_id": schedule_id
                    },
                    "user_nickname": schedule.get("user_nickname"),
                    "session_id": session_id,
                    "posts_metadata": report_result.get("post_mappings", [])
                }
                
                save_result = await supabase_reports_service.save_report(report_data)
                
                if save_result["success"]:
                    logger.info(f"✅ 보고서 저장 완료 | 스케줄 ID: {schedule_id}")
                    
                    # 4. 스케줄 업데이트 (성공 시에만)
                    # save_result에서 report_id 가져오기 (report_id 또는 data.id)
                    report_id = save_result.get("report_id")
                    if not report_id and save_result.get("data"):
                        report_id = save_result["data"].get("id")
                    
                    if not report_id:
                        logger.error(f"❌ 보고서 ID를 찾을 수 없음 | save_result: {save_result}")
                        raise Exception("Report ID not found in save result")
                    
                    update_result = await supabase_schedule_service.update_schedule_after_execution(
                        schedule_id=schedule_id,
                        interval_minutes=schedule.get("interval_minutes", 60),
                        report_id=report_id
                    )
                    
                    if update_result["success"]:
                        logger.info(f"✅ 스케줄 업데이트 완료 | ID: {schedule_id} | 다음 실행: {schedule.get('interval_minutes')}분 후")
                        execution_successful = True
                        
                        # 5. 알림 생성 (선택사항)
                        if schedule.get("notification_enabled"):
                            await self._create_notification(schedule, report_id)
                    else:
                        logger.error(f"[SCHEDULER] Failed to update schedule: {update_result['message']}")
                        raise Exception(f"Schedule update failed: {update_result['message']}")
                else:
                    logger.error(f"[SCHEDULER] Failed to save report: {save_result['message']}")
                    raise Exception(f"Report save failed: {save_result['message']}")
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"[SCHEDULER] Error executing schedule {schedule['id']} (attempt {retry_count}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"[SCHEDULER] Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    logger.error(f"[SCHEDULER] Max retries reached for schedule {schedule['id']}")
                    
                    # 최대 재시도 후에도 실패하면 스케줄 상태를 에러로 변경
                    if schedule.get("notification_enabled"):
                        await self._create_error_notification(schedule, str(e))
                        
        # 실행 실패 시 다음 실행 시간만 업데이트 (completed_reports는 증가시키지 않음)
        if not execution_successful:
            logger.error(f"[SCHEDULER] Schedule {schedule['id']} execution failed after all retries")
            # 실패해도 다음 실행 시간은 업데이트하여 무한 재시도 방지
            await supabase_schedule_service.update_next_run_only(
                schedule_id=schedule["id"],
                interval_minutes=schedule.get("interval_minutes", 60)
            )
                        
    async def _create_notification(self, schedule, report_id):
        """보고서 생성 완료 알림 생성"""
        try:
            notification_data = {
                "user_nickname": schedule.get("user_nickname"),
                "title": "보고서 생성 완료",
                "message": f"'{schedule['keyword']}' 키워드에 대한 보고서가 생성되었습니다.",
                "type": "report_completed",
                "data": {
                    "schedule_id": schedule["id"],
                    "report_id": report_id,
                    "keyword": schedule["keyword"]
                }
            }
            
            result = await supabase_schedule_service.create_notification_async(notification_data)
            if result["success"]:
                logger.info(f"[SCHEDULER] Notification created for schedule {schedule['id']}")
            else:
                logger.error(f"[SCHEDULER] Failed to create notification: {result['message']}")
                
        except Exception as e:
            logger.error(f"[SCHEDULER] Error creating notification: {e}")
            
    async def _create_error_notification(self, schedule, error_message):
        """보고서 생성 실패 알림 생성"""
        try:
            notification_data = {
                "user_nickname": schedule.get("user_nickname"),
                "title": "보고서 생성 실패",
                "message": f"'{schedule['keyword']}' 키워드에 대한 보고서 생성에 실패했습니다.",
                "type": "report_failed",
                "data": {
                    "schedule_id": schedule["id"],
                    "keyword": schedule["keyword"],
                    "error": error_message
                }
            }
            
            result = await supabase_schedule_service.create_notification_async(notification_data)
            if result["success"]:
                logger.info(f"[SCHEDULER] Error notification created for schedule {schedule['id']}")
                
        except Exception as e:
            logger.error(f"[SCHEDULER] Error creating error notification: {e}")

# 전역 인스턴스 생성
supabase_scheduler_service = SupabaseSchedulerService()