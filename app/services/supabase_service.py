import os
from supabase import create_client, Client
from typing import Dict, Any, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Supabase 클라이언트 초기화"""
        try:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                logger.warning("Supabase 설정이 없습니다. 사용자 관련 기능이 비활성화됩니다.")
                return
                
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase 클라이언트가 성공적으로 초기화되었습니다.")
        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {e}")
            self.supabase = None
    
    def is_available(self) -> bool:
        """Supabase 서비스 사용 가능 여부"""
        return self.supabase is not None
    
    async def register_user(self, nickname: str) -> Dict[str, Any]:
        """사용자 등록"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            # 닉네임을 소문자로 변환
            nickname_lower = nickname.lower()
            
            # 닉네임 중복 체크 (대소문자 구분 없이)
            existing_user = self.supabase.table('users').select('id').ilike('nickname', nickname_lower).execute()
            
            if existing_user.data:
                return {"success": False, "error": "NICKNAME_EXISTS"}
            
            # 새 사용자 생성 (원본 닉네임 저장)
            result = self.supabase.table('users').insert({
                'nickname': nickname,
                'approval_status': 'N'
            }).execute()
            
            if result.data:
                return {
                    "success": True,
                    "data": {
                        "id": result.data[0]['id'],
                        "nickname": result.data[0]['nickname'],
                        "approval_status": result.data[0]['approval_status'],
                        "created_at": result.data[0]['created_at']
                    }
                }
            else:
                return {"success": False, "error": "REGISTRATION_FAILED"}
                
        except Exception as e:
            logger.error(f"사용자 등록 오류: {e}")
            return {"success": False, "error": "REGISTRATION_FAILED"}
    
    async def login_user(self, nickname: str) -> Dict[str, Any]:
        """사용자 로그인 (닉네임 확인)"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            # 사용자 조회 (대소문자 구분 없이)
            result = self.supabase.table('users').select('*').ilike('nickname', nickname).execute()
            
            if not result.data:
                return {"success": False, "error": "USER_NOT_FOUND"}
            
            user = result.data[0]
            
            # 마지막 접속 시간 업데이트
            self.supabase.table('users').update({
                'last_access': 'now()'
            }).eq('id', user['id']).execute()
            
            return {
                "success": True,
                "data": {
                    "id": user['id'],
                    "nickname": user['nickname'],
                    "status": "approved" if user['approval_status'] == 'Y' else "pending",
                    "created_at": user['created_at'],
                    "last_access": user['last_access']
                }
            }
            
        except Exception as e:
            logger.error(f"사용자 로그인 오류: {e}")
            return {"success": False, "error": "LOGIN_FAILED"}
    
    async def get_pending_users(self) -> Dict[str, Any]:
        """승인 대기 중인 사용자 목록 조회"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            result = self.supabase.table('users').select('*').eq('approval_status', 'N').order('created_at', desc=True).execute()
            
            return {
                "success": True,
                "data": result.data
            }
            
        except Exception as e:
            logger.error(f"대기 사용자 조회 오류: {e}")
            return {"success": False, "error": "FETCH_FAILED"}
    
    async def approve_user(self, user_id: str) -> Dict[str, Any]:
        """사용자 승인"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            result = self.supabase.table('users').update({
                'approval_status': 'Y'
            }).eq('id', user_id).execute()
            
            if result.data:
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "APPROVAL_FAILED"}
                
        except Exception as e:
            logger.error(f"사용자 승인 오류: {e}")
            return {"success": False, "error": "APPROVAL_FAILED"}
    
    async def get_all_users(self) -> Dict[str, Any]:
        """모든 사용자 조회"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            result = self.supabase.table('users').select('*').order('created_at', desc=True).execute()
            
            return {
                "success": True,
                "data": result.data
            }
            
        except Exception as e:
            logger.error(f"사용자 목록 조회 오류: {e}")
            return {"success": False, "error": "FETCH_FAILED"}
    
    async def get_user_by_nickname(self, nickname: str) -> Dict[str, Any]:
        """닉네임으로 사용자 조회"""
        if not self.is_available():
            return {"success": False, "error": "SUPABASE_NOT_AVAILABLE"}
        
        try:
            # 사용자 조회 (대소문자 구분 없이)
            result = self.supabase.table('users').select('*').ilike('nickname', nickname).execute()
            
            if not result.data:
                return {"success": False, "error": "USER_NOT_FOUND"}
            
            user = result.data[0]
            return {
                "success": True,
                "data": {
                    "id": user['id'],
                    "nickname": user['nickname'],
                    "approval_status": user['approval_status'],
                    "created_at": user['created_at']
                }
            }
            
        except Exception as e:
            logger.error(f"사용자 조회 오류: {e}")
            return {"success": False, "error": "FETCH_FAILED"}

# 싱글톤 인스턴스
supabase_service = SupabaseService()