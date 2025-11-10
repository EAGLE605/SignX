"""
SQLAlchemy models for industry knowledge articles
Stores scraped content from fabrication, sign, and manufacturing sites
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey, Table, Index, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
import enum


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Association table for article-topic many-to-many
article_topics = Table(
    'article_topics',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('industry_articles.id', ondelete='CASCADE'), primary_key=True),
    Column('topic_id', Integer, ForeignKey('topics.id', ondelete='CASCADE'), primary_key=True),
    Column('relevance_score', Integer, default=0),  # How many keyword matches
    Column('created_at', DateTime, default=datetime.utcnow)
)


class RelevanceLevel(str, enum.Enum):
    """Site/article relevance to sign manufacturing"""
    HIGH = "high"       # Directly applicable (sign techniques, metal fab)
    MEDIUM = "medium"   # Moderately applicable (general manufacturing)
    LOW = "low"         # Tangentially applicable (construction trends)


class SiteCategory(str, enum.Enum):
    """Industry website categories"""
    FABRICATION = "fabrication"
    SIGNS = "signs"
    CONSTRUCTION = "construction"
    MATERIALS = "materials"
    COATINGS = "coatings"
    LED_LIGHTING = "led_lighting"
    AUTOMATION = "automation"
    ENGINEERING = "engineering"


class IndustrySite(Base):
    """Industry websites we monitor"""
    __tablename__ = "industry_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(500))
    rss_url: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[SiteCategory] = mapped_column(SQLEnum(SiteCategory), index=True)
    relevance: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), index=True)

    # Monitoring settings
    enabled: Mapped[bool] = mapped_column(default=True)
    check_frequency_hours: Mapped[int] = mapped_column(default=24)
    last_checked_at: Mapped[Optional[datetime]]
    last_article_found_at: Mapped[Optional[datetime]]

    # Statistics
    total_articles_found: Mapped[int] = mapped_column(default=0)
    total_high_value_articles: Mapped[int] = mapped_column(default=0)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    articles: Mapped[List["IndustryArticle"]] = relationship(back_populates="site", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IndustrySite(name='{self.name}', category='{self.category}', relevance='{self.relevance}')>"


class IndustryArticle(Base):
    """Articles scraped from industry websites"""
    __tablename__ = "industry_articles"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Source info
    site_id: Mapped[int] = mapped_column(ForeignKey("industry_sites.id", ondelete="CASCADE"), index=True)

    # Article metadata
    title: Mapped[str] = mapped_column(String(500), index=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(200))
    published_at: Mapped[Optional[datetime]] = mapped_column(index=True)

    # Content
    content_markdown: Mapped[str] = mapped_column(Text)
    content_preview: Mapped[str] = mapped_column(Text)  # First 500 chars
    content_html: Mapped[Optional[str]] = mapped_column(Text)  # Original HTML

    # Analysis
    word_count: Mapped[int] = mapped_column(default=0)
    relevance_score: Mapped[int] = mapped_column(default=0, index=True)  # Total keyword matches
    relevance_level: Mapped[RelevanceLevel] = mapped_column(SQLEnum(RelevanceLevel), index=True)

    # Metadata
    article_hash: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # MD5 of URL+title
    scraped_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # User interaction
    read: Mapped[bool] = mapped_column(default=False)
    starred: Mapped[bool] = mapped_column(default=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Integration
    added_to_rag: Mapped[bool] = mapped_column(default=False, index=True)  # Added to Gemini RAG
    rag_document_id: Mapped[Optional[str]] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site: Mapped["IndustrySite"] = relationship(back_populates="articles")
    topics: Mapped[List["Topic"]] = relationship(secondary=article_topics, back_populates="articles")

    # Indexes
    __table_args__ = (
        Index('idx_articles_relevance_published', 'relevance_score', 'published_at'),
        Index('idx_articles_site_published', 'site_id', 'published_at'),
        Index('idx_articles_starred_published', 'starred', 'published_at'),
    )

    def __repr__(self):
        return f"<IndustryArticle(title='{self.title[:50]}...', relevance={self.relevance_score})>"


class Topic(Base):
    """Topics/keywords for categorizing articles"""
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(100), index=True)  # e.g., "Manufacturing Techniques"

    # Keywords for this topic
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Statistics
    article_count: Mapped[int] = mapped_column(default=0)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    articles: Mapped[List["IndustryArticle"]] = relationship(secondary=article_topics, back_populates="topics")

    def __repr__(self):
        return f"<Topic(name='{self.name}', category='{self.category}')>"


class MonitoringState(Base):
    """Track monitoring state for each site"""
    __tablename__ = "monitoring_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("industry_sites.id", ondelete="CASCADE"), unique=True)

    # State
    seen_article_hashes: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    last_check_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_success_at: Mapped[Optional[datetime]]
    last_error_at: Mapped[Optional[datetime]]
    last_error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Statistics
    total_checks: Mapped[int] = mapped_column(default=0)
    total_errors: Mapped[int] = mapped_column(default=0)
    total_new_articles: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MonitoringState(site_id={self.site_id}, last_check={self.last_check_at})>"


class ArticleAnalysis(Base):
    """Detailed analysis of article content (optional)"""
    __tablename__ = "article_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("industry_articles.id", ondelete="CASCADE"), unique=True)

    # AI-generated analysis
    summary: Mapped[Optional[str]] = mapped_column(Text)  # AI-generated summary
    key_points: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))
    actionable_insights: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text))

    # Relevance details
    manufacturing_techniques: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    materials_mentioned: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    tools_equipment: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    # Business insights
    cost_implications: Mapped[Optional[str]] = mapped_column(Text)
    efficiency_opportunities: Mapped[Optional[str]] = mapped_column(Text)
    competitive_intelligence: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata
    analyzed_by: Mapped[str] = mapped_column(String(50))  # 'claude', 'gemini', etc.
    analyzed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    confidence_score: Mapped[Optional[float]] = mapped_column()

    def __repr__(self):
        return f"<ArticleAnalysis(article_id={self.article_id}, analyzed_by='{self.analyzed_by}')>"
