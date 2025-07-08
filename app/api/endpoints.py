from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.db.base import get_db
from app.schemas.schemas import SearchRequest, SearchResponse, PostResponse, ReportResponse
from app.models.models import SearchQuery, CollectedPost, Report
from app.services.reddit_service import RedditService
from app.services.twitter_service import TwitterService
from app.services.threads_service import ThreadsService
from app.services.llm_service import LLMService
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 인스턴스 생성
reddit_service = RedditService()
twitter_service = TwitterService()
threads_service = ThreadsService()
llm_service = LLMService()

@router.post("/search", response_model=SearchResponse)
async def search_and_analyze(
    request: SearchRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    여러 커뮤니티에서 정보를 검색하고 분석합니다.
    
    - **query**: 검색할 키워드
    - **sources**: 검색할 플랫폼 목록 (reddit, twitter, threads)
    """
    # 검색 쿼리 저장
    query = SearchQuery(query_text=request.query)
    db.add(query)
    db.commit()
    db.refresh(query)
    
    # 병렬로 각 플랫폼에서 검색
    tasks = []
    if "reddit" in request.sources:
        tasks.append(reddit_service.search_posts(request.query))
    if "twitter" in request.sources:
        tasks.append(twitter_service.search_posts(request.query))
    if "threads" in request.sources:
        tasks.append(threads_service.search_posts(request.query))
    
    # 모든 검색 결과 수집
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    all_posts = []
    
    for result in all_results:
        if isinstance(result, Exception):
            logger.error(f"Search error: {result}")
        else:
            all_posts.extend(result)
    
    # 수집된 게시물 저장
    saved_posts = []
    for post_data in all_posts:
        try:
            post = CollectedPost(
                source=post_data.source,
                post_id=post_data.post_id,
                author=post_data.author,
                title=post_data.title,
                content=post_data.content,
                url=post_data.url,
                search_query_id=query.id
            )
            db.add(post)
            saved_posts.append(post_data)
        except Exception as e:
            logger.error(f"Error saving post: {e}")
    
    db.commit()
    
    # LLM으로 보고서 생성
    report_data = await llm_service.generate_report(request.query, saved_posts)
    
    report = Report(
        search_query_id=query.id,
        summary=report_data["summary"],
        full_report=report_data["full_report"]
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return SearchResponse(
        query_id=query.id,
        query_text=query.query_text,
        posts_collected=len(saved_posts),
        report=ReportResponse(
            id=report.id,
            search_query_id=report.search_query_id,
            summary=report.summary,
            full_report=report.full_report,
            created_at=report.created_at
        )
    )

@router.get("/search/{query_id}", response_model=SearchResponse)
async def get_search_details(query_id: int, db: Session = Depends(get_db)):
    """특정 검색의 상세 정보를 가져옵니다."""
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
    
    posts_count = db.query(CollectedPost).filter(CollectedPost.search_query_id == query_id).count()
    report = db.query(Report).filter(Report.search_query_id == query_id).first()
    
    return SearchResponse(
        query_id=query.id,
        query_text=query.query_text,
        posts_collected=posts_count,
        report=ReportResponse(
            id=report.id,
            search_query_id=report.search_query_id,
            summary=report.summary,
            full_report=report.full_report,
            created_at=report.created_at
        ) if report else None
    )

@router.get("/posts/{query_id}", response_model=List[PostResponse])
async def get_posts_by_query(
    query_id: int, 
    source: Optional[str] = Query(None, description="필터링할 소스 (reddit, twitter, threads)"),
    limit: int = Query(50, description="반환할 최대 게시물 수"),
    db: Session = Depends(get_db)
):
    """검색 쿼리의 수집된 게시물들을 가져옵니다."""
    query = db.query(CollectedPost).filter(CollectedPost.search_query_id == query_id)
    
    if source:
        query = query.filter(CollectedPost.source == source)
    
    posts = query.limit(limit).all()
    
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found for this query")
    
    return posts

@router.get("/report/{query_id}", response_model=ReportResponse)
async def get_report_by_query(query_id: int, db: Session = Depends(get_db)):
    """검색 쿼리의 분석 보고서를 가져옵니다."""
    report = db.query(Report).filter(Report.search_query_id == query_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="No report found for this query")
    return report

@router.get("/trending")
async def get_trending_topics():
    """각 플랫폼의 트렌딩 토픽을 가져옵니다."""
    trending = {}
    
    # Reddit 트렌딩
    try:
        trending["reddit"] = await reddit_service.get_trending_topics()
    except Exception as e:
        logger.error(f"Error getting Reddit trending: {e}")
        trending["reddit"] = []
    
    # Twitter 트렌딩
    try:
        trending["twitter"] = await twitter_service.get_trending_topics()
    except Exception as e:
        logger.error(f"Error getting Twitter trending: {e}")
        trending["twitter"] = []
    
    # Threads 트렌딩
    try:
        trending["threads"] = await threads_service.get_trending_topics()
    except Exception as e:
        logger.error(f"Error getting Threads trending: {e}")
        trending["threads"] = []
    
    return trending

@router.get("/search/history")
async def get_search_history(
    limit: int = Query(10, description="반환할 최대 검색 수"),
    db: Session = Depends(get_db)
):
    """최근 검색 이력을 가져옵니다."""
    queries = db.query(SearchQuery).order_by(SearchQuery.created_at.desc()).limit(limit).all()
    
    history = []
    for query in queries:
        posts_count = db.query(CollectedPost).filter(CollectedPost.search_query_id == query.id).count()
        has_report = db.query(Report).filter(Report.search_query_id == query.id).first() is not None
        
        history.append({
            "id": query.id,
            "query_text": query.query_text,
            "created_at": query.created_at,
            "posts_collected": posts_count,
            "has_report": has_report
        })
    
    return history

@router.delete("/search/{query_id}")
async def delete_search(query_id: int, db: Session = Depends(get_db)):
    """검색 쿼리와 관련된 모든 데이터를 삭제합니다."""
    query = db.query(SearchQuery).filter(SearchQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Search query not found")
    
    # 관련 데이터 삭제 (cascade 설정에 따라 자동 삭제될 수도 있음)
    db.query(CollectedPost).filter(CollectedPost.search_query_id == query_id).delete()
    db.query(Report).filter(Report.search_query_id == query_id).delete()
    db.delete(query)
    db.commit()
    
    return {"message": "Search query and related data deleted successfully"}

@router.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """시스템 통계를 가져옵니다."""
    total_searches = db.query(SearchQuery).count()
    total_posts = db.query(CollectedPost).count()
    total_reports = db.query(Report).count()
    
    # 소스별 게시물 수
    source_stats = {}
    for source in ["reddit", "twitter", "threads"]:
        count = db.query(CollectedPost).filter(CollectedPost.source == source).count()
        source_stats[source] = count
    
    return {
        "total_searches": total_searches,
        "total_posts": total_posts,
        "total_reports": total_reports,
        "posts_by_source": source_stats,
        "services_status": {
            "reddit": reddit_service.reddit is not None,
            "twitter": twitter_service.client is not None,
            "threads": True,  # 항상 가능 (웹 스크래핑)
            "llm": llm_service.openai_client is not None
        }
    }