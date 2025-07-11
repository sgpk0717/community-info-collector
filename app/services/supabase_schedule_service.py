"""
수파베이스 스케줄링 서비스
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseScheduleService:
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase URL and Service Key are required")
        
        self.supabase: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
    
    def _ensure_utc_format(self, time_str: Optional[str]) -> Optional[str]:
        """시간 문자열이 UTC 형식인지 확인하고 필요시 Z 추가"""
        if not time_str:
            return time_str
        
        # 이미 Z나 +00:00 같은 타임존 정보가 있으면 그대로 반환
        if time_str.endswith('Z') or '+' in time_str or time_str.endswith('+00:00'):
            return time_str
        
        # 타임존 정보가 없으면 Z 추가
        return time_str + 'Z'
    
    def _format_schedule_times(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """스케줄의 시간 필드들을 UTC 형식으로 변환"""
        schedule["next_run"] = self._ensure_utc_format(schedule.get("next_run"))
        schedule["last_run"] = self._ensure_utc_format(schedule.get("last_run"))
        schedule["created_at"] = self._ensure_utc_format(schedule.get("created_at"))
        schedule["updated_at"] = self._ensure_utc_format(schedule.get("updated_at"))
        return schedule
    
    def create_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """스케줄 생성"""
        try:
            response = self.supabase.table("schedules").insert(schedule_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "스케줄 생성에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"스케줄 생성 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_user_schedules(self, user_nickname: str) -> Dict[str, Any]:
        """사용자의 스케줄 목록 조회"""
        try:
            response = self.supabase.table("schedules")\
                .select("*")\
                .eq("user_nickname", user_nickname)\
                .order("created_at", desc=True)\
                .execute()
            
            return {
                "success": True,
                "schedules": [self._format_schedule_times(schedule) for schedule in response.data]
            }
        except Exception as e:
            logger.error(f"스케줄 목록 조회 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 목록 조회 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_schedule_by_id(self, schedule_id: str) -> Dict[str, Any]:
        """스케줄 ID로 조회"""
        try:
            response = self.supabase.table("schedules")\
                .select("*")\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "스케줄을 찾을 수 없습니다."
                }
        except Exception as e:
            logger.error(f"스케줄 조회 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 조회 중 오류가 발생했습니다: {str(e)}"
            }
    
    def update_schedule_status(self, schedule_id: str, status: str) -> Dict[str, Any]:
        """스케줄 상태 업데이트"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # 재개 시 다음 실행 시간 설정
            if status == "active":
                # 기존 스케줄 정보 조회
                schedule_result = self.get_schedule_by_id(schedule_id)
                if schedule_result["success"]:
                    schedule = schedule_result["data"]
                    next_run = datetime.utcnow() + timedelta(minutes=schedule["interval_minutes"])
                    update_data["next_run"] = next_run.isoformat()
            
            response = self.supabase.table("schedules")\
                .update(update_data)\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "스케줄 상태 업데이트에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"스케줄 상태 업데이트 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
            }
    
    def delete_schedule(self, schedule_id: str, force_delete: bool = False) -> Dict[str, Any]:
        """스케줄 삭제 (기본: 상태를 cancelled로 변경, force_delete=True: DB에서 완전 삭제)"""
        try:
            # 먼저 현재 스케줄 상태 확인
            schedule_result = self.get_schedule_by_id(schedule_id)
            if not schedule_result["success"]:
                return schedule_result
            
            current_status = schedule_result["data"]["status"]
            
            # 이미 취소된 스케줄이거나 force_delete가 True면 완전 삭제
            if current_status == "cancelled" or force_delete:
                response = self.supabase.table("schedules")\
                    .delete()\
                    .eq("id", schedule_id)\
                    .execute()
                
                if response.data:
                    return {
                        "success": True,
                        "message": "스케줄이 완전히 삭제되었습니다."
                    }
                else:
                    return {
                        "success": False,
                        "message": "스케줄 삭제에 실패했습니다."
                    }
            else:
                # 아직 취소되지 않은 스케줄은 cancelled 상태로 변경
                response = self.supabase.table("schedules")\
                    .update({
                        "status": "cancelled",
                        "next_run": None,
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("id", schedule_id)\
                    .execute()
                
                if response.data:
                    return {
                        "success": True,
                        "message": "스케줄이 취소되었습니다."
                    }
                else:
                    return {
                        "success": False,
                        "message": "스케줄 취소에 실패했습니다."
                    }
        except Exception as e:
            logger.error(f"스케줄 삭제 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 삭제 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_active_schedules(self) -> Dict[str, Any]:
        """실행 대기 중인 스케줄 조회"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            # is_executing이 False인 스케줄만 조회 (동시 실행 방지)
            response = self.supabase.table("schedules")\
                .select("*")\
                .eq("status", "active")\
                .eq("is_executing", False)\
                .lte("next_run", current_time)\
                .execute()
            
            # 디버깅 로그 추가
            logger.info(f"Checking active schedules at UTC time: {current_time}")
            logger.info(f"Found {len(response.data)} active schedules")
            
            return {
                "success": True,
                "schedules": [self._format_schedule_times(schedule) for schedule in response.data]
            }
        except Exception as e:
            logger.error(f"활성 스케줄 조회 오류: {e}")
            return {
                "success": False,
                "message": f"활성 스케줄 조회 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def get_schedules_to_execute(self) -> List[Dict[str, Any]]:
        """실행해야 할 스케줄 목록 조회 (비동기)"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            # is_executing이 없는 경우를 대비하여 기본값 처리
            response = self.supabase.table("schedules")\
                .select("*")\
                .eq("status", "active")\
                .lte("next_run", current_time)\
                .execute()
            
            # is_executing이 False인 것만 필터링
            schedules = []
            for schedule in response.data:
                if not schedule.get("is_executing", False):  # 기본값 False
                    schedules.append(self._format_schedule_times(schedule))
            
            logger.info(f"Found {len(schedules)} schedules ready to execute")
            return schedules
        except Exception as e:
            logger.error(f"Error getting schedules to execute: {e}")
            return []
    
    async def try_acquire_schedule_lock(self, schedule_id: int) -> bool:
        """스케줄 실행 락 획득 시도 (원자적 업데이트)"""
        try:
            # 원자적으로 is_executing을 False에서 True로 변경
            # 이미 True인 경우 업데이트되지 않음
            response = self.supabase.table("schedules")\
                .update({
                    "is_executing": True,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .eq("is_executing", False)\
                .execute()
            
            if response.data:
                logger.info(f"Successfully acquired lock for schedule {schedule_id}")
                return True
            else:
                logger.info(f"Failed to acquire lock for schedule {schedule_id} - already executing")
                return False
        except Exception as e:
            logger.error(f"Error acquiring schedule lock: {e}")
            return False
    
    def mark_schedule_executing(self, schedule_id: str, is_executing: bool) -> Dict[str, Any]:
        """스케줄 실행 상태 변경"""
        try:
            response = self.supabase.table("schedules")\
                .update({
                    "is_executing": is_executing,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                logger.info(f"Schedule {schedule_id} marked as executing={is_executing}")
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "스케줄 실행 상태 업데이트에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"스케줄 실행 상태 업데이트 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 실행 상태 업데이트 중 오류가 발생했습니다: {str(e)}"
            }
    
    def update_schedule_execution(self, schedule_id: str, interval_minutes: int) -> Dict[str, Any]:
        """스케줄 실행 후 다음 실행 시간 업데이트"""
        try:
            # 먼저 현재 completed_reports 조회
            current_schedule = self.supabase.table("schedules")\
                .select("completed_reports")\
                .eq("id", schedule_id)\
                .execute()
            
            if not current_schedule.data:
                return {
                    "success": False,
                    "message": "스케줄을 찾을 수 없습니다."
                }
            
            current_count = current_schedule.data[0]["completed_reports"]
            next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
            
            # 업데이트 실행 (is_executing도 False로 리셋)
            response = self.supabase.table("schedules")\
                .update({
                    "last_run": datetime.utcnow().isoformat(),
                    "next_run": next_run.isoformat(),
                    "completed_reports": current_count + 1,
                    "is_executing": False,  # 실행 완료 후 False로 리셋
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "스케줄 실행 정보 업데이트에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"스케줄 실행 업데이트 오류: {e}")
            return {
                "success": False,
                "message": f"스케줄 실행 업데이트 중 오류가 발생했습니다: {str(e)}"
            }
    
    def reset_all_executing_flags(self) -> Dict[str, Any]:
        """모든 스케줄의 is_executing 플래그를 초기화 (서버 시작 시 호출)"""
        try:
            response = self.supabase.table("schedules")\
                .update({
                    "is_executing": False,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("is_executing", True)\
                .execute()
            
            count = len(response.data) if response.data else 0
            logger.info(f"Reset {count} executing flags on startup")
            
            return {
                "success": True,
                "reset_count": count
            }
        except Exception as e:
            logger.error(f"Error resetting executing flags: {e}")
            return {
                "success": False,
                "message": f"Error resetting executing flags: {str(e)}"
            }
    
    def create_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """알림 생성"""
        try:
            response = self.supabase.table("notifications").insert(notification_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "알림 생성에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"알림 생성 오류: {e}")
            return {
                "success": False,
                "message": f"알림 생성 중 오류가 발생했습니다: {str(e)}"
            }
    
    def delete_all_cancelled_schedules(self, user_nickname: str) -> Dict[str, Any]:
        """사용자의 취소된 스케줄 모두 삭제"""
        try:
            # 먼저 취소된 스케줄 목록 조회
            response = self.supabase.table("schedules")\
                .select("id")\
                .eq("user_nickname", user_nickname)\
                .eq("status", "cancelled")\
                .execute()
            
            if not response.data:
                return {
                    "success": True,
                    "message": "삭제할 취소된 스케줄이 없습니다.",
                    "deleted_count": 0
                }
            
            # 취소된 스케줄들의 ID 목록
            cancelled_ids = [schedule["id"] for schedule in response.data]
            
            # 일괄 삭제
            delete_response = self.supabase.table("schedules")\
                .delete()\
                .in_("id", cancelled_ids)\
                .execute()
            
            return {
                "success": True,
                "message": f"{len(cancelled_ids)}개의 취소된 스케줄이 삭제되었습니다.",
                "deleted_count": len(cancelled_ids)
            }
        except Exception as e:
            logger.error(f"취소된 스케줄 일괄 삭제 오류: {e}")
            return {
                "success": False,
                "message": f"취소된 스케줄 일괄 삭제 중 오류가 발생했습니다: {str(e)}"
            }
    
    def get_user_notifications(self, user_nickname: str, unread_only: bool = False) -> Dict[str, Any]:
        """사용자 알림 목록 조회"""
        try:
            query = self.supabase.table("notifications")\
                .select("*")\
                .eq("user_nickname", user_nickname)
            
            if unread_only:
                query = query.eq("is_read", False)
            
            response = query.order("sent_at", desc=True).limit(50).execute()
            
            return {
                "success": True,
                "notifications": response.data
            }
        except Exception as e:
            logger.error(f"알림 목록 조회 오류: {e}")
            return {
                "success": False,
                "message": f"알림 목록 조회 중 오류가 발생했습니다: {str(e)}"
            }
    
    async def release_schedule_lock(self, schedule_id: int) -> Dict[str, Any]:
        """스케줄 실행 락 해제"""
        try:
            response = self.supabase.table("schedules")\
                .update({
                    "is_executing": False,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                logger.info(f"Released lock for schedule {schedule_id}")
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to release schedule lock"
                }
        except Exception as e:
            logger.error(f"Error releasing schedule lock: {e}")
            return {
                "success": False,
                "message": f"Error releasing schedule lock: {str(e)}"
            }
    
    async def update_schedule_after_execution(self, schedule_id: int, interval_minutes: int, report_id: str) -> Dict[str, Any]:
        """스케줄 실행 후 업데이트 (completed_reports 증가, next_run 업데이트)"""
        try:
            # 먼저 현재 상태 조회
            current_schedule = self.supabase.table("schedules")\
                .select("completed_reports, total_reports")\
                .eq("id", schedule_id)\
                .execute()
            
            if not current_schedule.data:
                return {
                    "success": False,
                    "message": "Schedule not found"
                }
            
            current_count = current_schedule.data[0]["completed_reports"]
            total_reports = current_schedule.data[0]["total_reports"]
            next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
            
            # 모든 보고서가 완료되었는지 확인
            new_status = "active"
            if current_count + 1 >= total_reports:
                new_status = "completed"
            
            # 업데이트
            response = self.supabase.table("schedules")\
                .update({
                    "last_run": datetime.utcnow().isoformat(),
                    "next_run": next_run.isoformat() if new_status == "active" else None,
                    "completed_reports": current_count + 1,
                    "status": new_status,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated schedule {schedule_id} after execution. Status: {new_status}")
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update schedule"
                }
        except Exception as e:
            logger.error(f"Error updating schedule after execution: {e}")
            return {
                "success": False,
                "message": f"Error updating schedule: {str(e)}"
            }
    
    async def update_next_run_only(self, schedule_id: int, interval_minutes: int) -> Dict[str, Any]:
        """다음 실행 시간만 업데이트 (실패 시 사용)"""
        try:
            next_run = datetime.utcnow() + timedelta(minutes=interval_minutes)
            
            response = self.supabase.table("schedules")\
                .update({
                    "next_run": next_run.isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", schedule_id)\
                .execute()
            
            if response.data:
                logger.info(f"Updated next_run for schedule {schedule_id}")
                return {
                    "success": True,
                    "data": self._format_schedule_times(response.data[0])
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update next_run"
                }
        except Exception as e:
            logger.error(f"Error updating next_run: {e}")
            return {
                "success": False,
                "message": f"Error updating next_run: {str(e)}"
            }
    
    async def reset_all_executing_flags(self) -> Dict[str, Any]:
        """모든 스케줄의 is_executing 플래그를 초기화 (비동기 버전)"""
        try:
            response = self.supabase.table("schedules")\
                .update({
                    "is_executing": False,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("is_executing", True)\
                .execute()
            
            count = len(response.data) if response.data else 0
            logger.info(f"Reset {count} executing flags")
            
            return {
                "success": True,
                "reset_count": count
            }
        except Exception as e:
            logger.error(f"Error resetting executing flags: {e}")
            return {
                "success": False,
                "message": f"Error resetting executing flags: {str(e)}"
            }
    
    async def create_notification_async(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """알림 생성 (비동기 버전)"""
        # 동기 버전 호출
        try:
            response = self.supabase.table("notifications").insert(notification_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "data": response.data[0]
                }
            else:
                return {
                    "success": False,
                    "message": "알림 생성에 실패했습니다."
                }
        except Exception as e:
            logger.error(f"알림 생성 오류: {e}")
            return {
                "success": False,
                "message": f"알림 생성 중 오류가 발생했습니다: {str(e)}"
            }

# 싱글톤 인스턴스
supabase_schedule_service = SupabaseScheduleService()