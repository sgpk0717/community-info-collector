from supabase import create_client, Client
from app.core.config import settings
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import pytz
import uuid
import re
import ssl
import urllib3

# SSL 검증 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class SupabaseReportsService:
    def __init__(self):
        self.supabase: Client = None
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
            try:
                # SSL 컨텍스트 생성 (검증 비활성화)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
    
    async def save_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """보고서를 Supabase에 저장"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            report_id = str(uuid.uuid4())
            
            # 보고서에서 링크 추출
            links = self._extract_links_from_report(
                report_data.get("full_report", ""),
                report_data.get("posts_metadata", [])
            )
            
            # 보고서 데이터 준비 (posts_metadata 제외)
            report_record = {
                "id": report_id,
                "user_nickname": report_data.get("user_nickname"),
                "query_text": report_data.get("query_text"),
                "full_report": report_data.get("full_report"),
                "summary": report_data.get("summary"),
                "posts_collected": report_data.get("posts_collected", 0),
                "report_length": report_data.get("report_length", "moderate"),
                "session_id": report_data.get("session_id"),
                "created_at": datetime.now(pytz.timezone('Asia/Seoul')).isoformat()
            }
            
            # Supabase에 보고서 삽입
            result = self.supabase.table("reports").insert(report_record).execute()
            
            if result.data:
                logger.info(f"Report saved successfully: {report_id}")
                
                # 링크들을 별도 테이블에 저장
                if links:
                    link_records = []
                    for idx, link in enumerate(links):
                        link_record = {
                            "report_id": report_id,
                            "footnote_number": link["footnote_number"],
                            "url": link["url"],
                            "title": link.get("title"),
                            "score": link.get("score"),
                            "comments": link.get("comments"),
                            "created_utc": link.get("created_utc"),
                            "subreddit": link.get("subreddit"),
                            "author": link.get("author"),
                            "position_in_report": idx
                        }
                        link_records.append(link_record)
                    
                    # 링크들 일괄 삽입
                    links_result = self.supabase.table("report_links").insert(link_records).execute()
                    if links_result.data:
                        logger.info(f"Saved {len(link_records)} links for report {report_id}")
                
                return {
                    "success": True,
                    "data": result.data[0],
                    "report_id": report_id
                }
            else:
                logger.error(f"Failed to save report: {result}")
                return {"success": False, "error": "Failed to save report"}
                
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_reports(self, user_nickname: str, limit: int = 20) -> Dict[str, Any]:
        """사용자의 보고서 목록 조회"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # 사용자 보고서 조회 (최신순)
            result = self.supabase.table("reports")\
                .select("*")\
                .eq("user_nickname", user_nickname)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data is not None:
                logger.info(f"Retrieved {len(result.data)} reports for user: {user_nickname}")
                return {
                    "success": True,
                    "data": result.data,
                    "count": len(result.data)
                }
            else:
                logger.error(f"Failed to retrieve reports: {result}")
                return {"success": False, "error": "Failed to retrieve reports"}
                
        except Exception as e:
            logger.error(f"Error retrieving reports: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_report_by_id(self, report_id: str) -> Dict[str, Any]:
        """특정 보고서 조회"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            result = self.supabase.table("reports")\
                .select("*")\
                .eq("id", report_id)\
                .single()\
                .execute()
            
            if result.data:
                logger.info(f"Retrieved report: {report_id}")
                return {
                    "success": True,
                    "data": result.data
                }
            else:
                logger.error(f"Report not found: {report_id}")
                return {"success": False, "error": "Report not found"}
                
        except Exception as e:
            logger.error(f"Error retrieving report: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_links_from_report(self, full_report: str, posts_metadata: List[Dict]) -> List[Dict]:
        """보고서에서 링크 추출"""
        links = []
        
        # posts_metadata가 이미 footnote_number를 포함하고 있는 경우 (새 형식)
        if posts_metadata and isinstance(posts_metadata[0], dict) and 'footnote_number' in posts_metadata[0]:
            # 보고서에 실제로 사용된 각주 번호만 필터링
            used_footnotes = set()
            footnote_pattern = r'\[(\d+)\]'
            for match in re.findall(footnote_pattern, full_report):
                used_footnotes.add(int(match))
            
            # 사용된 각주에 해당하는 메타데이터만 반환
            for meta in posts_metadata:
                if meta['footnote_number'] in used_footnotes:
                    links.append(meta)
        else:
            # 기존 형식 처리: [숫자](URL)
            footnote_pattern = r'\[(\d+)\]\((https?://[^\)]+)\)'
            matches = re.findall(footnote_pattern, full_report)
            
            # URL을 메타데이터로 매핑
            metadata_map = {}
            for meta in posts_metadata:
                if meta.get("url"):
                    metadata_map[meta["url"]] = meta
            
            for footnote_number, url in matches:
                link_info = {
                    "footnote_number": int(footnote_number),
                    "url": url
                }
                
                # 메타데이터가 있으면 추가
                if url in metadata_map:
                    meta = metadata_map[url]
                    link_info.update({
                        "title": meta.get("title"),
                        "score": meta.get("score"),
                        "comments": meta.get("comments"),
                        "created_utc": meta.get("created_utc"),
                        "subreddit": meta.get("subreddit"),
                        "author": meta.get("author")
                    })
                
                links.append(link_info)
        
        return links
    
    async def get_report_links(self, report_id: str) -> Dict[str, Any]:
        """특정 보고서의 링크 목록 조회"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            result = self.supabase.table("report_links")\
                .select("*")\
                .eq("report_id", report_id)\
                .order("position_in_report")\
                .execute()
            
            if result.data is not None:
                logger.info(f"Retrieved {len(result.data)} links for report: {report_id}")
                return {
                    "success": True,
                    "data": result.data
                }
            else:
                return {"success": False, "error": "Failed to retrieve links"}
                
        except Exception as e:
            logger.error(f"Error retrieving report links: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_report(self, report_id: str, user_nickname: str) -> Dict[str, Any]:
        """보고서 삭제 (사용자 권한 확인)"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # 삭제 (사용자 권한 확인)
            result = self.supabase.table("reports")\
                .delete()\
                .eq("id", report_id)\
                .eq("user_nickname", user_nickname)\
                .execute()
            
            if result.data:
                logger.info(f"Report deleted: {report_id}")
                return {"success": True, "data": result.data}
            else:
                logger.error(f"Failed to delete report or permission denied: {report_id}")
                return {"success": False, "error": "Failed to delete report or permission denied"}
                
        except Exception as e:
            logger.error(f"Error deleting report: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_report_stats(self, user_nickname: str) -> Dict[str, Any]:
        """사용자의 보고서 통계"""
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"success": False, "error": "Database connection failed"}
        
        try:
            # 전체 보고서 수
            count_result = self.supabase.table("reports")\
                .select("id", count="exact")\
                .eq("user_nickname", user_nickname)\
                .execute()
            
            # 최근 7일 보고서 수
            recent_result = self.supabase.table("reports")\
                .select("id", count="exact")\
                .eq("user_nickname", user_nickname)\
                .gte("created_at", datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat())\
                .execute()
            
            return {
                "success": True,
                "data": {
                    "total_reports": count_result.count or 0,
                    "recent_reports": recent_result.count or 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving report stats: {e}")
            return {"success": False, "error": str(e)}

# 전역 Supabase 보고서 서비스
supabase_reports_service = SupabaseReportsService()