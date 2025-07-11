from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class PushNotificationService:
    def __init__(self):
        # Default host is fine for Expo push service
        self.client = PushClient()
    
    async def send_analysis_complete_notification(
        self, 
        push_token: str, 
        user_nickname: str,
        keyword: str,
        report_id: str
    ) -> bool:
        """분석 완료 알림 전송"""
        if not push_token:
            logger.info(f"No push token for user {user_nickname}, skipping notification")
            return False
        
        # Expo Go 더미 토큰 체크
        if push_token == 'expo-go-dummy-token':
            logger.info(f"Expo Go dummy token detected for {user_nickname}, skipping push notification")
            return False
            
        try:
            # Check that all push tokens are valid
            if not PushClient.is_exponent_push_token(push_token):
                logger.error(f"Invalid push token: {push_token}")
                return False
            
            # Create the messages to send
            message = PushMessage(
                to=push_token,
                title="📊 분석이 완료되었습니다!",
                body=f"'{keyword}' 분석 보고서가 준비되었습니다.",
                data={
                    'type': 'analysis_complete',
                    'report_id': report_id,
                    'keyword': keyword,
                    'user_nickname': user_nickname
                },
                sound="default",
                priority="high",
                badge=1
            )
            
            # Send the message
            try:
                response = self.client.publish(message)
                logger.info(f"푸시 알림 전송 성공: {user_nickname} - {keyword}")
                return True
            except PushServerError as e:
                logger.error(f"Push server error: {e}")
                return False
            except (DeviceNotRegisteredError, PushTicketError) as e:
                logger.error(f"Push notification error: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return False
    
    async def send_schedule_notification(
        self,
        push_token: str,
        user_nickname: str,
        keyword: str,
        schedule_id: int
    ) -> bool:
        """스케줄 분석 완료 알림 전송"""
        if not push_token:
            return False
            
        try:
            if not PushClient.is_exponent_push_token(push_token):
                logger.error(f"Invalid push token: {push_token}")
                return False
            
            message = PushMessage(
                to=push_token,
                title="🔔 예약 분석이 완료되었습니다!",
                body=f"'{keyword}' 예약 분석 보고서가 준비되었습니다.",
                data={
                    'type': 'schedule_complete',
                    'schedule_id': schedule_id,
                    'keyword': keyword,
                    'user_nickname': user_nickname
                },
                sound="default",
                priority="high",
                badge=1
            )
            
            try:
                response = self.client.publish(message)
                logger.info(f"스케줄 푸시 알림 전송 성공: {user_nickname} - {keyword}")
                return True
            except Exception as e:
                logger.error(f"Failed to send schedule notification: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error in schedule notification: {e}")
            return False

# 전역 푸시 알림 서비스 인스턴스
push_notification_service = PushNotificationService()