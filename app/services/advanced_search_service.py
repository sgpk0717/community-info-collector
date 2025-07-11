#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 검색 서비스 - weighted_search.py 기반
"""
import json
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI
from app.core.config import settings
from app.services.reddit_service import RedditService
from app.schemas.schemas import PostBase
import time
import httpx

logger = logging.getLogger(__name__)

class AdvancedSearchService:
    def __init__(self):
        self.reddit_service = RedditService()
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            # SSL 검증을 비활성화한 HTTP 클라이언트 생성
            http_client = httpx.Client(verify=False)
            self.openai_client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                http_client=http_client
            )
    
    async def expand_keywords_with_gpt4(self, user_input: str) -> List[Dict]:
        """GPT-4를 사용하여 키워드를 확장하고 영어로 변환"""
        if not self.openai_client:
            logger.warning("OpenAI client not initialized, using fallback")
            return [{"rank": 1, "query": self.translate_to_english_keywords(user_input), "posts_to_collect": 10, "reason": "기본 번역"}]
        
        try:
            prompt = f"""
사용자가 입력한 키워드: "{user_input}"

이 키워드를 기반으로 Reddit에서 최신 정보와 찌라시, 루머, 뉴스를 잘 찾을 수 있도록 6개의 영어 검색 키워드를 만들어주세요.

요구사항:
1. 첫 번째 키워드는 원래 키워드의 직접 번역
2. 나머지 5개는 관련된 최신 정보, 뉴스, 루머, 분석을 잘 찾을 수 있는 키워드
3. 각 키워드는 Reddit 검색에 적합하도록 2-4개 단어로 구성
4. 투자, 주식, 기업 관련이면 earnings, forecast, analysis, news, rumor 등 포함
5. 인물 관련이면 controversy, scandal, latest, update 등 포함

