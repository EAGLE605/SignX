-- Industry Knowledge Database Schema for SignX Platform
-- Stores scraped articles from fabrication, sign, and manufacturing websites
-- PostgreSQL 14+

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create custom types
CREATE TYPE relevance_level AS ENUM ('high', 'medium', 'low');
CREATE TYPE site_category AS ENUM (
    'fabrication',
    'signs',
    'construction',
    'materials',
    'coatings',
    'led_lighting',
    'automation',
    'engineering'
);

-- Industry sites table
CREATE TABLE IF NOT EXISTS industry_sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    url VARCHAR(500) NOT NULL,
    rss_url VARCHAR(500),
    category site_category NOT NULL,
    relevance relevance_level NOT NULL,

    -- Monitoring settings
    enabled BOOLEAN DEFAULT TRUE,
    check_frequency_hours INTEGER DEFAULT 24,
    last_checked_at TIMESTAMP,
    last_article_found_at TIMESTAMP,

    -- Statistics
    total_articles_found INTEGER DEFAULT 0,
    total_high_value_articles INTEGER DEFAULT 0,

    -- Metadata
    description TEXT,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sites_category ON industry_sites(category);
CREATE INDEX idx_sites_relevance ON industry_sites(relevance);
CREATE INDEX idx_sites_enabled ON industry_sites(enabled);

-- Topics table
CREATE TABLE IF NOT EXISTS topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    keywords TEXT[],
    article_count INTEGER DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_topics_category ON topics(category);
CREATE INDEX idx_topics_name_trgm ON topics USING gin (name gin_trgm_ops);

