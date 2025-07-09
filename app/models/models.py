from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum

class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ScheduleStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("CollectedPost", back_populates="search_query")
    reports = relationship("Report", back_populates="search_query")

class CollectedPost(Base):
    __tablename__ = "collected_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # reddit, twitter, threads
    post_id = Column(String(200))
    author = Column(String(200))
    title = Column(Text)
    content = Column(Text)
    url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    search_query_id = Column(Integer, ForeignKey("search_queries.id"))
    
    search_query = relationship("SearchQuery", back_populates="posts")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    search_query_id = Column(Integer, ForeignKey("search_queries.id"))
    summary = Column(Text)
    full_report = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=True)
    user_id = Column(String(200), nullable=True)
    
    search_query = relationship("SearchQuery", back_populates="reports")
    schedule = relationship("Schedule", back_populates="reports")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(200), unique=True, nullable=False)
    name = Column(String(200), nullable=True)
    push_token = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    schedules = relationship("Schedule", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword = Column(String(500), nullable=False)
    interval_minutes = Column(Integer, nullable=False)  # 주기 (분)
    report_length = Column(String(50), nullable=False)  # simple, moderate, detailed
    total_reports = Column(Integer, nullable=False)  # 총 보고 횟수
    completed_reports = Column(Integer, default=0)  # 완료된 보고 횟수
    status = Column(Enum(ScheduleStatus), default=ScheduleStatus.ACTIVE)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="schedules")
    reports = relationship("Report", back_populates="schedule")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")