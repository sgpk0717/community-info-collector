from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
# from app.api.advanced_endpoints import router as advanced_router  # 비활성화
# from app.api.schedule_endpoints import router as schedule_router  # SQLAlchemy 기반 - 비활성화
from app.api.supabase_schedule_endpoints import router as supabase_schedule_router
from app.api.user_endpoints import router as user_router
from app.api.websocket_endpoints import router as websocket_router
import logging
from app.core.logging_config import setup_logging

# 로깅 설정 - 보기 좋은 포맷 적용
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy 테이블 생성 제거 - Supabase 사용

app = FastAPI(
    title="Community Info Collector",
    description="해외 커뮤니티 정보 수집 및 분석 API - 정형/비정형 데이터 통합 수집",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["community"])
# app.include_router(advanced_router, prefix="/api/v1", tags=["advanced"])  # 비활성화
# app.include_router(schedule_router, prefix="/api/v1", tags=["schedule"])  # SQLAlchemy 기반 - 비활성화
app.include_router(supabase_schedule_router, tags=["supabase-schedule"])
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
app.include_router(websocket_router, prefix="/api/v1", tags=["websocket"])

# 새로운 스케줄 API 추가 (prefix 없이 직접 v1에 마운트)
from fastapi import APIRouter
new_schedule_router = APIRouter()

# 스케줄 관련 새 엔드포인트 추가 - 현재 비활성화
# SQLAlchemy 기반 엔드포인트는 Supabase 버전으로 대체 필요

# app.include_router(new_schedule_router, prefix="/api/v1", tags=["new-schedules"]) # 비활성화

@app.get("/")
async def root():
    return {
        "message": "Community Info Collector API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": {
            "standard": "Reddit, Twitter, Threads API",
            "advanced": "LinkedIn, Discord, HackerNews, Dynamic Web Scraping",
            "scheduling": "Automated report generation with push notifications"
        }
    }

# 스케줄러 서비스 시작
@app.on_event("startup")
async def startup_event():
    from app.api.websocket_endpoints import progress_manager
    from app.services.progress_service import progress_service
    from app.services.supabase_scheduler_service import supabase_scheduler_service
    
    progress_service.set_progress_manager(progress_manager)
    logger.info("Progress service initialized")
    
    # Supabase 스케줄러 시작 (비동기 함수이므로 await 사용)
    await supabase_scheduler_service.start()
    logger.info("✅ Supabase scheduler service started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.supabase_scheduler_service import supabase_scheduler_service
    await supabase_scheduler_service.stop()
    logger.info("🛑 Supabase scheduler service stopped")