#!/usr/bin/env python3
"""
Scrape The Unwind AI articles using Firecrawl API
Bypasses 403 errors and converts to structured data
"""

import os
import json
from datetime import datetime
from typing import List, Dict
try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("❌ Firecrawl not installed. Run: pip install firecrawl-py")
    exit(1)


def scrape_unwind_articles(api_key: str = None) -> List[Dict]:
    """
    Scrape all articles from The Unwind AI archive

    Args:
        api_key: Firecrawl API key (or set FIRECRAWL_API_KEY env var)

    Returns:
        List of article dictionaries with title, date, url, summary, tags
    """
    if not api_key:
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY not set. Get one from https://firecrawl.dev")

    app = FirecrawlApp(api_key=api_key)

    url = "https://www.theunwindai.com/archive?tags=AI+Tutorial&tags=AI+Blogs&tags=Daily+Unwind&tags=Weekly+Unwind"

    print(f"🔥 Scraping: {url}")

    # Scrape with formats: markdown for content, links for all article URLs
    result = app.scrape_url(
        url,
        params={
            'formats': ['markdown', 'links', 'html'],
            'onlyMainContent': True,
            'waitFor': 2000  # Wait for JS to load
        }
    )

    print(f"✅ Scraped successfully!")

    # Extract article metadata
    articles = []

    # Parse the markdown content
    markdown = result.get('markdown', '')
    links = result.get('links', [])

    print(f"\n📄 Found {len(links)} links on page")

    # Filter for article links
    article_links = [
        link for link in links
        if '/p/' in link  # The Unwind uses /p/ for posts
    ]

    print(f"📰 Found {len(article_links)} article links\n")

    # Now scrape each article for full details
    for idx, article_url in enumerate(article_links[:10], 1):  # Limit to first 10 for demo
        try:
            print(f"[{idx}/{min(10, len(article_links))}] Scraping: {article_url}")

            article_result = app.scrape_url(
                article_url,
                params={
                    'formats': ['markdown', 'html'],
                    'onlyMainContent': True
                }
            )

            # Extract metadata from article
            article_markdown = article_result.get('markdown', '')

            # Simple parsing (you could use BeautifulSoup for more robust parsing)
            lines = article_markdown.split('\n')
            title = lines[0].replace('#', '').strip() if lines else 'Unknown'

            articles.append({
                'title': title,
                'url': article_url,
                'markdown': article_markdown[:500] + '...',  # First 500 chars
                'scraped_at': datetime.now().isoformat(),
                'full_content': article_markdown
            })

        except Exception as e:
            print(f"  ⚠️  Failed to scrape {article_url}: {e}")
            continue

    return articles


def save_articles(articles: List[Dict], output_dir: str = "./scraped_articles"):
    """Save articles to JSON and individual markdown files"""
    os.makedirs(output_dir, exist_ok=True)

    # Save all as JSON
    json_path = f"{output_dir}/unwind_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved JSON: {json_path}")

    # Save individual markdown files
    for idx, article in enumerate(articles, 1):
        safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]  # Limit filename length

        md_path = f"{output_dir}/{idx:02d}_{safe_title}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {article['title']}\n\n")
            f.write(f"**URL**: {article['url']}\n\n")
            f.write(f"**Scraped**: {article['scraped_at']}\n\n")
            f.write("---\n\n")
            f.write(article['full_content'])

        print(f"  📝 {md_path}")

    print(f"\n✅ Saved {len(articles)} articles to {output_dir}/")


def analyze_articles(articles: List[Dict]) -> Dict:
    """Analyze article topics and relevance to SignX Platform"""

    # Keywords relevant to SignX
    relevant_keywords = {
        'RAG': ['rag', 'retrieval', 'vector', 'embedding'],
        'Agents': ['agent', 'autonomous', 'multi-agent', 'agentic'],
        'Document Processing': ['document', 'pdf', 'ocr', 'parsing'],
        'LLMs': ['llm', 'gpt', 'claude', 'gemini', 'model'],
        'Business Automation': ['automation', 'workflow', 'pipeline', 'production'],
        'Web Scraping': ['scraping', 'crawling', 'extraction', 'firecrawl'],
        'Cost Optimization': ['cost', 'pricing', 'optimization', 'efficiency']
    }

    analysis = {
        'total_articles': len(articles),
        'by_topic': {},
        'high_relevance': [],
        'medium_relevance': [],
        'low_relevance': []
    }

    for article in articles:
        content_lower = (article.get('full_content', '') + article.get('title', '')).lower()

        # Count keywords by topic
        relevance_score = 0
        matched_topics = []

        for topic, keywords in relevant_keywords.items():
            count = sum(1 for kw in keywords if kw in content_lower)
            if count > 0:
                matched_topics.append(topic)
                relevance_score += count
                analysis['by_topic'][topic] = analysis['by_topic'].get(topic, 0) + 1

        # Categorize by relevance
        article_summary = {
            'title': article['title'],
            'url': article['url'],
            'topics': matched_topics,
            'score': relevance_score
        }

        if relevance_score >= 5:
            analysis['high_relevance'].append(article_summary)
        elif relevance_score >= 2:
            analysis['medium_relevance'].append(article_summary)
        else:
            analysis['low_relevance'].append(article_summary)

    return analysis


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🔥 The Unwind AI Article Scraper")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]

    if not api_key:
        print("\n❌ No API key found!")
        print("\nGet a free key from: https://firecrawl.dev")
        print("\nThen run:")
        print("  export FIRECRAWL_API_KEY='your-key'  # Linux/Mac")
        print("  $env:FIRECRAWL_API_KEY='your-key'    # PowerShell")
        print("\nOr pass as argument:")
        print("  python scrape_unwind_ai.py your-key")
        sys.exit(1)

    try:
        # Scrape articles
        articles = scrape_unwind_articles(api_key)

        if not articles:
            print("⚠️  No articles found")
            sys.exit(1)

        # Save to files
        save_articles(articles)

        # Analyze relevance
        analysis = analyze_articles(articles)

        # Print analysis
        print("\n" + "=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"\nTotal Articles: {analysis['total_articles']}")

        print("\n🎯 Articles by Topic:")
        for topic, count in sorted(analysis['by_topic'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {topic}: {count} articles")

        print(f"\n🔥 High Relevance ({len(analysis['high_relevance'])} articles):")
        for article in analysis['high_relevance']:
            print(f"  • {article['title']}")
            print(f"    Topics: {', '.join(article['topics'])}")
            print(f"    Score: {article['score']}")
            print(f"    URL: {article['url']}\n")

        print(f"\n✅ Complete! Check ./scraped_articles/ for full content")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
