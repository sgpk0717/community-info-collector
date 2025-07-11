from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict
from app.schemas.schemas import SearchRequest, SearchResponse, PostResponse, ReportResponse
from app.services.reddit_service import RedditService
from app.services.twitter_service import TwitterService
from app.services.threads_service import ThreadsService
from app.services.llm_service import LLMService
from app.services.progress_service import progress_service
from app.services.supabase_reports_service import supabase_reports_service
from app.services.push_notification_service import push_notification_service
import asyncio
import logging
from datetime import datetime
import uuid

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
    background_tasks: BackgroundTasks
):
    """
    여러 커뮤니티에서 정보를 검색하고 분석합니다.
    
    - **query**: 검색할 키워드
    - **sources**: 검색할 플랫폼 목록 (reddit, twitter, threads)
    - **user_nickname**: 사용자 닉네임
    - **schedule_yn**: 스케줄링 여부 (Y/N)
    - **schedule_period**: 주기 (분 단위) - schedule_yn이 Y일 때 필수
    - **schedule_count**: 반복 횟수 - schedule_yn이 Y일 때 필수  
    - **schedule_start_time**: 시작 시간 - schedule_yn이 Y일 때 필수
    """
    # 세션 ID 사용 (클라이언트에서 전달하거나 새로 생성)
    session_id = request.session_id or str(uuid.uuid4())
    
    logger.info(f"=== Search API Called ===")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Request data: {request.dict()}")
    logger.info(f"Query: {request.query}")
    logger.info(f"Sources: {request.sources}")
    logger.info(f"User nickname: {request.user_nickname}")
    logger.info(f"Schedule YN: {request.schedule_yn}")
    
    # 진행 상태 초기화
    await progress_service.update_progress(
        session_id, 
        "initializing", 
        5, 
        "분석 준비 중...",
        "요청을 처리하고 검색을 시작합니다"
    )
    # 스케줄링 파라미터 검증
    if request.schedule_yn == "Y":
        if not all([request.schedule_period, request.schedule_count, request.schedule_start_time]):
            raise HTTPException(
                status_code=400,
                detail="스케줄링이 활성화된 경우 schedule_period, schedule_count, schedule_start_time이 필수입니다."
            )
        
        # 스케줄링 생성 로직
        from app.services.supabase_schedule_service import supabase_schedule_service
        
        # 사용자 닉네임으로 user_id 조회
        if request.user_nickname:
            from app.services.supabase_service import supabase_service
            user_result = await supabase_service.get_user_by_nickname(request.user_nickname)
            if user_result and user_result["success"]:
                user_data = user_result["data"]
                # 스케줄 생성
                schedule_data = {
                    "user_id": user_data.get("id"),
                    "keyword": request.query,
                    "interval_minutes": request.schedule_period,
                    "total_reports": request.schedule_count,
                    "report_length": request.length.value,
                    "next_run": request.schedule_start_time,
                    "sources": request.sources
                }
                schedule = await supabase_schedule_service.create_schedule(schedule_data)
                logger.info(f"스케줄 생성됨: {schedule.id}")
            else:
                raise HTTPException(
                    status_code=404,
                    detail="사용자를 찾을 수 없습니다."
                )
    
    # 기존 검색 로직은 그대로 유지
    # 검색 쿼리는 Supabase reports에 직접 저장되므로 별도 저장 불필요
    logger.info(f"Processing search query: {request.query}")
    query_id = str(uuid.uuid4())  # 임시 query ID 생성
    
    # 고급 가중치 검색 시스템 사용
    if "reddit" in request.sources:
        await progress_service.update_progress(
            session_id, 
            "keyword_expansion", 
            20, 
            "🤖 AI가 키워드를 확장하고 있습니다...",
            f"'{request.query}'를 분석하여 최적의 검색 키워드를 생성 중"
        )
        
        logger.info("Using advanced weighted search system for Reddit")
        try:
            # GPT-4로 키워드 확장
            from app.services.advanced_search_service import AdvancedSearchService
            advanced_search = AdvancedSearchService()
            
            await progress_service.update_progress(
                session_id, 
                "reddit_search", 
                40, 
                "🔍 Reddit에서 게시물을 수집하고 있습니다...",
                "가중치 기반 검색으로 고품질 게시물을 선별 중"
            )
            
            # 가중치 기반 검색 실행
            search_result = await advanced_search.weighted_search(request.query, session_id)
            all_posts = search_result.get('posts', [])
            
            logger.info(f"Advanced search completed. Total posts: {len(all_posts)}")
            
            await progress_service.update_progress(
                session_id, 
                "data_collection", 
                60, 
                f"📊 {len(all_posts)}개의 게시물을 수집했습니다",
                "댓글과 메타데이터를 포함한 상세 정보 수집 완료"
            )
            
        except Exception as e:
            logger.error(f"Advanced search failed, falling back to basic search: {e}")
            # 기본 검색으로 폴백
            all_posts = reddit_service.search_posts(request.query)
    else:
        # 기존 로직 유지 (Twitter, Threads)
        tasks = []
        logger.info(f"Starting search on platforms: {request.sources}")
        
        if "twitter" in request.sources:
            logger.info("Adding Twitter search task")
            tasks.append(asyncio.to_thread(twitter_service.search_posts, request.query))
        if "threads" in request.sources:
            logger.info("Adding Threads search task")
            tasks.append(asyncio.to_thread(threads_service.search_posts, request.query))
        
        logger.info(f"Total tasks to execute: {len(tasks)}")
        
        # 모든 검색 결과 수집
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        all_posts = []
        
        logger.info(f"Search results collected. Total results: {len(all_results)}")
        
        for i, result in enumerate(all_results):
            if isinstance(result, Exception):
                logger.error(f"Search error in task {i}: {result}")
                logger.error(f"Exception type: {type(result)}")
            else:
                logger.info(f"Task {i} returned {len(result)} posts")
                all_posts.extend(result)
    
    # 수집된 게시물 정리 (데이터베이스 저장 없이 메모리에만 유지)
    saved_posts = all_posts  # 모든 post_data를 그대로 사용
    logger.info(f"Collected {len(saved_posts)} posts")
    
    # 수집된 게시물이 없으면 에러 반환
    if not saved_posts:
        logger.warning(f"No posts collected for query: {request.query}")
        raise HTTPException(
            status_code=404,
            detail="검색 결과가 없습니다. 다른 키워드로 시도해주세요."
        )
    
    # 고급 검증된 분석 시스템 사용
    await progress_service.update_progress(
        session_id, 
        "analysis", 
        80, 
        "🧠 AI가 수집된 데이터를 분석하고 있습니다...",
        "GPT-4.1을 사용하여 검증된 분석 보고서 생성 중"
    )
    
    try:
        from app.services.verified_analysis_service import VerifiedAnalysisService
        verified_analysis = VerifiedAnalysisService()
        
        # 검증된 분석 보고서 생성
        report_data = await verified_analysis.generate_verified_report(
            request.query,
            saved_posts,
            report_length=request.length.value if request.length else "moderate",
            session_id=session_id
        )
        
        logger.info("Used verified analysis system")
        
    except Exception as e:
        logger.error(f"Verified analysis failed, using basic LLM: {e}")
        # 기본 LLM 서비스로 폴백
        report_data = await llm_service.generate_report(
            request.query, 
            saved_posts,
            report_length=request.length.value if request.length else "moderate"
        )
    
    # Report 객체 생성 (데이터베이스 저장 없이 임시 생성)
    report_id = str(uuid.uuid4())
    
    # LLM이 생성한 post_mappings 사용 (있으면)
    posts_metadata = report_data.get("post_mappings", [])
    
    # post_mappings가 없으면 기존 방식으로 메타데이터 수집
    if not posts_metadata:
        for post in saved_posts[:30]:  # 최대 30개 포스트의 메타데이터 저장
            if post.url:  # URL이 있는 포스트만
                metadata = {
                    "url": post.url,
                    "score": post.score,
                    "comments": post.comments,
                    "created_utc": post.created_utc,
                    "subreddit": post.subreddit,
                    "title": post.title[:100] if post.title else None
                }
                posts_metadata.append(metadata)
    
    # Supabase에 보고서 저장
    try:
        supabase_report_data = {
            "user_nickname": request.user_nickname,
            "query_text": request.query,
            "full_report": report_data["full_report"],
            "summary": report_data["summary"],
            "posts_collected": len(saved_posts),
            "report_length": request.length.value if request.length else "moderate",
            "session_id": session_id,
            "posts_metadata": posts_metadata  # 메타데이터 추가
        }
        
        save_result = await supabase_reports_service.save_report(supabase_report_data)
        if save_result["success"]:
            logger.info(f"Report saved to Supabase: {save_result['report_id']}")
            
            # 푸시 알림 전송 (비동기)
            if request.push_token:
                asyncio.create_task(
                    push_notification_service.send_analysis_complete_notification(
                        push_token=request.push_token,
                        user_nickname=request.user_nickname or "사용자",
                        keyword=request.query,
                        report_id=save_result['report_id']
                    )
                )
        else:
            logger.error(f"Failed to save report to Supabase: {save_result['error']}")
    except Exception as e:
        logger.error(f"Error saving report to Supabase: {e}")
    
    # 완료 상태 업데이트
    await progress_service.update_progress(
        session_id, 
        "completed", 
        100, 
        "✅ 분석이 완료되었습니다!",
        f"총 {len(saved_posts)}개 게시물 분석 완료"
    )
    
    response = SearchResponse(
        query_id=query_id,
        query_text=request.query,
        posts_collected=len(saved_posts),
        report=ReportResponse(
            id=report_id,
            search_query_id=query_id,
            summary=report_data["summary"],
            full_report=report_data["full_report"],
            created_at=datetime.utcnow()
        )
    )
    
    # 응답에 세션 ID 추가
    response.session_id = session_id
    
    return response

