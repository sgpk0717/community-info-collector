import praw
from typing import List, Dict, Optional
from app.core.config import settings
from app.schemas.schemas import PostBase
import logging
import asyncio
from datetime import datetime
import time
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class RedditService:
    def __init__(self):
        self.reddit = None
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            try:
                # SSL 검증을 비활성화한 세션 생성
                session = requests.Session()
                session.verify = False
                
                # SSL 경고 비활성화
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                self.reddit = praw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT,
                    timeout=30,
                    requestor_kwargs={'session': session}
                )
                # 연결 테스트
                self.reddit.user.me()
                logger.info("✅ Reddit 클라이언트 초기화 성공")
            except Exception as e:
                logger.error(f"❌ Reddit 클라이언트 초기화 실패: {e}")
    
    def search_posts(self, query: str, limit: int = 25, sort: str = "relevance") -> List[PostBase]:
        """
        Reddit에서 게시물 검색
        
        Args:
            query: 검색 쿼리
            limit: 가져올 게시물 수 (최대 100)
            sort: 정렬 방식 (relevance, hot, top, new)
        """
        if not self.reddit:
            logger.warning("Reddit client not initialized")
            return []
        
        posts = []
        try:
            # 한글 검색어를 위한 키워드 매핑
            keyword_mapping = {
                "테슬라": ["Tesla", "TSLA"],
                "애플": ["Apple", "AAPL"],
                "삼성": ["Samsung"],
                "구글": ["Google", "GOOGL"],
                "아마존": ["Amazon", "AMZN"],
                "메타": ["Meta", "META", "Facebook"],
                "엔비디아": ["NVIDIA", "NVDA"],
                "뉴스": ["news", "update", "announcement"],
                "주식": ["stock", "shares", "investment"],
                "주가": ["stock price", "share price"],
                "전망": ["forecast", "prediction", "outlook"],
                "분석": ["analysis", "review"],
            }
            
            # 한글 키워드를 영어로 변환
            search_queries = []
            original_query = query
            
            # 키워드 매핑 적용
            for korean, english_list in keyword_mapping.items():
                if korean in query:
                    for eng in english_list:
                        modified_query = query.replace(korean, eng)
                        if modified_query not in search_queries:
                            search_queries.append(modified_query)
            
            # 원본 쿼리도 추가 (혹시 영어로 검색한 경우)
            if not search_queries or query == original_query:
                search_queries.append(query)
            
            logger.info(f"Original query: {original_query}")
            logger.info(f"Search queries: {search_queries}")
            
            # 각 검색어로 검색 실행
            all_submissions = []
            seen_ids = set()
            
            for search_query in search_queries[:3]:  # 최대 3개 쿼리만 실행
                try:
                    logger.debug(f"Searching Reddit with query: {search_query}")
                    submissions = list(self.reddit.subreddit("all").search(
                        search_query, 
                        sort=sort, 
                        time_filter="week",  # 최근 일주일
                        limit=min(limit, 100)
                    ))
                    
                    # 중복 제거
                    for sub in submissions:
                        if sub.id not in seen_ids:
                            all_submissions.append(sub)
                            seen_ids.add(sub.id)
                    
                    logger.debug(f"Found {len(submissions)} posts for query: {search_query}")
                except Exception as e:
                    logger.error(f"Error searching with query '{search_query}': {e}")
            
            # 결과가 없으면 더 넓은 범위로 재검색
            if not all_submissions and search_queries:
                logger.info("No results found, trying broader search...")
                # 첫 번째 영어 키워드로만 재검색
                first_english_word = None
                for word in search_queries[0].split():
                    if word.isascii() and len(word) > 2:
                        first_english_word = word
                        break
                
                if first_english_word:
                    logger.debug(f"Broader search with: {first_english_word}")
                    try:
                        submissions = list(self.reddit.subreddit("all").search(
                            first_english_word,
                            sort="hot",
                            time_filter="month",  # 더 넓은 시간 범위
                            limit=min(limit, 50)
                        ))
                        all_submissions.extend(submissions)
                    except Exception as e:
                        logger.error(f"Error in broader search: {e}")
            
            # 검색 결과를 PostBase 객체로 변환
            for submission in all_submissions[:limit]:
                # 댓글 수와 점수 정보 추가
                post = PostBase(
                    source="reddit",
                    post_id=submission.id,
                    author=str(submission.author) if submission.author else "[deleted]",
                    title=submission.title,
                    content=self._get_post_content(submission),
                    url=f"https://reddit.com{submission.permalink}",
                    # 메타데이터 추가
                    score=submission.score,
                    comments=submission.num_comments,
                    created_utc=submission.created_utc,
                    subreddit=submission.subreddit.display_name
                )
                posts.append(post)
                
            logger.info(f"📋 Reddit 검색 완료 | 키워드: '{original_query}' | 결과: {len(posts)}개")
            
        except praw.exceptions.APIException as e:
            logger.error(f"⚠️ Reddit API 오류: {e}")
        except Exception as e:
            logger.error(f"❌ Reddit 검색 오류: {e}")
        
        return posts
    
    def search_subreddit(self, subreddit_name: str, query: str, limit: int = 25) -> List[PostBase]:
        """특정 서브레딧에서 검색"""
        if not self.reddit:
            return []
        
        posts = []
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            submissions = list(subreddit.search(query, limit=limit))
            
            for submission in submissions:
                post = PostBase(
                    source=f"reddit/{subreddit_name}",
                    post_id=submission.id,
                    author=str(submission.author) if submission.author else "[deleted]",
                    title=submission.title,
                    content=self._get_post_content(submission),
                    url=f"https://reddit.com{submission.permalink}",
                    # 메타데이터 추가
                    score=submission.score,
                    comments=submission.num_comments,
                    created_utc=submission.created_utc,
                    subreddit=submission.subreddit.display_name
                )
                posts.append(post)
                
        except Exception as e:
            logger.error(f"Error searching subreddit {subreddit_name}: {e}")
        
        return posts
    
    def get_trending_topics(self, subreddits: List[str] = None) -> List[Dict]:
        """인기 토픽 가져오기"""
        if not self.reddit:
            return []
        
        if not subreddits:
            subreddits = ["technology", "programming", "machinelearning", "artificial"]
        
        trending = []
        try:
            for sub_name in subreddits:
                subreddit = self.reddit.subreddit(sub_name)
                hot_posts = list(subreddit.hot(limit=5))
                
                for post in hot_posts:
                    trending.append({
                        "subreddit": sub_name,
                        "title": post.title,
                        "score": post.score,
                        "comments": post.num_comments,
                        "url": f"https://reddit.com{post.permalink}"
                    })
                    
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
        
        return trending
    
    def _get_post_content(self, submission) -> str:
        """게시물 내용 추출 및 포맷팅"""
        content_parts = []
        
        # 본문
        if submission.selftext:
            content_parts.append(submission.selftext[:1000])
        
        # 메타데이터
        meta = f"\n\n---\n"
        meta += f"👍 Score: {submission.score} | "
        meta += f"💬 Comments: {submission.num_comments} | "
        meta += f"📅 Posted: {datetime.fromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M')}"
        
        content_parts.append(meta)
        
        return "\n".join(content_parts)
    
    async def collect_reddit_posts(self, query: str, limit: int = 25) -> List[PostBase]:
        """비동기 래퍼 메서드 - 스케줄러에서 사용"""
        # 동기 메서드를 비동기로 래핑
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search_posts, query, limit)