-- Industry articles table
CREATE TABLE IF NOT EXISTS industry_articles (
    id SERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES industry_sites(id) ON DELETE CASCADE,

    -- Article metadata
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    author VARCHAR(200),
    published_at TIMESTAMP,

    -- Content
    content_markdown TEXT NOT NULL,
    content_preview TEXT NOT NULL,
    content_html TEXT,

    -- Analysis
    word_count INTEGER DEFAULT 0,
    relevance_score INTEGER DEFAULT 0,
    relevance_level relevance_level NOT NULL,

    -- Metadata
    article_hash VARCHAR(32) UNIQUE NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- User interaction
    read BOOLEAN DEFAULT FALSE,
    starred BOOLEAN DEFAULT FALSE,
    notes TEXT,

    -- RAG integration
    added_to_rag BOOLEAN DEFAULT FALSE,
    rag_document_id VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_articles_site_id ON industry_articles(site_id);
CREATE INDEX idx_articles_published_at ON industry_articles(published_at DESC);
CREATE INDEX idx_articles_relevance_score ON industry_articles(relevance_score DESC);
CREATE INDEX idx_articles_relevance_level ON industry_articles(relevance_level);
CREATE INDEX idx_articles_starred ON industry_articles(starred);
CREATE INDEX idx_articles_added_to_rag ON industry_articles(added_to_rag);
CREATE INDEX idx_articles_created_at ON industry_articles(created_at DESC);
CREATE INDEX idx_articles_hash ON industry_articles(article_hash);

-- Compound indexes for common queries
CREATE INDEX idx_articles_relevance_published ON industry_articles(relevance_score DESC, published_at DESC);
CREATE INDEX idx_articles_site_published ON industry_articles(site_id, published_at DESC);
CREATE INDEX idx_articles_starred_published ON industry_articles(starred, published_at DESC) WHERE starred = TRUE;

-- Full-text search index
CREATE INDEX idx_articles_title_trgm ON industry_articles USING gin (title gin_trgm_ops);
CREATE INDEX idx_articles_content_trgm ON industry_articles USING gin (content_markdown gin_trgm_ops);

-- Article-Topic association table (many-to-many)
CREATE TABLE IF NOT EXISTS article_topics (
    article_id INTEGER NOT NULL REFERENCES industry_articles(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    relevance_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id, topic_id)
);

CREATE INDEX idx_article_topics_article ON article_topics(article_id);
CREATE INDEX idx_article_topics_topic ON article_topics(topic_id);
CREATE INDEX idx_article_topics_relevance ON article_topics(relevance_score DESC);

-- Monitoring state table
CREATE TABLE IF NOT EXISTS monitoring_state (
    id SERIAL PRIMARY KEY,
    site_id INTEGER UNIQUE NOT NULL REFERENCES industry_sites(id) ON DELETE CASCADE,

    -- State
    seen_article_hashes TEXT[],
    last_check_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error_at TIMESTAMP,
    last_error_message TEXT,

    -- Statistics
    total_checks INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    total_new_articles INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitoring_site ON monitoring_state(site_id);

-- Article analysis table (optional AI-generated insights)
CREATE TABLE IF NOT EXISTS article_analyses (
    id SERIAL PRIMARY KEY,
    article_id INTEGER UNIQUE NOT NULL REFERENCES industry_articles(id) ON DELETE CASCADE,

    -- AI-generated analysis
    summary TEXT,
    key_points TEXT[],
    actionable_insights TEXT[],

    -- Relevance details
    manufacturing_techniques TEXT[],
    materials_mentioned TEXT[],
    tools_equipment TEXT[],

    -- Business insights
    cost_implications TEXT,
    efficiency_opportunities TEXT,
    competitive_intelligence TEXT,

    -- Metadata
    analyzed_by VARCHAR(50) NOT NULL,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(3, 2)
);

CREATE INDEX idx_analyses_article ON article_analyses(article_id);
CREATE INDEX idx_analyses_analyzed_at ON article_analyses(analyzed_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_industry_sites_updated_at
    BEFORE UPDATE ON industry_sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_industry_articles_updated_at
    BEFORE UPDATE ON industry_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitoring_state_updated_at
    BEFORE UPDATE ON monitoring_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries

-- View: High-value recent articles
CREATE OR REPLACE VIEW high_value_recent_articles AS
SELECT
    a.id,
    a.title,
    a.url,
    a.published_at,
    a.relevance_score,
    a.word_count,
    s.name AS site_name,
    s.category AS site_category,
    a.starred,
    a.read,
    ARRAY_AGG(t.name) AS topics
FROM industry_articles a
JOIN industry_sites s ON a.site_id = s.id
LEFT JOIN article_topics at ON a.id = at.article_id
LEFT JOIN topics t ON at.topic_id = t.id
WHERE a.relevance_level = 'high'
    AND a.published_at > CURRENT_DATE - INTERVAL '30 days'
GROUP BY a.id, s.name, s.category
ORDER BY a.relevance_score DESC, a.published_at DESC;

-- View: Site statistics
CREATE OR REPLACE VIEW site_statistics AS
SELECT
    s.id,
    s.name,
    s.category,
    s.relevance,
    COUNT(a.id) AS total_articles,
    COUNT(a.id) FILTER (WHERE a.relevance_level = 'high') AS high_value_articles,
    COUNT(a.id) FILTER (WHERE a.published_at > CURRENT_DATE - INTERVAL '7 days') AS articles_this_week,
    MAX(a.published_at) AS latest_article_date,
    s.last_checked_at
FROM industry_sites s
LEFT JOIN industry_articles a ON s.id = a.site_id
GROUP BY s.id, s.name, s.category, s.relevance, s.last_checked_at
ORDER BY high_value_articles DESC, total_articles DESC;

-- View: Topic popularity
CREATE OR REPLACE VIEW topic_statistics AS
SELECT
    t.id,
    t.name,
    t.category,
    COUNT(DISTINCT at.article_id) AS article_count,
    AVG(a.relevance_score) AS avg_relevance,
    COUNT(DISTINCT at.article_id) FILTER (
        WHERE a.published_at > CURRENT_DATE - INTERVAL '30 days'
    ) AS articles_last_30_days
FROM topics t
LEFT JOIN article_topics at ON t.id = at.topic_id
LEFT JOIN industry_articles a ON at.article_id = a.id
GROUP BY t.id, t.name, t.category
ORDER BY article_count DESC;

-- Insert default topics
INSERT INTO topics (name, category, keywords) VALUES
-- Manufacturing Techniques
('Welding', 'Manufacturing Techniques', ARRAY['welding', 'weld', 'tig', 'mig', 'arc', 'spot weld']),
('Laser Cutting', 'Manufacturing Techniques', ARRAY['laser', 'laser cutting', 'laser engraving', 'co2 laser', 'fiber laser']),
('Plasma Cutting', 'Manufacturing Techniques', ARRAY['plasma', 'plasma cutting', 'plasma cutter']),
('CNC Machining', 'Manufacturing Techniques', ARRAY['cnc', 'machining', 'mill', 'lathe', 'router']),
('Metal Bending', 'Manufacturing Techniques', ARRAY['bending', 'brake', 'press brake', 'forming', 'roll forming']),
('Waterjet Cutting', 'Manufacturing Techniques', ARRAY['waterjet', 'water jet', 'abrasive']),

-- Materials & Finishes
('Aluminum', 'Materials & Finishes', ARRAY['aluminum', 'aluminium', 'alloy', '6061', '5052']),
('Steel', 'Materials & Finishes', ARRAY['steel', 'stainless', 'galvanized', 'carbon steel']),
('Acrylic', 'Materials & Finishes', ARRAY['acrylic', 'plexiglass', 'perspex']),
('Powder Coating', 'Materials & Finishes', ARRAY['powder coating', 'powder coat', 'coating']),
('Vinyl', 'Materials & Finishes', ARRAY['vinyl', 'wrap', 'decal', 'adhesive']),

-- Sign-Specific
('LED Signs', 'Sign-Specific', ARRAY['led', 'illuminated', 'backlit', 'lit sign']),
('Channel Letters', 'Sign-Specific', ARRAY['channel letter', 'channel', 'dimensional letter']),
('Monument Signs', 'Sign-Specific', ARRAY['monument', 'monument sign', 'ground sign', 'pylon']),
('Digital Signage', 'Sign-Specific', ARRAY['digital', 'electronic', 'lcd', 'led display']),
('Wayfinding', 'Sign-Specific', ARRAY['wayfinding', 'directional', 'ada', 'accessibility']),

-- Engineering & Codes
('Wind Load', 'Engineering & Codes', ARRAY['wind load', 'wind speed', 'structural', 'asce']),
('Building Codes', 'Engineering & Codes', ARRAY['building code', 'ibc', 'permit', 'zoning']),
('Foundation Design', 'Engineering & Codes', ARRAY['foundation', 'footing', 'anchor', 'concrete']),

-- Business & Operations
('Pricing', 'Business & Operations', ARRAY['pricing', 'cost', 'quote', 'estimate', 'margin']),
('Workflow', 'Business & Operations', ARRAY['workflow', 'process', 'efficiency', 'productivity']),
('Automation', 'Business & Operations', ARRAY['automation', 'automate', 'software', 'system'])

ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO signx_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO signx_user;

-- Comments for documentation
COMMENT ON TABLE industry_sites IS 'Industry websites monitored for content scraping';
COMMENT ON TABLE industry_articles IS 'Articles scraped from industry websites';
COMMENT ON TABLE topics IS 'Topics/keywords for categorizing articles';
COMMENT ON TABLE article_topics IS 'Many-to-many relationship between articles and topics';
COMMENT ON TABLE monitoring_state IS 'Tracking state for monitoring system';
COMMENT ON TABLE article_analyses IS 'AI-generated analysis of article content';

COMMENT ON COLUMN industry_articles.article_hash IS 'MD5 hash of URL+title for deduplication';
COMMENT ON COLUMN industry_articles.relevance_score IS 'Total number of keyword matches';
COMMENT ON COLUMN industry_articles.added_to_rag IS 'Whether article has been added to Gemini RAG corpus';
