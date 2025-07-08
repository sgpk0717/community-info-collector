import praw
from typing import List, Dict, Optional
from app.core.config import settings
from app.schemas.schemas import PostBase
import logging
import asyncio
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class RedditService:
    def __init__(self):
        self.reddit = None
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT,
                    timeout=30
                )
                # 연결 테스트
                self.reddit.user.me()
                logger.info("Reddit client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Reddit client: {e}")
    
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
            # Reddit 검색 실행
            submissions = list(self.reddit.subreddit("all").search(
                query, 
                sort=sort, 
                time_filter="week",  # 최근 일주일
                limit=min(limit, 100)
            ))
            
            for submission in submissions:
                # 댓글 수와 점수 정보 추가
                post = PostBase(
                    source="reddit",
                    post_id=submission.id,
                    author=str(submission.author) if submission.author else "[deleted]",
                    title=submission.title,
                    content=self._get_post_content(submission),
                    url=f"https://reddit.com{submission.permalink}"
                )
                posts.append(post)
                
            logger.info(f"Retrieved {len(posts)} posts from Reddit for query: {query}")
            
        except praw.exceptions.APIException as e:
            logger.error(f"Reddit API error: {e}")
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
        
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
                    url=f"https://reddit.com{submission.permalink}"
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