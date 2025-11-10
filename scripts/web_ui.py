#!/usr/bin/env python3
"""
Simple web UI for browsing industry knowledge articles
FastAPI + HTML interface for searching and reading articles
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

try:
    from sqlalchemy import func, or_, and_
    from sqlalchemy.orm import Session, joinedload
except ImportError:
    print("❌ sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
    sys.exit(1)

# Add database utilities to path
sys.path.insert(0, str(Path(__file__).parent / "database"))
from db_utils import IndustryKnowledgeDB
from models import IndustryArticle, IndustrySite, Topic, RelevanceLevel, SiteCategory

# Initialize FastAPI
app = FastAPI(
    title="SignX Industry Knowledge Browser",
    description="Browse and search industry articles",
    version="1.0.0"
)

# Initialize database
db = IndustryKnowledgeDB()

# Dependency to get DB session
def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# === API ENDPOINTS ===

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with search and filters"""
    return HTML_TEMPLATE


@app.get("/api/articles", response_class=JSONResponse)
async def get_articles(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Site category"),
    relevance: Optional[str] = Query(None, description="Relevance level"),
    topic: Optional[str] = Query(None, description="Topic name"),
    starred: Optional[bool] = Query(None, description="Only starred"),
    unread: Optional[bool] = Query(None, description="Only unread"),
    days: int = Query(30, description="Days back to search"),
    limit: int = Query(50, description="Max results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get articles with filters"""

    session = next(get_db())

    # Base query
    query = session.query(IndustryArticle).join(IndustrySite)

    # Date filter
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = query.filter(IndustryArticle.published_at >= cutoff)

    # Search query
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                IndustryArticle.title.ilike(search_term),
                IndustryArticle.content_markdown.ilike(search_term)
            )
        )

    # Category filter
    if category:
        query = query.filter(IndustrySite.category == category)

    # Relevance filter
    if relevance:
        query = query.filter(IndustryArticle.relevance_level == relevance)

    # Topic filter
    if topic:
        topic_obj = session.query(Topic).filter_by(name=topic).first()
        if topic_obj:
            query = query.filter(IndustryArticle.topics.contains(topic_obj))

    # Starred/unread filters
    if starred:
        query = query.filter(IndustryArticle.starred == True)
    if unread:
        query = query.filter(IndustryArticle.read == False)

    # Order by relevance and date
    query = query.order_by(
        IndustryArticle.relevance_score.desc(),
        IndustryArticle.published_at.desc()
    )

    # Pagination
    total = query.count()
    articles = query.offset(offset).limit(limit).all()

    # Convert to JSON
    results = []
    for article in articles:
        results.append({
            'id': article.id,
            'title': article.title,
            'url': article.url,
            'site_name': article.site.name,
            'site_category': article.site.category.value,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'relevance_score': article.relevance_score,
            'relevance_level': article.relevance_level.value,
            'word_count': article.word_count,
            'preview': article.content_preview,
            'topics': [t.name for t in article.topics][:5],
            'read': article.read,
            'starred': article.starred,
            'added_to_rag': article.added_to_rag
        })

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'results': results
    }


@app.get("/api/articles/{article_id}", response_class=JSONResponse)
async def get_article(article_id: int):
    """Get single article with full content"""

    session = next(get_db())
    article = session.query(IndustryArticle).options(
        joinedload(IndustryArticle.site),
        joinedload(IndustryArticle.topics)
    ).get(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        'id': article.id,
        'title': article.title,
        'url': article.url,
        'author': article.author,
        'site_name': article.site.name,
        'site_category': article.site.category.value,
        'site_url': article.site.url,
        'published_at': article.published_at.isoformat() if article.published_at else None,
        'relevance_score': article.relevance_score,
        'relevance_level': article.relevance_level.value,
        'word_count': article.word_count,
        'content_markdown': article.content_markdown,
        'topics': [{'name': t.name, 'category': t.category} for t in article.topics],
        'read': article.read,
        'starred': article.starred,
        'notes': article.notes,
        'added_to_rag': article.added_to_rag,
        'scraped_at': article.scraped_at.isoformat()
    }


