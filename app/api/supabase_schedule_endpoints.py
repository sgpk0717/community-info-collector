"""
수파베이스 기반 스케줄링 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.supabase_schedule_service import supabase_schedule_service
from app.services.supabase_service import supabase_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])

@router.post("/create", response_model=Dict[str, Any])
async def create_schedule(schedule_data: Dict[str, Any]):
    """
    새로운 스케줄 생성
    """
    try:
        logger.info(f"📥 스케줄 생성 요청 | 키워드: {schedule_data.get('keyword')} | 주기: {schedule_data.get('interval_minutes')}분")
        
        # 사용자 닉네임 확인
        user_nickname = schedule_data.get("user_nickname")
        if not user_nickname:
            logger.error("사용자 닉네임이 없음")
            raise HTTPException(status_code=400, detail="사용자 닉네임이 필요합니다.")
        
        logger.info(f"사용자 닉네임: {user_nickname}")
        
        # 사용자 존재 확인
        user_result = await supabase_service.get_user_by_nickname(user_nickname)
        logger.info(f"사용자 조회 결과: {user_result}")
        
        if not user_result["success"]:
            logger.error(f"사용자를 찾을 수 없음: {user_nickname}")
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 스케줄 데이터 준비
        # start_time이 이미 ISO 형식의 문자열로 전달됨
        start_time_str = schedule_data.get("start_time")
        logger.info(f"받은 start_time: {start_time_str}")
        
        schedule_create_data = {
            "user_nickname": user_nickname,
            "keyword": schedule_data.get("keyword"),
            "interval_minutes": schedule_data.get("interval_minutes"),
            "total_reports": schedule_data.get("total_reports", 1),
            "completed_reports": 0,
            "report_length": "moderate",
            "status": "active",
            "notification_enabled": schedule_data.get("notification_enabled", False),
            "next_run": start_time_str,  # 그대로 전달
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # 스케줄 생성
        result = supabase_schedule_service.create_schedule(schedule_create_data)
        
        if result["success"]:
            # 기존 스케줄러 서비스는 사용하지 않음 (Supabase 스케줄러가 자동으로 처리)
            logger.info(f"✅ 새 스케줄 생성 완료 | ID: {result['data']['id']} | 사용자: {user_nickname} | 키워드: {schedule_data.get('keyword')}")
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 생성에 실패했습니다.")

@router.get("/user/{user_nickname}", response_model=Dict[str, Any])
async def get_user_schedules(user_nickname: str):
    """
    사용자의 스케줄 목록 조회
    """
    try:
        result = supabase_schedule_service.get_user_schedules(user_nickname)
        
        # 실행 중인 스케줄 정보 추가
        if result["success"] and result.get("schedules"):
            from app.services.supabase_scheduler_service import supabase_scheduler_service
            executing_schedules = supabase_scheduler_service.get_executing_schedules()
            logger.info(f"[API] Currently executing schedules: {executing_schedules}")
            
            for schedule in result["schedules"]:
                # 모든 스케줄의 is_executing을 기본값 False로 설정
                schedule["is_executing"] = False
                
                # ID 타입 확인 및 변환 (DB에서 오는 ID는 int, executing_schedules도 int여야 함)
                schedule_id = int(schedule["id"]) if isinstance(schedule["id"], str) else schedule["id"]
                
                # 실행 중인 스케줄 목록에 있으면 True로 변경
                if schedule_id in executing_schedules:
                    schedule["is_executing"] = True
                    
                logger.info(f"[API] Schedule ID: {schedule_id} (type: {type(schedule_id)}), executing_schedules: {executing_schedules}, is_executing: {schedule['is_executing']}")
        
        return result
    except Exception as e:
        logger.error(f"스케줄 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 목록 조회에 실패했습니다.")

@router.delete("/{schedule_id}", response_model=Dict[str, Any])
async def delete_schedule(schedule_id: str, force_delete: bool = False):
    """
    스케줄 삭제
    - force_delete=False: 상태를 cancelled로 변경 (기본)
    - force_delete=True: DB에서 완전 삭제
    """
    try:
        # Supabase 스케줄러가 자동으로 처리하므로 별도 제거 불필요
        logger.info(f"🗑️ 스케줄 삭제 처리 시작 | ID: {schedule_id}")
        
        # 수파베이스에서 삭제 처리
        result = supabase_schedule_service.delete_schedule(schedule_id, force_delete)
        
        if result["success"]:
            logger.info(f"스케줄 {'완전 삭제' if force_delete else '취소'}: {schedule_id}")
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 삭제에 실패했습니다.")

@router.patch("/{schedule_id}/status", response_model=Dict[str, Any])
async def update_schedule_status(schedule_id: str, status_data: Dict[str, Any]):
    """
    스케줄 상태 변경 (일시정지/재개)
    """
    try:
        action = status_data.get("action")
        
        if action == "pause":
            # Supabase 스케줄러가 자동으로 처리
            logger.info(f"⏸️ 스케줄 일시정지 요청 | ID: {schedule_id}")
            result = supabase_schedule_service.update_schedule_status(schedule_id, "paused")
            
        elif action == "resume":
            logger.info(f"▶️ 스케줄 재개 요청 | ID: {schedule_id}")
            result = supabase_schedule_service.update_schedule_status(schedule_id, "active")
                
        else:
            raise HTTPException(status_code=400, detail="올바르지 않은 액션입니다. 'pause' 또는 'resume'을 사용하세요.")
        
        if result["success"]:
            logger.info(f"스케줄 상태 변경: {schedule_id} -> {action}")
            return {
                "success": True,
                "message": f"스케줄이 {action}되었습니다.",
                "status": result["data"]["status"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 상태 변경 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 상태 변경에 실패했습니다.")

@router.get("/active", response_model=Dict[str, Any])
async def get_active_schedules():
    """
    실행 대기 중인 스케줄 조회 (스케줄러 서비스용)
    """
    try:
        result = supabase_schedule_service.get_active_schedules()
        return result
    except Exception as e:
        logger.error(f"활성 스케줄 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="활성 스케줄 조회에 실패했습니다.")

@router.post("/{schedule_id}/execute", response_model=Dict[str, Any])
async def update_schedule_execution(schedule_id: str, execution_data: Dict[str, Any]):
    """
    스케줄 실행 후 정보 업데이트
    """
    try:
        interval_minutes = execution_data.get("interval_minutes", 60)
        result = supabase_schedule_service.update_schedule_execution(schedule_id, interval_minutes)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스케줄 실행 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail="스케줄 실행 업데이트에 실패했습니다.")

@router.delete("/cancelled/{user_nickname}", response_model=Dict[str, Any])
async def delete_all_cancelled_schedules(user_nickname: str):
    """
    사용자의 취소된 스케줄 모두 삭제
    """
    try:
        result = supabase_schedule_service.delete_all_cancelled_schedules(user_nickname)
        
        if result["success"]:
            logger.info(f"사용자 {user_nickname}의 취소된 스케줄 {result['deleted_count']}개 삭제")
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"취소된 스케줄 일괄 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="취소된 스케줄 일괄 삭제에 실패했습니다.")

@router.get("/notifications/{user_nickname}", response_model=Dict[str, Any])
async def get_user_notifications(user_nickname: str, unread_only: bool = False):
    """
    사용자 알림 목록 조회
    """
    try:
        result = supabase_schedule_service.get_user_notifications(user_nickname, unread_only)
        return result
    except Exception as e:
        logger.error(f"알림 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="알림 목록 조회에 실패했습니다.")

@router.post("/notifications", response_model=Dict[str, Any])
async def create_notification(notification_data: Dict[str, Any]):
    """
    알림 생성
    """
    try:
        result = supabase_schedule_service.create_notification(notification_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 생성 오류: {e}")
        raise HTTPException(status_code=500, detail="알림 생성에 실패했습니다.")