@router.get("/search/{query_id}", response_model=SearchResponse)
async def get_search_details(query_id: int):
    """특정 검색의 상세 정보를 가져옵니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

@router.get("/posts/{query_id}", response_model=List[PostResponse])
async def get_posts_by_query(
    query_id: int, 
    source: Optional[str] = Query(None, description="필터링할 소스 (reddit, twitter, threads)"),
    limit: int = Query(50, description="반환할 최대 게시물 수")
):
    """검색 쿼리의 수집된 게시물들을 가져옵니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

@router.get("/report/{query_id}", response_model=ReportResponse)
async def get_report_by_query(query_id: int):
    """검색 쿼리의 분석 보고서를 가져옵니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

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
    limit: int = Query(10, description="반환할 최대 검색 수")
):
    """최근 검색 이력을 가져옵니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

@router.delete("/search/{query_id}")
async def delete_search(query_id: int):
    """검색 쿼리와 관련된 모든 데이터를 삭제합니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )
    db.query(CollectedPost).filter(CollectedPost.search_query_id == query_id).delete()
    db.query(Report).filter(Report.search_query_id == query_id).delete()

@router.get("/stats")
async def get_statistics():
    """시스템 통계를 가져옵니다."""
    # 이 엔드포인트는 Supabase 기반으로 재구현 필요
    raise HTTPException(
        status_code=501,
        detail="이 엔드포인트는 현재 사용할 수 없습니다. Supabase 기반 API를 사용하세요."
    )

@router.get("/reports/{user_nickname}")
async def get_user_reports(
    user_nickname: str,
    limit: int = Query(20, description="반환할 최대 보고서 수")
):
    """사용자의 보고서 목록을 Supabase에서 조회합니다."""
    try:
        result = await supabase_reports_service.get_user_reports(user_nickname, limit)
        
        if result["success"]:
            return {
                "success": True,
                "reports": result["data"],
                "count": result["count"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"보고서 조회 실패: {result['error']}"
            )
    except Exception as e:
        logger.error(f"Error retrieving user reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/detail/{report_id}")
async def get_report_detail(report_id: str):
    """특정 보고서의 상세 정보를 조회합니다."""
    try:
        result = await supabase_reports_service.get_report_by_id(report_id)
        
        if result["success"]:
            return {
                "success": True,
                "report": result["data"]
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="보고서를 찾을 수 없습니다."
            )
    except Exception as e:
        logger.error(f"Error retrieving report detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{report_id}/links")
async def get_report_links(report_id: str):
    """특정 보고서의 링크 목록을 조회합니다."""
    try:
        result = await supabase_reports_service.get_report_links(report_id)
        
        if result["success"]:
            return {
                "success": True,
                "links": result["data"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"링크 조회 실패: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 링크 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")

@router.delete("/reports/{report_id}")
async def delete_user_report(
    report_id: str,
    user_nickname: str = Query(description="삭제를 요청하는 사용자 닉네임")
):
    """사용자의 보고서를 삭제합니다."""
    try:
        result = await supabase_reports_service.delete_report(report_id, user_nickname)
        
        if result["success"]:
            return {
                "success": True,
                "message": "보고서가 성공적으로 삭제되었습니다."
            }
        else:
            raise HTTPException(
                status_code=403,
                detail="보고서 삭제 권한이 없거나 보고서를 찾을 수 없습니다."
            )
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{user_nickname}/stats")
async def get_user_report_stats(user_nickname: str):
    """사용자의 보고서 통계를 조회합니다."""
    try:
        result = await supabase_reports_service.get_report_stats(user_nickname)
        
        if result["success"]:
            return {
                "success": True,
                "stats": result["data"]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"통계 조회 실패: {result['error']}"
            )
    except Exception as e:
        logger.error(f"Error retrieving report stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))