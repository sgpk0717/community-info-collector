from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ProgressManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.active_sessions: Set[str] = set()
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[session_id] = websocket
        self.active_sessions.add(session_id)
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.connections:
            del self.connections[session_id]
        if session_id in self.active_sessions:
            self.active_sessions.remove(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_progress(self, session_id: str, progress_data: dict):
        if session_id in self.connections:
            try:
                await self.connections[session_id].send_text(json.dumps(progress_data))
                logger.debug(f"Progress sent to {session_id}: {progress_data}")
            except Exception as e:
                logger.error(f"Error sending progress to {session_id}: {e}")
                self.disconnect(session_id)

# 전역 진행 상태 관리자
progress_manager = ProgressManager()

@router.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await progress_manager.connect(session_id, websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (연결 유지용)
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        progress_manager.disconnect(session_id)