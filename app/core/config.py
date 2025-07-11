from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # DATABASE_URL: Optional[str] = None  # SQLite 비활성화
    DATABASE_URL: Optional[str] = None  # 수파베이스 사용
    
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "CommunityCollector/1.0"
    
    TWITTER_BEARER_TOKEN: Optional[str] = None
    TWITTER_API_KEY: Optional[str] = None
    TWITTER_API_SECRET: Optional[str] = None
    TWITTER_ACCESS_TOKEN: Optional[str] = None
    TWITTER_ACCESS_TOKEN_SECRET: Optional[str] = None
    
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()