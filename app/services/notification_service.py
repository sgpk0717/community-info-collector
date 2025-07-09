"""
푸시 알림 서비스
Firebase Cloud Messaging (FCM)을 사용하여 모바일 앱에 푸시 알림 발송
"""
import os
import json
import httpx
from typing import Optional, Dict
import logging
from google.oauth2 import service_account
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.fcm_project_id = os.getenv("FCM_PROJECT_ID")
        self.fcm_credentials_path = os.getenv("FCM_CREDENTIALS_PATH")
        self.fcm_api_url = f"https://fcm.googleapis.com/v1/projects/{self.fcm_project_id}/messages:send"
        self._credentials = None
        self._access_token = None
        
        if not self.fcm_project_id or not self.fcm_credentials_path:
            logger.warning("FCM configuration not found. Push notifications will be disabled.")
    
    def _get_access_token(self):
        """FCM 액세스 토큰 획득"""
        if not self.fcm_credentials_path or not os.path.exists(self.fcm_credentials_path):
            return None
            
        try:
            if not self._credentials:
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.fcm_credentials_path,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
            
            # 토큰이 만료되었거나 없으면 새로 발급
            if not self._access_token or self._credentials.expired:
                self._credentials.refresh(Request())
                self._access_token = self._credentials.token
                
            return self._access_token
            
        except Exception as e:
            logger.error(f"Error getting FCM access token: {e}")
            return None
    
    async def send_push_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        FCM을 통해 푸시 알림 발송
        
        Args:
            token: 디바이스 FCM 토큰
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
            
        Returns:
            성공 여부
        """
        if not self.fcm_project_id:
            logger.warning("FCM not configured, skipping push notification")
            return False
            
        access_token = self._get_access_token()
        if not access_token:
            logger.error("Failed to get FCM access token")
            return False
        
        # FCM 메시지 구성
        message = {
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body
                },
                "android": {
                    "priority": "high",
                    "notification": {
                        "sound": "default",
                        "click_action": "FLUTTER_NOTIFICATION_CLICK"
                    }
                },
                "apns": {
                    "payload": {
                        "aps": {
                            "sound": "default",
                            "badge": 1
                        }
                    }
                }
            }
        }
        
        # 추가 데이터가 있으면 포함
        if data:
            message["message"]["data"] = {k: str(v) for k, v in data.items()}
        
        # FCM API 호출
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.fcm_api_url,
                    headers=headers,
                    json=message
                )
                
                if response.status_code == 200:
                    logger.info(f"Push notification sent successfully to {token[:10]}...")
                    return True
                else:
                    logger.error(f"Failed to send push notification: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def send_batch_notifications(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        여러 디바이스에 동시에 푸시 알림 발송
        
        Args:
            tokens: 디바이스 FCM 토큰 리스트
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
            
        Returns:
            각 토큰별 성공 여부
        """
        results = {}
        
        # 동시에 여러 알림 발송
        import asyncio
        tasks = []
        for token in tokens:
            task = self.send_push_notification(token, title, body, data)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for token, response in zip(tokens, responses):
            if isinstance(response, Exception):
                results[token] = False
                logger.error(f"Error sending to {token[:10]}...: {response}")
            else:
                results[token] = response
        
        return results

# 개발 환경에서 FCM 없이 테스트하기 위한 Mock 서비스
class MockNotificationService(NotificationService):
    """개발/테스트용 Mock 알림 서비스"""
    
    async def send_push_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> bool:
        """Mock 푸시 알림 - 로그만 출력"""
        logger.info(f"[MOCK] Push notification - Token: {token[:10]}..., Title: {title}, Body: {body}, Data: {data}")
        return True

# 환경에 따라 적절한 서비스 사용
def get_notification_service():
    if os.getenv("ENVIRONMENT") == "development" or not os.getenv("FCM_PROJECT_ID"):
        return MockNotificationService()
    return NotificationService()