from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ReportLength(str, Enum):
    simple = "simple"
    moderate = "moderate"
    detailed = "detailed"

class ScheduleStatusEnum(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"

class SearchRequest(BaseModel):
    query: str
    sources: Optional[List[str]] = ["reddit", "twitter", "threads"]

class PostBase(BaseModel):
    source: str
    post_id: Optional[str]
    author: Optional[str]
    title: Optional[str]
    content: Optional[str]
    url: Optional[str]

class PostResponse(PostBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: int
    search_query_id: int
    summary: str
    full_report: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query_id: int
    query_text: str
    posts_collected: int
    report: Optional[ReportResponse]

# 사용자 관련 모델
class UserCreate(BaseModel):
    device_id: str
    name: Optional[str] = None
    push_token: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    push_token: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    device_id: str
    name: Optional[str]
    push_token: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 스케줄 관련 모델
class ScheduleCreate(BaseModel):
    keyword: str
    interval_minutes: int
    report_length: ReportLength
    total_reports: int

class ScheduleUpdate(BaseModel):
    status: Optional[ScheduleStatusEnum] = None
    interval_minutes: Optional[int] = None
    total_reports: Optional[int] = None

class ScheduleResponse(BaseModel):
    id: int
    user_id: int
    keyword: str
    interval_minutes: int
    report_length: str
    total_reports: int
    completed_reports: int
    status: str
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 알림 관련 모델
class NotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str
    data: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    data: Optional[dict]
    is_read: bool
    sent_at: datetime
    
    class Config:
        from_attributes = True

# 서비스 응답 모델 (내부용)
class PostData(BaseModel):
    source: str
    post_id: str
    author: Optional[str]
    title: Optional[str]
    content: Optional[str]
    url: Optional[str]

# 새로운 사용자 인증 모델 (Supabase용)
class UserRegisterRequest(BaseModel):
    nickname: str

class UserLoginRequest(BaseModel):
    nickname: str

class UserAuthResponse(BaseModel):
    id: str
    nickname: str
    status: str  # "approved" or "pending"
    created_at: Optional[str]
    last_access: Optional[str]

class SupabaseUserResponse(BaseModel):
    id: str
    nickname: str
    approval_status: str  # "Y" or "N"
    created_at: str
    last_access: str