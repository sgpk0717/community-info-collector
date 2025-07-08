from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router
from app.api.advanced_endpoints import router as advanced_router
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

@app.get("/")
async def root():
    return {
        "message": "Community Info Collector API",
        "version": "2.0.0",
        "docs": "/docs",
        "features": {
            "standard": "Reddit, Twitter, Threads API",
            "advanced": "LinkedIn, Discord, HackerNews, Dynamic Web Scraping"
        }
    }