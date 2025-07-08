import tweepy
from typing import List, Dict, Optional
from app.core.config import settings
from app.schemas.schemas import PostBase
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.client = None
        self.api = None  # v1.1 API용
        
        if settings.TWITTER_BEARER_TOKEN:
            try:
                # v2 API 클라이언트
                self.client = tweepy.Client(
                    bearer_token=settings.TWITTER_BEARER_TOKEN,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter v2 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter v2 client: {e}")
        
        # v1.1 API도 초기화 (더 많은 기능 사용 가능)
        if all([settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET,
                settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET]):
            try:
                auth = tweepy.OAuthHandler(settings.TWITTER_API_KEY, settings.TWITTER_API_SECRET)
                auth.set_access_token(settings.TWITTER_ACCESS_TOKEN, settings.TWITTER_ACCESS_TOKEN_SECRET)
                self.api = tweepy.API(auth, wait_on_rate_limit=True)
                logger.info("Twitter v1.1 API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twitter v1.1 API: {e}")
    
    async def search_posts(self, query: str, limit: int = 25, result_type: str = "mixed") -> List[PostBase]:
        """
        Twitter에서 트윗 검색
        
        Args:
            query: 검색 쿼리
            limit: 가져올 트윗 수 (최대 100)
            result_type: mixed(기본), recent(최신), popular(인기)
        """
        if not self.client:
            logger.warning("Twitter client not initialized")
            return []
        
        posts = []
        try:
            # 비동기 실행을 위한 executor 사용
            loop = asyncio.get_event_loop()
            
            # 고급 검색 쿼리 옵션 추가
            search_query = f"{query} -is:retweet lang:en OR lang:ko"
            
            tweets = await loop.run_in_executor(
                None,
                lambda: self.client.search_recent_tweets(
                    query=search_query,
                    max_results=min(limit, 100),
                    tweet_fields=['created_at', 'author_id', 'public_metrics', 'referenced_tweets', 'lang'],
                    user_fields=['username', 'name', 'verified'],
                    expansions=['author_id']
                )
            )
            
            if tweets.data:
                # 사용자 정보 매핑
                users = {user.id: user for user in (tweets.includes.get('users', []) or [])}
                
                for tweet in tweets.data:
                    user = users.get(tweet.author_id, None)
                    username = user.username if user else tweet.author_id
                    
                    # 메트릭 정보 추출
                    metrics = tweet.public_metrics or {}
                    
                    content = self._format_tweet_content(tweet, metrics)
                    
                    post = PostBase(
                        source="twitter",
                        post_id=str(tweet.id),
                        author=f"@{username}" if user else str(tweet.author_id),
                        title=None,  # Twitter는 제목이 없음
                        content=content,
                        url=f"https://twitter.com/{username}/status/{tweet.id}" if user else f"https://twitter.com/i/web/status/{tweet.id}"
                    )
                    posts.append(post)
                
                logger.info(f"Retrieved {len(posts)} tweets for query: {query}")
                
        except tweepy.TooManyRequests:
            logger.error("Twitter API rate limit exceeded")
        except tweepy.Unauthorized:
            logger.error("Twitter API unauthorized - check your credentials")
        except Exception as e:
            logger.error(f"Error searching Twitter: {e}")
        
        return posts
    
    async def get_trending_topics(self, location_id: int = 1) -> List[Dict]:
        """
        트렌딩 토픽 가져오기
        
        Args:
            location_id: 위치 ID (1=전세계, 23424977=미국, 23424868=한국)
        """
        if not self.api:  # v1.1 API 필요
            logger.warning("Twitter v1.1 API not initialized")
            return []
        
        trends = []
        try:
            loop = asyncio.get_event_loop()
            trending = await loop.run_in_executor(
                None,
                self.api.get_place_trends,
                location_id
            )
            
            if trending:
                for trend in trending[0]['trends'][:10]:  # 상위 10개만
                    trends.append({
                        'name': trend['name'],
                        'url': trend['url'],
                        'tweet_volume': trend.get('tweet_volume', 0)
                    })
                    
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
        
        return trends
    
    async def search_user_tweets(self, username: str, limit: int = 10) -> List[PostBase]:
        """특정 사용자의 최근 트윗 가져오기"""
        if not self.client:
            return []
        
        posts = []
        try:
            loop = asyncio.get_event_loop()
            
            # 사용자 ID 가져오기
            user = await loop.run_in_executor(
                None,
                lambda: self.client.get_user(username=username)
            )
            
            if user.data:
                user_id = user.data.id
                
                # 사용자의 트윗 가져오기
                tweets = await loop.run_in_executor(
                    None,
                    lambda: self.client.get_users_tweets(
                        id=user_id,
                        max_results=min(limit, 100),
                        tweet_fields=['created_at', 'public_metrics']
                    )
                )
                
                if tweets.data:
                    for tweet in tweets.data:
                        metrics = tweet.public_metrics or {}
                        content = self._format_tweet_content(tweet, metrics)
                        
                        post = PostBase(
                            source=f"twitter/@{username}",
                            post_id=str(tweet.id),
                            author=f"@{username}",
                            title=None,
                            content=content,
                            url=f"https://twitter.com/{username}/status/{tweet.id}"
                        )
                        posts.append(post)
                        
        except Exception as e:
            logger.error(f"Error getting user tweets: {e}")
        
        return posts
    
    def _format_tweet_content(self, tweet, metrics: dict) -> str:
        """트윗 내용 포맷팅"""
        content_parts = [tweet.text]
        
        # 메트릭 정보 추가
        meta = "\n\n---\n"
        meta += f"❤️ Likes: {metrics.get('like_count', 0)} | "
        meta += f"🔁 Retweets: {metrics.get('retweet_count', 0)} | "
        meta += f"💬 Replies: {metrics.get('reply_count', 0)} | "
        meta += f"📊 Impressions: {metrics.get('impression_count', 'N/A')}"
        
        if hasattr(tweet, 'created_at') and tweet.created_at:
            meta += f"\n📅 Posted: {tweet.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        content_parts.append(meta)
        
        return "\n".join(content_parts)