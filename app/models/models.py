from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

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
    
    search_query = relationship("SearchQuery", back_populates="reports")