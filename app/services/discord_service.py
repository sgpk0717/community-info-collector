"""
Discord 서버 메시지 수집 서비스
웹훅을 통한 메시지 수집 및 공개 서버 정보 크롤링
"""
from typing import List, Dict, Optional
from app.schemas.schemas import PostBase
import logging
import httpx
import asyncio
from datetime import datetime
import json
from app.core.config import settings

logger = logging.getLogger(__name__)

class DiscordService:
    def __init__(self):
        self.base_url = "https://discord.com"
        self.api_base = "https://discord.com/api/v10"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        # Discord 봇 토큰 (옵션)
        self.bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', None)
        if self.bot_token:
            self.headers['Authorization'] = f'Bot {self.bot_token}'
    
    async def search_posts(self, query: str, limit: int = 25) -> List[PostBase]:
        """
        Discord 공개 정보 검색
        Note: Discord는 대부분 비공개이므로 제한적인 정보만 수집 가능
        """
        posts = []
        
        try:
            # 1. 공개 서버 목록에서 검색
            public_servers = await self._search_public_servers(query)
            
            # 2. Discord 상태 페이지에서 정보 수집
            status_info = await self._get_discord_status()
            if status_info:
                posts.append(status_info)
            
            # 3. 웹훅으로 받은 메시지가 있다면 검색
            webhook_messages = await self._search_webhook_messages(query)
            posts.extend(webhook_messages)
            
            logger.info(f"Retrieved {len(posts)} items from Discord for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching Discord: {e}")
        
        return posts[:limit]
    
    async def _search_public_servers(self, query: str) -> List[PostBase]:
        """공개 서버 디렉토리 검색 (Discord.me, Disboard 등)"""
        posts = []
        
        try:
            # Disboard (Discord 서버 목록 사이트) 검색
            async with httpx.AsyncClient() as client:
                search_url = f"https://disboard.org/servers/search/{query}"
                response = await client.get(search_url, headers=self.headers)
                
                if response.status_code == 200:
                    # 간단한 파싱 (실제로는 BeautifulSoup 사용 권장)
                    content = response.text
                    if query.lower() in content.lower():
                        post = PostBase(
                            source="discord/disboard",
                            post_id=None,
                            author="Discord Server Directory",
                            title=f"Discord servers related to: {query}",
                            content=f"Found Discord servers matching '{query}' on Disboard. Visit {search_url} for more details.",
                            url=search_url
                        )
                        posts.append(post)
                        
        except Exception as e:
            logger.error(f"Error searching public servers: {e}")
        
        return posts
    
    async def _get_discord_status(self) -> Optional[PostBase]:
        """Discord 상태 정보 가져오기"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://discordstatus.com/api/v2/summary.json")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    status = data.get('status', {})
                    incidents = data.get('incidents', [])
                    
                    content = f"Discord Status: {status.get('description', 'Unknown')}\n"
                    content += f"Last Updated: {data.get('page', {}).get('updated_at', 'Unknown')}\n\n"
                    
                    if incidents:
                        content += "Recent Incidents:\n"
                        for incident in incidents[:3]:
                            content += f"- {incident.get('name', 'Unknown incident')}\n"
                    
                    return PostBase(
                        source="discord/status",
                        post_id=None,
                        author="Discord Status",
                        title="Discord Service Status",
                        content=content,
                        url="https://discordstatus.com"
                    )
                    
        except Exception as e:
            logger.error(f"Error getting Discord status: {e}")
        
        return None
    
    async def _search_webhook_messages(self, query: str) -> List[PostBase]:
        """웹훅으로 수집된 메시지 검색 (데이터베이스에 저장된 경우)"""
        posts = []
        
        # 실제 구현에서는 데이터베이스에서 웹훅 메시지를 검색
        # 여기서는 예시로 빈 리스트 반환
        
        return posts
    
    async def setup_webhook_listener(self, webhook_url: str) -> Dict:
        """Discord 웹훅 설정 (메시지 수신용)"""
        try:
            # 웹훅 정보 확인
            async with httpx.AsyncClient() as client:
                response = await client.get(webhook_url)
                
                if response.status_code == 200:
                    webhook_info = response.json()
                    return {
                        'id': webhook_info.get('id'),
                        'name': webhook_info.get('name'),
                        'channel_id': webhook_info.get('channel_id'),
                        'guild_id': webhook_info.get('guild_id'),
                        'status': 'active'
                    }
                    
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def send_to_webhook(self, webhook_url: str, message: str, embed: Optional[Dict] = None) -> bool:
        """Discord 웹훅으로 메시지 전송"""
        try:
            payload = {
                'content': message,
                'username': 'Community Collector Bot'
            }
            
            if embed:
                payload['embeds'] = [embed]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Error sending to webhook: {e}")
            return False
    
    async def get_guild_info(self, guild_id: str) -> Optional[Dict]:
        """Discord 서버(길드) 정보 가져오기 (봇 토큰 필요)"""
        if not self.bot_token:
            logger.warning("Discord bot token not configured")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/guilds/{guild_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error getting guild info: {e}")
        
        return None
    
    async def search_messages_in_channel(self, channel_id: str, query: str) -> List[Dict]:
        """특정 채널에서 메시지 검색 (봇 토큰 필요)"""
        if not self.bot_token:
            return []
        
        messages = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/channels/{channel_id}/messages",
                    headers=self.headers,
                    params={'limit': 100}
                )
                
                if response.status_code == 200:
                    all_messages = response.json()
                    
                    # 쿼리와 일치하는 메시지 필터링
                    for msg in all_messages:
                        if query.lower() in msg.get('content', '').lower():
                            messages.append({
                                'id': msg.get('id'),
                                'content': msg.get('content'),
                                'author': msg.get('author', {}).get('username', 'Unknown'),
                                'timestamp': msg.get('timestamp'),
                                'channel_id': channel_id
                            })
                            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
        
        return messages
    
    def create_embed(self, title: str, description: str, fields: List[Dict], 
                    color: int = 0x7289DA) -> Dict:
        """Discord embed 메시지 생성"""
        embed = {
            'title': title,
            'description': description,
            'color': color,
            'fields': fields,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Community Collector'
            }
        }
        
        return embed