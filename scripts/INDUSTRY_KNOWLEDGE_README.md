# Industry Knowledge System for SignX Platform

Automated scraping and knowledge base system for fabrication, sign manufacturing, and engineering industry websites.

## 🎯 Purpose

Build a comprehensive knowledge base by monitoring 15+ industry websites covering:
- Sign manufacturing techniques and trends
- Metal fabrication and welding
- Structural engineering and building codes
- LED technology and electrical systems
- Coatings and finishing
- Business operations and automation

## 📊 Database Schema

### Tables

**industry_sites** - Source websites we monitor
- 15 curated sites across 7 categories
- RSS feeds and monitoring settings
- Statistics tracking

**industry_articles** - Scraped article content
- Full markdown content
- Relevance scoring (keyword matches)
- User interaction (read, starred, notes)
- RAG integration tracking

**topics** - Categorization keywords
- 20+ pre-seeded topics
- Manufacturing techniques, materials, sign-specific, engineering, business
- Automatic article categorization

**article_topics** - Many-to-many relationship
- Links articles to relevant topics
- Tracks keyword match scores

**monitoring_state** - Scraper state tracking
- Seen article hashes (deduplication)
- Error tracking and statistics

**article_analyses** - AI-generated insights (optional)
- Summaries and key points
- Manufacturing techniques mentioned
- Business/cost implications

###Views

**high_value_recent_articles** - Quick access to best content
**site_statistics** - Monitor scraping performance
**topic_statistics** - Track topic popularity

## 🚀 Quick Start

### 1. Initialize Database

```bash
# Option A: Run SQL directly
psql -d signx -f scripts/database/init_schema.sql

# Option B: Use Python utilities
cd scripts/database
python db_utils.py
```

### 2. Install Dependencies

```bash
pip install feedparser html2text sqlalchemy psycopg2-binary
```

### 3. Scrape Initial Content

```bash
# Scrape all 15 sites
python scripts/scrape_industry_sites.py

# Or specific categories
python scripts/scrape_industry_sites.py signs fabrication engineering
```

### 4. Set Up Monitoring (Optional)

```bash
# Check for new articles daily
python scripts/monitor_industry_news.py --report

# Add to crontab (Linux) or Task Scheduler (Windows)
# Daily at 6 AM:
0 6 * * * cd /path/to/SignX && python scripts/monitor_industry_news.py --report
```

## 📖 Usage Examples

### Query High-Value Articles

```python
from scripts.database.db_utils import IndustryKnowledgeDB

db = IndustryKnowledgeDB()
session = db.get_session()

# Get unread high-value articles
articles = db.get_unread_high_value(session, limit=10)

for article in articles:
    print(f"{article.title} (Score: {article.relevance_score})")
    print(f"  {article.url}")
    print(f"  Topics: {[t.name for t in article.topics]}")
```

### Search Articles

```python
# Full-text search
results = db.search_articles(session, "powder coating aluminum", limit=20)

# By topic
welding_articles = db.get_recent_by_topic(session, "Welding", days=30)
```

### Get Articles for RAG

```python
# Get high-value articles not yet in RAG corpus
articles = db.get_articles_for_rag(session, limit=100)

for article in articles:
    # Add to Gemini RAG corpus
    doc_id = add_to_gemini_rag(article.content_markdown)

    # Mark as added
    db.mark_added_to_rag(session, article.id, doc_id)
```

### Site Statistics

```python
stats = db.get_site_stats(session)

for site in stats:
    print(f"{site['name']}: {site['total_articles']} articles, {site['high_value']} high-value")
```

## 🏭 Monitored Sites

### High-Priority (check every 12-24 hours)

**Signs**
- Signs of the Times (signsofthetimes.com) - Daily updates
- SignCraft (signcraft.com) - Materials and finishing
- Sign Builder Illustrated (signshop.com) - Production techniques

**Fabrication**
- The Fabricator (thefabricator.com) - Metal fab bible
- Tube & Pipe Journal - Post and structure work

**Engineering**
- STRUCTURE Magazine (structuremag.org) - Wind loads, foundations
- Modern Steel Construction - AISC case studies

**LED/Electrical**
- LEDs Magazine (ledsmagazine.com) - LED specs and thermal management

**Coatings**
- CoatingsPro Magazine - Industrial coatings, durability
- Products Finishing - Powder coating, paint

### Medium-Priority (check every 24-48 hours)

- Engineering News-Record - Code changes
- EC&M - Electrical codes and safety
- Metal Architecture - Finishing techniques
- SHEET METAL PLUS - CNC and automation
- ISA Sign Expo - Industry trends

## 📈 Relevance Scoring

Articles are scored by keyword matches across 6 categories:

1. **Manufacturing Techniques** (10 keywords)
   - welding, cutting, bending, cnc, laser, plasma, etc.

2. **Materials & Finishes** (10 keywords)
   - aluminum, steel, powder coating, vinyl, etc.

3. **Sign-Specific** (10 keywords)
   - monument sign, channel letter, LED, wayfinding, etc.

4. **Engineering & Codes** (10 keywords)
   - wind load, building code, foundation, ASCE, IBC, etc.

5. **Business & Operations** (10 keywords)
   - quoting, pricing, workflow, automation, efficiency, etc.

6. **Installation** (10 keywords)
   - mounting, anchor, crane, rigging, safety, etc.

**Scoring**:
- **High relevance** (6+ matches) - Must read
- **Medium relevance** (2-5 matches) - Review later
- **Low relevance** (0-1 matches) - Skip

