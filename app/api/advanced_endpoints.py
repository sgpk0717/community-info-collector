"""
비정형 데이터 수집을 위한 고급 API 엔드포인트
헤드리스 브라우저와 고급 크롤링 기능 제공
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from app.schemas.schemas import SearchRequest, SearchResponse, PostResponse
from app.services.browser_service import BrowserService
from app.services.linkedin_service import LinkedInService
from app.services.discord_service import DiscordService
from app.services.hackernews_service import HackerNewsService
from app.services.llm_service import LLMService
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advanced", tags=["advanced"])

# 서비스 인스턴스
browser_service = BrowserService()
linkedin_service = LinkedInService()
discord_service = DiscordService()
hackernews_service = HackerNewsService()
llm_service = LLMService()

@router.post("/dynamic-search")
async def dynamic_content_search(
    url: str,
    selectors: Dict[str, str],
    scroll: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    동적 웹페이지에서 콘텐츠 추출
    JavaScript 렌더링이 필요한 사이트 크롤링
    
    - **url**: 크롤링할 URL
    - **selectors**: CSS 셀렉터 딕셔너리 {"title": "h1", "content": ".article-body"}
    - **scroll**: 무한 스크롤 페이지 여부
    """
    try:
        await browser_service.start()
        
        if scroll:
            # 무한 스크롤 처리
            items = await browser_service.handle_infinite_scroll(
                url, 
                selectors.get('item_selector', 'article'),
                max_items=50
            )
            return {"status": "success", "items": items, "count": len(items)}
        else:
            # 일반 동적 콘텐츠 추출
            data = await browser_service.extract_dynamic_content(url, selectors)
            return {"status": "success", "data": data}
            
    except Exception as e:
        logger.error(f"Dynamic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if background_tasks:
            background_tasks.add_task(browser_service.stop)

@router.post("/execute-script")
async def execute_javascript(
    url: str,
    script: str,
    wait_time: int = Query(2, description="페이지 로드 대기 시간(초)")
):
    """
    웹페이지에서 커스텀 JavaScript 실행
    
    - **url**: 대상 URL
    - **script**: 실행할 JavaScript 코드
    - **wait_time**: 페이지 로드 대기 시간
    """
    try:
        await browser_service.start()
        result = await browser_service.execute_custom_script(url, script)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Script execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await browser_service.stop()

@router.post("/linkedin-search")
async def search_linkedin(
    query: str,
    search_type: str = Query("posts", description="posts, jobs, profiles"),
    db: Session = Depends(get_db)
):
    """
    LinkedIn 데이터 수집
    
    - **query**: 검색 키워드
    - **search_type**: 검색 유형 (posts, jobs, profiles)
    """
    try:
        if search_type == "posts":
            posts = await linkedin_service.search_posts(query)
            
            # DB 저장
            search_query = SearchQuery(query_text=f"linkedin:{query}")
            db.add(search_query)
            db.commit()
            
            for post in posts:
                db_post = CollectedPost(
                    source=post.source,
                    post_id=post.post_id,
                    author=post.author,
                    title=post.title,
                    content=post.content,
                    url=post.url,
                    search_query_id=search_query.id
                )
                db.add(db_post)
            db.commit()
            
            return {"status": "success", "posts": posts, "count": len(posts)}
            
        elif search_type == "jobs":
            jobs = await linkedin_service.get_job_postings(query)
            return {"status": "success", "jobs": jobs, "count": len(jobs)}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid search type")
            
    except Exception as e:
        logger.error(f"LinkedIn search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discord-webhook")
async def setup_discord_webhook(webhook_url: str):
    """
    Discord 웹훅 설정
    
    - **webhook_url**: Discord 웹훅 URL
    """
    result = await discord_service.setup_webhook_listener(webhook_url)
    return result

@router.post("/discord-search")
async def search_discord(query: str, db: Session = Depends(get_db)):
    """
    Discord 공개 정보 검색
    """
    posts = await discord_service.search_posts(query)
    
    if posts:
        # DB 저장
        search_query = SearchQuery(query_text=f"discord:{query}")
        db.add(search_query)
        db.commit()
        
        for post in posts:
            db_post = CollectedPost(
                source=post.source,
                post_id=post.post_id,
                author=post.author,
                title=post.title,
                content=post.content,
                url=post.url,
                search_query_id=search_query.id
            )
            db.add(db_post)
        db.commit()
    
    return {"status": "success", "posts": posts, "count": len(posts)}

@router.get("/hackernews/top")
async def get_hn_top_stories(
    story_type: str = Query("top", description="top, new, best, ask, show, job"),
    limit: int = Query(30, description="스토리 개수")
):
    """
    Hacker News 인기 스토리
    """
    stories = await hackernews_service.get_top_stories(story_type, limit)
    return {"status": "success", "stories": stories, "count": len(stories)}

@router.post("/hackernews-search")
async def search_hackernews(query: str, limit: int = 25, db: Session = Depends(get_db)):
    """
    Hacker News 검색
    """
    posts = await hackernews_service.search_posts(query, limit)
    
    if posts:
        # DB 저장
        search_query = SearchQuery(query_text=f"hackernews:{query}")
        db.add(search_query)
        db.commit()
        
        for post in posts:
            db_post = CollectedPost(
                source=post.source,
                post_id=post.post_id,
                author=post.author,
                title=post.title,
                content=post.content,
                url=post.url,
                search_query_id=search_query.id
            )
            db.add(db_post)
        db.commit()
    
    return {"status": "success", "posts": posts, "count": len(posts)}

@router.get("/hackernews/comments/{story_id}")
async def get_hn_comments(story_id: int, max_depth: int = 2):
    """
    Hacker News 스토리의 댓글 가져오기
    """
    comments = await hackernews_service.get_comments_for_story(story_id, max_depth)
    return {"status": "success", "comments": comments, "count": len(comments)}

@router.post("/multi-source-crawl")
async def multi_source_crawl(
    query: str,
    sources: List[str] = Query(["hackernews", "linkedin", "discord"]),
    db: Session = Depends(get_db)
):
    """
    여러 소스에서 동시에 크롤링
    
    - **query**: 검색 키워드
    - **sources**: 크롤링할 소스 목록
    """
    all_posts = []
    tasks = []
    
    if "hackernews" in sources:
        tasks.append(hackernews_service.search_posts(query))
    if "linkedin" in sources:
        tasks.append(linkedin_service.search_posts(query))
    if "discord" in sources:
        tasks.append(discord_service.search_posts(query))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if not isinstance(result, Exception):
            all_posts.extend(result)
    
    # DB 저장
    if all_posts:
        search_query = SearchQuery(query_text=f"multi:{query}")
        db.add(search_query)
        db.commit()
        
        for post in all_posts:
            try:
                db_post = CollectedPost(
                    source=post.source,
                    post_id=post.post_id,
                    author=post.author,
                    title=post.title,
                    content=post.content,
                    url=post.url,
                    search_query_id=search_query.id
                )
                db.add(db_post)
            except Exception as e:
                logger.error(f"Error saving post: {e}")
        
        db.commit()
        
        # LLM 분석
        report_data = await llm_service.generate_report(query, all_posts)
        
        report = Report(
            search_query_id=search_query.id,
            summary=report_data["summary"],
            full_report=report_data["full_report"]
        )
        db.add(report)
        db.commit()
        
        return {
            "status": "success",
            "query_id": search_query.id,
            "posts_collected": len(all_posts),
            "sources": sources,
            "report": {
                "summary": report.summary,
                "full_report": report.full_report
            }
        }
    
    return {"status": "success", "posts_collected": 0}

@router.post("/cloudflare-bypass")
async def bypass_cloudflare_protection(url: str):
    """
    Cloudflare 보호 우회
    
    - **url**: Cloudflare로 보호된 URL
    """
    try:
        await browser_service.start()
        content = await browser_service.bypass_cloudflare(url)
        
        if content:
            return {
                "status": "success",
                "content_length": len(content),
                "preview": content[:500] + "..." if len(content) > 500 else content
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to bypass Cloudflare")
            
    except Exception as e:
        logger.error(f"Cloudflare bypass error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await browser_service.stop()

@router.get("/service-status")
async def get_advanced_service_status():
    """
    고급 크롤링 서비스 상태 확인
    """
    return {
        "browser_service": "ready",
        "linkedin": "ready",
        "discord": {
            "status": "ready",
            "bot_configured": discord_service.bot_token is not None
        },
        "hackernews": "ready",
        "features": {
            "dynamic_content": True,
            "javascript_execution": True,
            "infinite_scroll": True,
            "cloudflare_bypass": True,
            "webhook_support": True
        }
    }