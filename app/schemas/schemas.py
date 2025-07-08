from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

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