## 🔄 Monitoring System

The monitor tracks seen articles to avoid duplicates:

```python
from scripts.monitor_industry_news import IndustryNewsMonitor

monitor = IndustryNewsMonitor()

# Check all sites
new_articles = monitor.check_all()

# Generate markdown report
report_path = monitor.generate_report(new_articles)

# Send notification (console for now, email/Slack future)
monitor.send_notification(new_articles)
```

**State Management**:
- Seen article hashes stored in `monitoring_state` table
- Only articles from last 7 days are considered
- Error tracking for troubleshooting failed scrapes

## 🎨 Integration with SignX Platform

### Add to Gemini RAG Corpus

```python
# Get high-value articles
articles = db.get_articles_for_rag(session, limit=100)

# Convert to Gemini-compatible format
for article in articles:
    doc = {
        'title': article.title,
        'content': article.content_markdown,
        'source': article.site.name,
        'url': article.url,
        'date': article.published_at,
        'topics': [t.name for t in article.topics]
    }

    # Upload to Gemini
    corpus_id = upload_to_gemini_rag(doc)

    # Mark as added
    db.mark_added_to_rag(session, article.id, corpus_id)
```

### Use in Quote Generation

```sql
-- Find relevant articles for customer query
SELECT a.title, a.content_preview, a.url
FROM industry_articles a
JOIN article_topics at ON a.id = at.article_id
JOIN topics t ON at.topic_id = t.id
WHERE t.name IN ('Monument Signs', 'LED Signs', 'Aluminum')
  AND a.relevance_level = 'high'
  AND a.published_at > NOW() - INTERVAL '1 year'
ORDER BY a.relevance_score DESC
LIMIT 10;
```

### Display in UI

```javascript
// Fetch recent high-value articles
const articles = await fetch('/api/knowledge/recent?relevance=high&limit=10');

// Display in dashboard
articles.forEach(article => {
  displayArticle(article.title, article.preview, article.topics);
});
```

## 🔧 Maintenance

### Update Site List

```python
from scripts.database.db_utils import IndustryKnowledgeDB, SiteCategory, RelevanceLevel

db = IndustryKnowledgeDB()
session = db.get_session()

db.add_site(
    session,
    name="New Site",
    url="https://newsite.com",
    rss_url="https://newsite.com/feed",
    category=SiteCategory.SIGNS,
    relevance=RelevanceLevel.HIGH,
    description="New industry site",
    tags=['new', 'trending'],
    check_frequency_hours=24
)
```

### Add New Topics

```sql
INSERT INTO topics (name, category, keywords) VALUES
('New Topic', 'Category', ARRAY['keyword1', 'keyword2', 'keyword3']);
```

### Backup Database

```bash
pg_dump signx -t industry_sites -t industry_articles -t topics -t article_topics > industry_knowledge_backup.sql
```

## 📊 Analytics Queries

### Top Sites by High-Value Content

```sql
SELECT name, total_high_value_articles, total_articles_found
FROM industry_sites
ORDER BY total_high_value_articles DESC;
```

### Most Popular Topics

```sql
SELECT t.name, t.category, COUNT(at.article_id) AS article_count
FROM topics t
JOIN article_topics at ON t.id = at.topic_id
GROUP BY t.id, t.name, t.category
ORDER BY article_count DESC
LIMIT 20;
```

### Articles Added to RAG

```sql
SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE added_to_rag = TRUE) AS in_rag
FROM industry_articles
WHERE relevance_level = 'high';
```

### Weekly Activity

```sql
SELECT
  DATE_TRUNC('week', published_at) AS week,
  COUNT(*) AS articles,
  AVG(relevance_score) AS avg_score
FROM industry_articles
WHERE published_at > NOW() - INTERVAL '3 months'
GROUP BY week
ORDER BY week DESC;
```

## 🚨 Troubleshooting

### RSS Feed Not Working

```python
# Test feed manually
import feedparser
feed = feedparser.parse('https://site.com/feed')
print(f"Entries: {len(feed.entries)}")
print(f"Errors: {feed.bozo_exception if feed.bozo else 'None'}")
```

### No Articles Found

1. Check if site is enabled: `SELECT * FROM industry_sites WHERE enabled = FALSE;`
2. Check monitoring state: `SELECT * FROM monitoring_state WHERE last_error_message IS NOT NULL;`
3. Verify RSS URL is correct
4. Try alternative RSS patterns (`/rss`, `/feed/`, `/atom.xml`)

### Database Connection Issues

```bash
# Test connection
psql -d signx -c "SELECT COUNT(*) FROM industry_articles;"

# Check environment variable
echo $DATABASE_URL
```

## 📝 Future Enhancements

- [ ] Email/Slack notifications for new high-value articles
- [ ] AI summarization for long articles (Claude/Gemini)
- [ ] Automatic RAG corpus updates
- [ ] Competitor monitoring (pricing, lead times)
- [ ] Trend analysis and reporting
- [ ] Integration with quote generation workflow
- [ ] Mobile app for reading on-the-go

## 🤝 Contributing

To add new sites or improve categorization:

1. Add site to `INDUSTRY_SITES` in `scrape_industry_sites.py`
2. Test RSS feed: `python scrape_industry_sites.py`
3. Add to database: `db.add_site(session, ...)`
4. Run initial scrape
5. Review relevance scores and adjust keywords if needed

---

**Built for SignX Platform** | **Powered by 15+ industry sources** | **Updated daily**
