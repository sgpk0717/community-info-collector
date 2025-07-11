import asyncio
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ProgressService:
    def __init__(self):
        self.progress_manager = None
    
    def set_progress_manager(self, manager):
        self.progress_manager = manager
    
    async def update_progress(self, session_id: str, stage: str, percentage: int, message: str, details: Optional[str] = None):
        """진행 상태 업데이트"""
        if not self.progress_manager:
            return
        
        progress_data = {
            "session_id": session_id,
            "stage": stage,
            "percentage": percentage,
            "message": message,
            "details": details or "",
            "timestamp": datetime.now().isoformat()
        }
        
        await self.progress_manager.send_progress(session_id, progress_data)
        logger.info(f"Progress update: {session_id} - {stage} ({percentage}%) - {message}")

# 전역 진행 상태 서비스
progress_service = ProgressService()