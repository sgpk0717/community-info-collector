from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.schemas.schemas import UserRegisterRequest, UserLoginRequest, UserAuthResponse, SupabaseUserResponse
from app.services.supabase_service import supabase_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=Dict[str, Any])
async def register_user(request: UserRegisterRequest):
    """사용자 등록"""
    try:
        result = await supabase_service.register_user(request.nickname)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            error_code = result.get("error", "UNKNOWN_ERROR")
            if error_code == "NICKNAME_EXISTS":
                raise HTTPException(status_code=409, detail="닉네임이 이미 사용 중입니다.")
            elif error_code == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=400, detail="사용자 등록에 실패했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 등록 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.post("/login", response_model=Dict[str, Any])
async def login_user(request: UserLoginRequest):
    """사용자 로그인"""
    try:
        result = await supabase_service.login_user(request.nickname)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            error_code = result.get("error", "UNKNOWN_ERROR")
            if error_code == "USER_NOT_FOUND":
                raise HTTPException(status_code=404, detail="등록되지 않은 닉네임입니다.")
            elif error_code == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=400, detail="로그인에 실패했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 로그인 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.get("/pending", response_model=Dict[str, Any])
async def get_pending_users():
    """승인 대기 중인 사용자 목록 조회 (관리자용)"""
    try:
        result = await supabase_service.get_pending_users()
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            error_code = result.get("error", "UNKNOWN_ERROR")
            if error_code == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=400, detail="사용자 목록 조회에 실패했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대기 사용자 조회 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.post("/approve/{user_id}", response_model=Dict[str, Any])
async def approve_user(user_id: str):
    """사용자 승인 (관리자용)"""
    try:
        result = await supabase_service.approve_user(user_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            error_code = result.get("error", "UNKNOWN_ERROR")
            if error_code == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=400, detail="사용자 승인에 실패했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 승인 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.get("/all", response_model=Dict[str, Any])
async def get_all_users():
    """모든 사용자 조회 (관리자용)"""
    try:
        result = await supabase_service.get_all_users()
        
        if result["success"]:
            return {
                "success": True,
                "data": result["data"]
            }
        else:
            error_code = result.get("error", "UNKNOWN_ERROR")
            if error_code == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=400, detail="사용자 목록 조회에 실패했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 목록 조회 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.get("/status")
async def get_user_service_status():
    """사용자 서비스 상태 확인"""
    return {
        "service": "user_service",
        "available": supabase_service.is_available(),
        "provider": "supabase"
    }

@router.get("/check-nickname/{nickname}", response_model=Dict[str, Any])
async def check_nickname_duplicate(nickname: str):
    """닉네임 중복 확인"""
    try:
        result = await supabase_service.get_user_by_nickname(nickname)
        
        # 사용자가 있으면 중복
        if result["success"]:
            return {
                "success": True,
                "available": False,
                "message": "이미 사용 중인 닉네임입니다."
            }
        else:
            # 사용자가 없으면 사용 가능
            if result.get("error") == "USER_NOT_FOUND":
                return {
                    "success": True,
                    "available": True,
                    "message": "사용 가능한 닉네임입니다."
                }
            elif result.get("error") == "SUPABASE_NOT_AVAILABLE":
                raise HTTPException(status_code=503, detail="사용자 서비스를 사용할 수 없습니다.")
            else:
                raise HTTPException(status_code=500, detail="닉네임 확인 중 오류가 발생했습니다.")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"닉네임 중복 확인 API 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")