@app.post("/api/articles/{article_id}/star")
async def star_article(article_id: int):
    """Toggle star on article"""
    session = next(get_db())
    article = session.query(IndustryArticle).get(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.starred = not article.starred
    session.commit()

    return {'starred': article.starred}


@app.post("/api/articles/{article_id}/read")
async def mark_read(article_id: int):
    """Mark article as read"""
    session = next(get_db())
    article = session.query(IndustryArticle).get(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.read = True
    session.commit()

    return {'read': True}


@app.get("/api/stats", response_class=JSONResponse)
async def get_stats():
    """Get overall statistics"""

    session = next(get_db())

    total_articles = session.query(func.count(IndustryArticle.id)).scalar()
    high_value = session.query(func.count(IndustryArticle.id)).filter(
        IndustryArticle.relevance_level == RelevanceLevel.HIGH
    ).scalar()
    unread = session.query(func.count(IndustryArticle.id)).filter(
        IndustryArticle.read == False
    ).scalar()
    starred = session.query(func.count(IndustryArticle.id)).filter(
        IndustryArticle.starred == True
    ).scalar()
    in_rag = session.query(func.count(IndustryArticle.id)).filter(
        IndustryArticle.added_to_rag == True
    ).scalar()

    # Recent articles (last 7 days)
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent = session.query(func.count(IndustryArticle.id)).filter(
        IndustryArticle.published_at >= cutoff
    ).scalar()

    # By category
    by_category = session.query(
        IndustrySite.category,
        func.count(IndustryArticle.id)
    ).join(IndustryArticle).group_by(IndustrySite.category).all()

    # Top topics
    top_topics = session.query(
        Topic.name,
        func.count(IndustryArticle.id)
    ).join(Topic.articles).group_by(Topic.name).order_by(
        func.count(IndustryArticle.id).desc()
    ).limit(10).all()

    return {
        'total_articles': total_articles,
        'high_value': high_value,
        'unread': unread,
        'starred': starred,
        'in_rag': in_rag,
        'recent_7_days': recent,
        'by_category': [{'category': c.value, 'count': cnt} for c, cnt in by_category],
        'top_topics': [{'name': name, 'count': cnt} for name, cnt in top_topics]
    }


@app.get("/api/topics", response_class=JSONResponse)
async def get_topics():
    """Get all topics"""
    session = next(get_db())
    topics = session.query(Topic).order_by(Topic.name).all()

    return [
        {'name': t.name, 'category': t.category, 'article_count': t.article_count}
        for t in topics
    ]


@app.get("/api/sites", response_class=JSONResponse)
async def get_sites():
    """Get all monitored sites"""
    session = next(get_db())
    sites = session.query(IndustrySite).order_by(IndustrySite.name).all()

    return [
        {
            'name': s.name,
            'url': s.url,
            'category': s.category.value,
            'relevance': s.relevance.value,
            'total_articles': s.total_articles_found,
            'high_value_articles': s.total_high_value_articles,
            'last_checked': s.last_checked_at.isoformat() if s.last_checked_at else None
        }
        for s in sites
    ]


# === HTML TEMPLATE ===

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SignX Industry Knowledge Browser</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
        }
        header h1 { font-size: 2em; margin-bottom: 10px; }
        header p { opacity: 0.9; }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card .number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .stat-card .label {
            color: #666;
            font-size: 0.9em;
        }

        .search-bar {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .search-bar input {
            width: 100%;
            padding: 12px;
            font-size: 1em;
            border: 2px solid #ddd;
            border-radius: 6px;
            transition: border-color 0.3s;
        }
        .search-bar input:focus {
            outline: none;
            border-color: #667eea;
        }

        .filters {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        .filters select, .filters button {
            padding: 8px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        .filters select:hover, .filters button:hover {
            border-color: #667eea;
        }
        .filters button {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        .filters button:hover {
            background: #5568d3;
        }

        .articles {
            display: grid;
            gap: 20px;
        }
        .article-card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .article-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .article-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        .article-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        .article-meta {
            display: flex;
            gap: 15px;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 12px;
        }
        .article-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .badge-high { background: #d4edda; color: #155724; }
        .badge-medium { background: #fff3cd; color: #856404; }
        .badge-low { background: #f8d7da; color: #721c24; }

        .topics {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 12px;
        }
        .topic-tag {
            background: #e7e7ff;
            color: #667eea;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }

        .empty {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            overflow-y: auto;
        }
        .modal.active { display: block; }
        .modal-content {
            max-width: 900px;
            margin: 40px auto;
            background: white;
            border-radius: 10px;
            padding: 40px;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 2em;
            cursor: pointer;
            color: #999;
        }
        .modal-close:hover { color: #333; }

        .article-content {
            line-height: 1.8;
            font-size: 1.05em;
        }
        .article-content h1, .article-content h2 {
            margin: 30px 0 15px 0;
            color: #333;
        }
        .article-content p {
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏭 SignX Industry Knowledge Browser</h1>
            <p>15 monitored sites • Updated daily • Free RSS feeds</p>
        </header>

        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">Total Articles</div>
            </div>
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">High Value</div>
            </div>
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">Unread</div>
            </div>
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">Starred</div>
            </div>
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">In RAG</div>
            </div>
            <div class="stat-card">
                <div class="number">-</div>
                <div class="label">Last 7 Days</div>
            </div>
        </div>

        <div class="search-bar">
            <input type="text" id="search" placeholder="🔍 Search articles (title, content, topics)...">
            <div class="filters">
                <select id="category">
                    <option value="">All Categories</option>
                    <option value="signs">Signs</option>
                    <option value="fabrication">Fabrication</option>
                    <option value="engineering">Engineering</option>
                    <option value="materials">Materials</option>
                    <option value="coatings">Coatings</option>
                    <option value="led_lighting">LED Lighting</option>
                    <option value="automation">Automation</option>
                </select>
                <select id="relevance">
                    <option value="">All Relevance</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
                <select id="days">
                    <option value="7">Last 7 Days</option>
                    <option value="30" selected>Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                    <option value="365">Last Year</option>
                </select>
                <button onclick="search()">Search</button>
                <button onclick="clearFilters()">Clear</button>
            </div>
        </div>

        <div class="articles" id="articles">
            <div class="loading">Loading articles...</div>
        </div>
    </div>

    <!-- Article Modal -->
    <div class="modal" id="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modal-body">Loading...</div>
        </div>
    </div>

    <script>
        let articles = [];

        // Load stats
        async function loadStats() {
            const res = await fetch('/api/stats');
            const stats = await res.json();

            document.querySelectorAll('.stat-card')[0].querySelector('.number').textContent = stats.total_articles;
            document.querySelectorAll('.stat-card')[1].querySelector('.number').textContent = stats.high_value;
            document.querySelectorAll('.stat-card')[2].querySelector('.number').textContent = stats.unread;
            document.querySelectorAll('.stat-card')[3].querySelector('.number').textContent = stats.starred;
            document.querySelectorAll('.stat-card')[4].querySelector('.number').textContent = stats.in_rag;
            document.querySelectorAll('.stat-card')[5].querySelector('.number').textContent = stats.recent_7_days;
        }

        // Load articles
        async function loadArticles(params = {}) {
            const container = document.getElementById('articles');
            container.innerHTML = '<div class="loading">Loading articles...</div>';

            const query = new URLSearchParams(params).toString();
            const res = await fetch(`/api/articles?${query}`);
            const data = await res.json();

            articles = data.results;

            if (articles.length === 0) {
                container.innerHTML = `
                    <div class="empty">
                        <div class="empty-icon">📭</div>
                        <h2>No articles found</h2>
                        <p>Try adjusting your search filters</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = articles.map(article => `
                <div class="article-card" onclick="openArticle(${article.id})">
                    <div class="article-header">
                        <div style="flex: 1;">
                            <div class="article-title">${article.title}</div>
                            <div class="article-meta">
                                <span>🏢 ${article.site_name}</span>
                                <span>📅 ${new Date(article.published_at).toLocaleDateString()}</span>
                                <span>📊 Score: ${article.relevance_score}</span>
                                <span>📝 ${article.word_count.toLocaleString()} words</span>
                            </div>
                        </div>
                        <span class="badge badge-${article.relevance_level}">${article.relevance_level.toUpperCase()}</span>
                    </div>
                    <div class="article-preview">${article.preview}</div>
                    <div class="topics">
                        ${article.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}
                    </div>
                </div>
            `).join('');
        }

        // Search
        function search() {
            const params = {
                q: document.getElementById('search').value,
                category: document.getElementById('category').value,
                relevance: document.getElementById('relevance').value,
                days: document.getElementById('days').value,
                limit: 50
            };
            loadArticles(params);
        }

        // Clear filters
        function clearFilters() {
            document.getElementById('search').value = '';
            document.getElementById('category').value = '';
            document.getElementById('relevance').value = '';
            document.getElementById('days').value = '30';
            search();
        }

        // Open article modal
        async function openArticle(id) {
            const modal = document.getElementById('modal');
            const body = document.getElementById('modal-body');

            modal.classList.add('active');
            body.innerHTML = '<div class="loading">Loading article...</div>';

            const res = await fetch(`/api/articles/${id}`);
            const article = await res.json();

            // Mark as read
            await fetch(`/api/articles/${id}/read`, { method: 'POST' });

            body.innerHTML = `
                <h1>${article.title}</h1>
                <div class="article-meta">
                    <span>🏢 ${article.site_name}</span>
                    <span>📅 ${new Date(article.published_at).toLocaleDateString()}</span>
                    <span>📊 Score: ${article.relevance_score}/60</span>
                    <span>📝 ${article.word_count.toLocaleString()} words</span>
                </div>
                <div class="topics" style="margin: 20px 0;">
                    ${article.topics.map(t => `<span class="topic-tag">${t.name}</span>`).join('')}
                </div>
                <div style="margin: 20px 0;">
                    <a href="${article.url}" target="_blank" style="color: #667eea; text-decoration: none;">
                        🔗 View Original Article
                    </a>
                </div>
                <hr style="margin: 30px 0;">
                <div class="article-content">${markdownToHTML(article.content_markdown)}</div>
            `;
        }

        // Close modal
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        // Simple markdown to HTML
        function markdownToHTML(md) {
            return md
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
        }

        // Enter to search
        document.getElementById('search').addEventListener('keypress', e => {
            if (e.key === 'Enter') search();
        });

        // Initial load
        loadStats();
        loadArticles({ days: 30, limit: 50 });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn

    print("="*80)
    print("🌐 SignX Industry Knowledge Browser")
    print("="*80)
    print("\nStarting web server...")
    print("Open browser: http://localhost:8080")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
