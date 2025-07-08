"""
Hacker News 크롤링 서비스
개발자 커뮤니티의 최신 트렌드와 토론 수집
"""
from typing import List, Dict, Optional
from app.schemas.schemas import PostBase
import logging
import httpx
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class HackerNewsService:
    def __init__(self):
        self.base_url = "https://news.ycombinator.com"
        self.api_base = "https://hacker-news.firebaseio.com/v0"
        self.algolia_api = "https://hn.algolia.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def search_posts(self, query: str, limit: int = 25) -> List[PostBase]:
        """
        Hacker News에서 게시물 검색
        Algolia Search API 사용 (공식 검색 API)
        """
        posts = []
        
        try:
            # Algolia API로 검색
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.algolia_api}/search",
                    params={
                        'query': query,
                        'tags': 'story',  # story, comment, poll 중 선택
                        'hitsPerPage': limit
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get('hits', [])
                    
                    for hit in hits:
                        post = self._parse_algolia_hit(hit)
                        if post:
                            posts.append(post)
            
            logger.info(f"Retrieved {len(posts)} posts from Hacker News for query: {query}")
            
        except Exception as e:
            logger.error(f"Error searching Hacker News: {e}")
        
        return posts
    
    def _parse_algolia_hit(self, hit: Dict) -> Optional[PostBase]:
        """Algolia 검색 결과 파싱"""
        try:
            # 콘텐츠 구성
            content = ""
            
            # 본문이 있는 경우 (Ask HN, Tell HN 등)
            if hit.get('story_text'):
                content = hit['story_text']
            elif hit.get('comment_text'):
                content = hit['comment_text']
            else:
                content = hit.get('title', '')
            
            # 메타데이터 추가
            metadata = f"\n\n---\n"
            metadata += f"👍 Points: {hit.get('points', 0)} | "
            metadata += f"💬 Comments: {hit.get('num_comments', 0)} | "
            
            # 시간 정보
            created_at = hit.get('created_at')
            if created_at:
                metadata += f"📅 Posted: {created_at}"
            
            # URL 처리
            story_url = hit.get('url')  # 외부 링크
            hn_url = f"{self.base_url}/item?id={hit.get('objectID', '')}"  # HN 토론 링크
            
            content += metadata
            
            return PostBase(
                source="hackernews",
                post_id=hit.get('objectID'),
                author=hit.get('author', 'Unknown'),
                title=hit.get('title'),
                content=content,
                url=story_url or hn_url  # 외부 링크가 있으면 우선, 없으면 HN 링크
            )
            
        except Exception as e:
            logger.error(f"Error parsing Algolia hit: {e}")
            return None
    
    async def get_top_stories(self, story_type: str = "top", limit: int = 30) -> List[PostBase]:
        """
        인기 스토리 가져오기
        story_type: top, new, best, ask, show, job
        """
        posts = []
        
        try:
            async with httpx.AsyncClient() as client:
                # 스토리 ID 목록 가져오기
                response = await client.get(f"{self.api_base}/{story_type}stories.json")
                
                if response.status_code == 200:
                    story_ids = response.json()[:limit]
                    
                    # 각 스토리 상세 정보 가져오기 (병렬 처리)
                    tasks = []
                    for story_id in story_ids:
                        task = self._get_story_details(client, story_id)
                        tasks.append(task)
                    
                    stories = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for story in stories:
                        if isinstance(story, PostBase):
                            posts.append(story)
            
        except Exception as e:
            logger.error(f"Error getting top stories: {e}")
        
        return posts
    
    async def _get_story_details(self, client: httpx.AsyncClient, story_id: int) -> Optional[PostBase]:
        """개별 스토리 상세 정보 가져오기"""
        try:
            response = await client.get(f"{self.api_base}/item/{story_id}.json")
            
            if response.status_code == 200:
                item = response.json()
                
                if not item or item.get('deleted') or item.get('dead'):
                    return None
                
                # 콘텐츠 구성
                content = item.get('text', '') or item.get('title', '')
                
                # 메타데이터
                metadata = f"\n\n---\n"
                metadata += f"👍 Score: {item.get('score', 0)} | "
                metadata += f"💬 Comments: {len(item.get('kids', []))} | "
                metadata += f"📅 Posted: {datetime.fromtimestamp(item.get('time', 0)).strftime('%Y-%m-%d %H:%M')}"
                
                content += metadata
                
                return PostBase(
                    source="hackernews",
                    post_id=str(story_id),
                    author=item.get('by', 'Unknown'),
                    title=item.get('title'),
                    content=content,
                    url=item.get('url') or f"{self.base_url}/item?id={story_id}"
                )
                
        except Exception as e:
            logger.error(f"Error getting story details: {e}")
            return None
    
    async def get_user_submissions(self, username: str, limit: int = 20) -> List[PostBase]:
        """특정 사용자의 제출물 가져오기"""
        posts = []
        
        try:
            async with httpx.AsyncClient() as client:
                # 사용자 정보 가져오기
                response = await client.get(f"{self.api_base}/user/{username}.json")
                
                if response.status_code == 200:
                    user_data = response.json()
                    submitted_ids = user_data.get('submitted', [])[:limit]
                    
                    # 각 제출물 정보 가져오기
                    tasks = []
                    for item_id in submitted_ids:
                        task = self._get_story_details(client, item_id)
                        tasks.append(task)
                    
                    items = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for item in items:
                        if isinstance(item, PostBase):
                            posts.append(item)
                            
        except Exception as e:
            logger.error(f"Error getting user submissions: {e}")
        
        return posts
    
    async def get_comments_for_story(self, story_id: int, max_depth: int = 2) -> List[Dict]:
        """스토리의 댓글 가져오기"""
        comments = []
        
        try:
            async with httpx.AsyncClient() as client:
                # 스토리 정보 가져오기
                response = await client.get(f"{self.api_base}/item/{story_id}.json")
                
                if response.status_code == 200:
                    story = response.json()
                    kid_ids = story.get('kids', [])
                    
                    # 댓글 가져오기 (재귀적으로)
                    for kid_id in kid_ids[:10]:  # 상위 10개 댓글만
                        comment = await self._get_comment_tree(client, kid_id, max_depth)
                        if comment:
                            comments.append(comment)
                            
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
        
        return comments
    
    async def _get_comment_tree(self, client: httpx.AsyncClient, comment_id: int, 
                               max_depth: int, current_depth: int = 0) -> Optional[Dict]:
        """댓글 트리 구조로 가져오기"""
        if current_depth >= max_depth:
            return None
        
        try:
            response = await client.get(f"{self.api_base}/item/{comment_id}.json")
            
            if response.status_code == 200:
                comment = response.json()
                
                if not comment or comment.get('deleted') or comment.get('dead'):
                    return None
                
                comment_data = {
                    'id': comment_id,
                    'author': comment.get('by', 'Unknown'),
                    'text': comment.get('text', ''),
                    'time': datetime.fromtimestamp(comment.get('time', 0)).isoformat(),
                    'replies': []
                }
                
                # 대댓글 가져오기
                kid_ids = comment.get('kids', [])
                for kid_id in kid_ids[:3]:  # 대댓글은 3개까지만
                    reply = await self._get_comment_tree(
                        client, kid_id, max_depth, current_depth + 1
                    )
                    if reply:
                        comment_data['replies'].append(reply)
                
                return comment_data
                
        except Exception as e:
            logger.error(f"Error getting comment tree: {e}")
            return None
    
    async def monitor_keywords(self, keywords: List[str], callback) -> None:
        """키워드 모니터링 (실시간 알림)"""
        logger.info(f"Starting HN monitoring for keywords: {keywords}")
        
        last_seen_ids = set()
        
        while True:
            try:
                # 새 스토리 확인
                new_stories = await self.get_top_stories("new", limit=30)
                
                for story in new_stories:
                    if story.post_id not in last_seen_ids:
                        last_seen_ids.add(story.post_id)
                        
                        # 키워드 매칭
                        content_lower = (story.title or '').lower() + ' ' + story.content.lower()
                        
                        for keyword in keywords:
                            if keyword.lower() in content_lower:
                                await callback(story, keyword)
                                break
                
                # 메모리 관리 (최근 1000개만 유지)
                if len(last_seen_ids) > 1000:
                    last_seen_ids = set(list(last_seen_ids)[-1000:])
                
                # 5분마다 체크
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in keyword monitoring: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기