from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.api.advanced_endpoints import router as advanced_router
from app.api.schedule_endpoints import router as schedule_router
from app.api.user_endpoints import router as user_router
from app.db.base import engine, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

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
app.include_router(advanced_router, prefix="/api/v1", tags=["advanced"])
app.include_router(schedule_router, prefix="/api/v1", tags=["schedule"])
app.include_router(user_router, prefix="/api/v1/users", tags=["users"])

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
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()
    logger.info("Scheduler service started")

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.scheduler_service import scheduler_service
    scheduler_service.stop()
    logger.info("Scheduler service stopped")