JSON 형식으로 응답:
{{
    "keywords": [
        {{"keyword": "키워드1", "reason": "선택 이유"}},
        {{"keyword": "키워드2", "reason": "선택 이유"}},
        {{"keyword": "키워드3", "reason": "선택 이유"}},
        {{"keyword": "키워드4", "reason": "선택 이유"}},
        {{"keyword": "키워드5", "reason": "선택 이유"}},
        {{"keyword": "키워드6", "reason": "선택 이유"}}
    ]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            # JSON 응답 파싱
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"GPT-4 generated expanded keywords for '{user_input}'")
            
            expanded_keywords = []
            for i, item in enumerate(result["keywords"], 1):
                expanded_keywords.append({
                    "rank": i,
                    "query": item["keyword"],
                    "posts_to_collect": 10,
                    "reason": item["reason"]
                })
            
            return expanded_keywords
            
        except Exception as e:
            logger.error(f"GPT-4 keyword expansion failed: {e}")
            # 실패 시 기본 변환 로직 사용
            return [{"rank": 1, "query": self.translate_to_english_keywords(user_input), "posts_to_collect": 10, "reason": "기본 번역"}]
    
    def translate_to_english_keywords(self, korean_input: str) -> str:
        """한국어 키워드를 영어로 변환"""
        keyword_mapping = {
            "테슬라": "Tesla",
            "애플": "Apple",
            "주가": "stock price",
            "전망": "outlook forecast",
            "삼성": "Samsung",
            "네이버": "Naver",
            "카카오": "Kakao",
            "LG": "LG",
            "현대": "Hyundai",
            "기아": "Kia",
            "SK": "SK",
            "분석": "analysis",
            "투자": "investment",
            "수익": "profit earnings",
            "실적": "performance earnings",
            "매출": "revenue sales",
            "배당": "dividend",
            "상승": "rise increase",
            "하락": "fall decrease",
            "예측": "prediction forecast",
            "뉴스": "news",
            "발표": "announcement",
            "실적": "earnings results"
        }
        
        english_keywords = []
        for word in korean_input.split():
            if word in keyword_mapping:
                english_keywords.append(keyword_mapping[word])
            else:
                english_keywords.append(word)
        
        return " ".join(english_keywords)
    
    async def weighted_search(self, user_input: str, session_id: str = None) -> Dict:
        """가중치 기반 검색 - 중요도 순위별 게시물 수집"""
        if not self.reddit_service.reddit:
            logger.error("Reddit service not initialized")
            return {"posts": []}
        
        # GPT-4를 사용하여 키워드 확장
        logger.info(f"Expanding keywords for: {user_input}")
        search_keywords = await self.expand_keywords_with_gpt4(user_input)
        
        logger.info(f"Generated {len(search_keywords)} search keywords")
        
        all_posts_by_keyword = {}
        all_posts_combined = []
        seen_ids = set()
        
        for keyword_info in search_keywords:
            query = keyword_info['query']
            target_count = keyword_info['posts_to_collect']
            keyword_posts = []
            
            logger.info(f"Searching for '{query}' (target: {target_count})")
            
            # 다양한 정렬 방식으로 검색하여 목표 개수 달성
            for sort_method in ['hot', 'relevance', 'top']:
                if len(keyword_posts) >= target_count:
                    break
                    
                try:
                    # 기존 Reddit 서비스의 search_posts 사용
                    posts = self.reddit_service.search_posts(query, limit=20, sort=sort_method)
                    
                    for post in posts:
                        if len(keyword_posts) >= target_count:
                            break
                            
                        if post.post_id not in seen_ids:
                            seen_ids.add(post.post_id)
                            
                            try:
                                submission = self.reddit_service.reddit.submission(id=post.post_id)
                                
                                # 점수 20 이상인 게시물만
                                if submission.score >= 20:
                                    # 댓글 수집 (상위 5개)
                                    submission.comments.replace_more(limit=0)
                                    top_comments = []
                                    
                                    comment_count = 0
                                    for comment in sorted(submission.comments.list()[:20], 
                                                        key=lambda x: x.score if hasattr(x, 'score') else 0, 
                                                        reverse=True):
                                        if hasattr(comment, 'body') and comment_count < 5:
                                            top_comments.append({
                                                "author": str(comment.author) if comment.author else "[deleted]",
                                                "score": comment.score,
                                                "body": comment.body,
                                                "created_utc": comment.created_utc
                                            })
                                            comment_count += 1
                                    
                                    # PostBase 형식으로 변환 (메타데이터 포함)
                                    post_base = PostBase(
                                        source="reddit",
                                        post_id=submission.id,
                                        author=str(submission.author) if submission.author else "[deleted]",
                                        title=submission.title,
                                        content=self._format_post_content(submission, top_comments),
                                        url=f"https://reddit.com{submission.permalink}",
                                        # 메타데이터 추가
                                        score=submission.score,
                                        comments=submission.num_comments,
                                        created_utc=submission.created_utc,
                                        subreddit=submission.subreddit.display_name
                                    )
                                    
                                    keyword_posts.append(post_base)
                                    all_posts_combined.append(post_base)
                                    
                                    logger.debug(f"Added post: [{submission.score}] {submission.title[:50]}...")
                                    
                            except Exception as e:
                                logger.error(f"Error processing post {post.post_id}: {e}")
                                continue
                            
                except Exception as e:
                    logger.error(f"Error searching with query '{query}': {e}")
                
                # API 제한 방지
                await asyncio.sleep(0.5)
            
            # 키워드별 결과 저장
            all_posts_by_keyword[query] = {
                "rank": keyword_info['rank'],
                "reason": keyword_info['reason'],
                "target_count": target_count,
                "actual_count": len(keyword_posts),
                "posts": keyword_posts
            }
            
            logger.info(f"Collected {len(keyword_posts)} posts for '{query}'")
        
        logger.info(f"Total posts collected: {len(all_posts_combined)}")
        
        return {
            "topic": user_input,
            "total_posts": len(all_posts_combined),
            "posts": all_posts_combined,
            "keywords_used": search_keywords,
            "results_by_keyword": all_posts_by_keyword
        }
    
    def _format_post_content(self, submission, top_comments: List[Dict]) -> str:
        """게시물 내용 포맷팅"""
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
        
        # 상위 댓글 추가
        if top_comments:
            content_parts.append("\n\n🔥 Top Comments:")
            for i, comment in enumerate(top_comments[:3], 1):
                content_parts.append(f"{i}. [{comment['score']}] {comment['body'][:200]}...")
        
        return "\n".join(content_parts)