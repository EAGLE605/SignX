"""
Database utilities for industry knowledge system
Handles article storage, querying, and RAG integration
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from sqlalchemy import create_engine, func, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert

from models import (
    Base, IndustrySite, IndustryArticle, Topic, MonitoringState,
    ArticleAnalysis, article_topics, RelevanceLevel, SiteCategory
)


class IndustryKnowledgeDB:
    """Database manager for industry articles"""

    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://localhost:5432/signx'
            )

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def add_site(self, session: Session, **kwargs) -> IndustrySite:
        """Add or update a site"""
        site = session.query(IndustrySite).filter_by(name=kwargs['name']).first()

        if site:
            # Update existing
            for key, value in kwargs.items():
                setattr(site, key, value)
        else:
            # Create new
            site = IndustrySite(**kwargs)
            session.add(site)

        session.commit()
        return site

    def add_article(
        self,
        session: Session,
        site_name: str,
        title: str,
        url: str,
        content_markdown: str,
        **kwargs
    ) -> Optional[IndustryArticle]:
        """Add article if not already exists"""

        # Generate hash
        article_hash = hashlib.md5(f"{url}|{title}".encode()).hexdigest()

        # Check if exists
        existing = session.query(IndustryArticle).filter_by(article_hash=article_hash).first()
        if existing:
            return None  # Already exists

        # Get site
        site = session.query(IndustrySite).filter_by(name=site_name).first()
        if not site:
            raise ValueError(f"Site '{site_name}' not found")

        # Create preview
        content_preview = content_markdown[:500] + '...' if len(content_markdown) > 500 else content_markdown

        # Create article
        article = IndustryArticle(
            site_id=site.id,
            title=title,
            url=url,
            content_markdown=content_markdown,
            content_preview=content_preview,
            article_hash=article_hash,
            word_count=len(content_markdown.split()),
            **kwargs
        )

        session.add(article)

        # Update site stats
        site.total_articles_found += 1
        if article.relevance_level == RelevanceLevel.HIGH:
            site.total_high_value_articles += 1
        site.last_article_found_at = datetime.utcnow()

        session.commit()
        return article

    def add_topics_to_article(
        self,
        session: Session,
        article_id: int,
        topic_matches: Dict[str, int]
    ):
        """Add topic associations to article"""

        for topic_name, relevance_score in topic_matches.items():
            topic = session.query(Topic).filter_by(name=topic_name).first()
            if not topic:
                continue

            # Insert association
            stmt = insert(article_topics).values(
                article_id=article_id,
                topic_id=topic.id,
                relevance_score=relevance_score
            ).on_conflict_do_nothing()

            session.execute(stmt)

            # Update topic count
            topic.article_count = session.query(func.count(article_topics.c.article_id)).filter(
                article_topics.c.topic_id == topic.id
            ).scalar()

        session.commit()

    def get_unread_high_value(self, session: Session, limit: int = 50) -> List[IndustryArticle]:
        """Get unread high-value articles"""
        return session.query(IndustryArticle).filter(
            and_(
                IndustryArticle.read == False,
                IndustryArticle.relevance_level == RelevanceLevel.HIGH
            )
        ).order_by(desc(IndustryArticle.relevance_score), desc(IndustryArticle.published_at)).limit(limit).all()

    def get_articles_for_rag(self, session: Session, limit: int = 100) -> List[IndustryArticle]:
        """Get articles not yet added to RAG"""
        return session.query(IndustryArticle).filter(
            and_(
                IndustryArticle.added_to_rag == False,
                IndustryArticle.relevance_level == RelevanceLevel.HIGH,
                IndustryArticle.word_count >= 500  # Minimum meaningful length
            )
        ).order_by(desc(IndustryArticle.relevance_score)).limit(limit).all()

    def mark_added_to_rag(self, session: Session, article_id: int, rag_document_id: str):
        """Mark article as added to RAG corpus"""
        article = session.query(IndustryArticle).get(article_id)
        if article:
            article.added_to_rag = True
            article.rag_document_id = rag_document_id
            session.commit()

    def search_articles(
        self,
        session: Session,
        query: str,
        limit: int = 20
    ) -> List[IndustryArticle]:
        """Full-text search articles"""
        return session.query(IndustryArticle).filter(
            or_(
                IndustryArticle.title.ilike(f'%{query}%'),
                IndustryArticle.content_markdown.ilike(f'%{query}%')
            )
        ).order_by(desc(IndustryArticle.relevance_score)).limit(limit).all()

    def get_recent_by_topic(
        self,
        session: Session,
        topic_name: str,
        days: int = 30,
        limit: int = 20
    ) -> List[IndustryArticle]:
        """Get recent articles for a specific topic"""
        cutoff = datetime.utcnow() - timedelta(days=days)

        topic = session.query(Topic).filter_by(name=topic_name).first()
        if not topic:
            return []

        return session.query(IndustryArticle).join(
            article_topics
        ).filter(
            and_(
                article_topics.c.topic_id == topic.id,
                IndustryArticle.published_at >= cutoff
            )
        ).order_by(desc(IndustryArticle.published_at)).limit(limit).all()

    def get_site_stats(self, session: Session) -> List[Dict]:
        """Get statistics for all sites"""
        query = """
        SELECT
            s.name,
            s.category,
            s.relevance,
            COUNT(a.id) AS total_articles,
            COUNT(a.id) FILTER (WHERE a.relevance_level = 'high') AS high_value,
            MAX(a.published_at) AS latest_article,
            s.last_checked_at
        FROM industry_sites s
        LEFT JOIN industry_articles a ON s.id = a.site_id
        GROUP BY s.id, s.name, s.category, s.relevance, s.last_checked_at
        ORDER BY high_value DESC, total_articles DESC
        """
        result = session.execute(query)
        return [dict(row) for row in result]

    def update_monitoring_state(
        self,
        session: Session,
        site_id: int,
        new_hashes: List[str],
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Update monitoring state for a site"""
        state = session.query(MonitoringState).filter_by(site_id=site_id).first()

        if not state:
            state = MonitoringState(site_id=site_id, seen_article_hashes=[])
            session.add(state)

        # Update state
        state.seen_article_hashes = list(set(state.seen_article_hashes + new_hashes))
        state.last_check_at = datetime.utcnow()
        state.total_checks += 1

        if success:
            state.last_success_at = datetime.utcnow()
            state.total_new_articles += len(new_hashes)
        else:
            state.last_error_at = datetime.utcnow()
            state.last_error_message = error_message
            state.total_errors += 1

        session.commit()


def seed_industry_sites(db: IndustryKnowledgeDB):
    """Seed database with curated industry sites"""

    sites = [
        # Primary Sign Industry
        {
            'name': 'Signs of the Times',
            'url': 'https://www.signsofthetimes.com',
            'rss_url': 'https://www.signsofthetimes.com/rss',
            'category': SiteCategory.SIGNS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Dominant sign industry publication covering design, business, materials, and technical specs',
            'tags': ['design', 'business', 'materials', 'trends'],
            'check_frequency_hours': 12
        },
        {
            'name': 'SignCraft',
            'url': 'https://signcraft.com',
            'rss_url': 'https://signcraft.com/feed/',
            'category': SiteCategory.SIGNS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Traditional sign painting and techniques, excellent material specs and finishing details',
            'tags': ['painting', 'traditional', 'materials', 'finishing'],
            'check_frequency_hours': 24
        },
        {
            'name': 'Sign Builder Illustrated',
            'url': 'https://www.signshop.com',
            'rss_url': 'https://www.signshop.com/rss',
            'category': SiteCategory.SIGNS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Production techniques, equipment reviews, shop efficiency, CAD/CAM automation',
            'tags': ['production', 'equipment', 'automation', 'efficiency'],
            'check_frequency_hours': 12
        },

        # Structural/Engineering
        {
            'name': 'STRUCTURE Magazine',
            'url': 'https://www.structuremag.org',
            'rss_url': 'https://www.structuremag.org/feed',
            'category': SiteCategory.ENGINEERING,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Practical structural engineering for outdoor structures, foundations, wind load analysis',
            'tags': ['structural', 'engineering', 'wind load', 'foundations'],
            'check_frequency_hours': 24
        },
        {
            'name': 'Modern Steel Construction',
            'url': 'https://www.aisc.org/modernsteel',
            'rss_url': 'https://www.aisc.org/modernsteel/feed/',
            'category': SiteCategory.ENGINEERING,
            'relevance': RelevanceLevel.HIGH,
            'description': 'AISC publication with steel design case studies, connections, code updates',
            'tags': ['steel', 'aisc', 'connections', 'codes'],
            'check_frequency_hours': 24
        },
        {
            'name': 'Engineering News-Record',
            'url': 'https://www.enr.com',
            'rss_url': 'https://www.enr.com/rss/all',
            'category': SiteCategory.ENGINEERING,
            'relevance': RelevanceLevel.MEDIUM,
            'description': 'Code changes, material shortages, regulatory updates affecting structural calculations',
            'tags': ['news', 'codes', 'regulations', 'materials'],
            'check_frequency_hours': 24
        },

        # Metal Fabrication & Materials
        {
            'name': 'The Fabricator',
            'url': 'https://www.thefabricator.com',
            'rss_url': 'https://www.thefabricator.com/rss',
            'category': SiteCategory.FABRICATION,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Metal fabrication techniques, welding, cutting, bending, materials',
            'tags': ['fabrication', 'welding', 'cutting', 'bending'],
            'check_frequency_hours': 12
        },
        {
            'name': 'Tube & Pipe Journal',
            'url': 'https://www.thefabricator.com/tubepipejournal',
            'rss_url': 'https://www.thefabricator.com/tubepipejournal/rss',
            'category': SiteCategory.FABRICATION,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Tube and pipe work relevant to sign posts and structures',
            'tags': ['tube', 'pipe', 'posts', 'structures'],
            'check_frequency_hours': 24
        },
        {
            'name': 'Metal Architecture',
            'url': 'https://www.metalarchitecture.com',
            'rss_url': 'https://www.metalarchitecture.com/feed',
            'category': SiteCategory.MATERIALS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Architectural metal applications, finishing techniques, weathering data',
            'tags': ['architecture', 'finishing', 'weathering'],
            'check_frequency_hours': 48  # Inconsistent publishing
        },
        {
            'name': 'SHEET METAL PLUS',
            'url': 'https://www.sheetmetalplus.com',
            'rss_url': 'https://www.sheetmetalplus.com/feed',
            'category': SiteCategory.FABRICATION,
            'relevance': RelevanceLevel.MEDIUM,
            'description': 'CNC, CAD/CAM workflows, shop floor automation',
            'tags': ['cnc', 'cadcam', 'automation'],
            'check_frequency_hours': 48
        },

        # LED & Electrical
        {
            'name': 'LEDs Magazine',
            'url': 'https://www.ledsmagazine.com',
            'rss_url': 'https://www.ledsmagazine.com/rss',
            'category': SiteCategory.LED_LIGHTING,
            'relevance': RelevanceLevel.HIGH,
            'description': 'LED technical specs, driver technology, thermal management',
            'tags': ['led', 'drivers', 'thermal', 'specs'],
            'check_frequency_hours': 24
        },
        {
            'name': 'EC&M',
            'url': 'https://www.ecmag.com',
            'rss_url': 'https://www.ecmag.com/rss',
            'category': SiteCategory.LED_LIGHTING,
            'relevance': RelevanceLevel.MEDIUM,
            'description': 'Electrical Construction & Maintenance, NEC updates, power distribution',
            'tags': ['electrical', 'nec', 'power', 'safety'],
            'check_frequency_hours': 24
        },

        # Coatings & Materials
        {
            'name': 'CoatingsPro Magazine',
            'url': 'https://www.coatingspromag.com',
            'rss_url': 'https://www.coatingspromag.com/feed',
            'category': SiteCategory.COATINGS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Industrial coatings, surface prep, durability testing for outdoor signage',
            'tags': ['coatings', 'durability', 'weathering'],
            'check_frequency_hours': 24
        },
        {
            'name': 'Products Finishing',
            'url': 'https://www.pfonline.com',
            'rss_url': 'https://www.pfonline.com/rss',
            'category': SiteCategory.COATINGS,
            'relevance': RelevanceLevel.HIGH,
            'description': 'Powder coating, wet paint, finishing troubleshooting',
            'tags': ['powder coating', 'paint', 'finishing'],
            'check_frequency_hours': 48  # Inconsistent publishing
        },

        # Business/Operations
        {
            'name': 'ISA Sign Expo',
            'url': 'https://www.signexpo.org/blog',
            'rss_url': 'https://www.signexpo.org/blog/rss',
            'category': SiteCategory.SIGNS,
            'relevance': RelevanceLevel.MEDIUM,
            'description': 'Industry trends, business strategies, emerging technologies',
            'tags': ['trends', 'business', 'technology'],
            'check_frequency_hours': 48
        }
    ]

    session = db.get_session()
    try:
        for site_data in sites:
            db.add_site(session, **site_data)
        print(f"✅ Seeded {len(sites)} industry sites")
    finally:
        session.close()


if __name__ == "__main__":
    # Initialize database
    db = IndustryKnowledgeDB()

    print("Creating tables...")
    db.create_tables()

    print("Seeding industry sites...")
    seed_industry_sites(db)

    print("\n✅ Database initialized successfully!")
