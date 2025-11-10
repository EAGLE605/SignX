#!/usr/bin/env python3
"""
Scrape Substack newsletters via RSS feed - NO API KEY NEEDED!
Free, fast, and works with any Substack publication
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict
try:
    import feedparser
except ImportError:
    print("❌ feedparser not installed. Run: pip install feedparser")
    exit(1)

try:
    import html2text
except ImportError:
    print("❌ html2text not installed. Run: pip install html2text")
    exit(1)


class SubstackRSSFetcher:
    """Fetch Substack articles via RSS - completely free!"""

    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0  # No wrapping

    def fetch_feed(self, feed_url: str) -> List[Dict]:
        """
        Fetch articles from Substack RSS feed

        Args:
            feed_url: RSS feed URL (e.g., https://theunwindai.substack.com/feed)

        Returns:
            List of article dictionaries
        """
        # Normalize URL
        if not feed_url.endswith('/feed'):
            feed_url = feed_url.rstrip('/') + '/feed'

        print(f"📡 Fetching RSS feed: {feed_url}")

        feed = feedparser.parse(feed_url)

        if feed.bozo:
            print(f"⚠️  Warning: Feed may have errors ({feed.bozo_exception})")

        if not feed.entries:
            print("❌ No entries found in feed")
            return []

        print(f"✅ Found {len(feed.entries)} articles\n")

        articles = []
        for entry in feed.entries:
            # Convert HTML to markdown
            content_html = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
            content_md = self.html_converter.handle(content_html)

            # Clean up title
            title = entry.get('title', 'Untitled')

            # Parse date
            published = entry.get('published_parsed')
            pub_date = datetime(*published[:6]).isoformat() if published else None

            # Extract author
            author = entry.get('author', 'Unknown')

            # Get link
            link = entry.get('link', '')

            # Word count
            word_count = len(content_md.split())

            articles.append({
                'title': title,
                'url': link,
                'author': author,
                'published': pub_date,
                'content_markdown': content_md,
                'content_preview': content_md[:500] + '...' if len(content_md) > 500 else content_md,
                'word_count': word_count,
                'fetched_at': datetime.now().isoformat()
            })

            print(f"  ✅ {title[:70]}{'...' if len(title) > 70 else ''}")
            print(f"     {pub_date} | {word_count:,} words")

        return articles

    def analyze_for_signx(self, articles: List[Dict]) -> Dict:
        """Analyze articles for SignX Platform relevance"""

        keywords = {
            'RAG & Vector Search': [
                'rag', 'retrieval augmented generation', 'vector', 'embedding', 'semantic search',
                'pinecone', 'chroma', 'weaviate', 'faiss', 'pgvector'
            ],
            'AI Agents & Workflows': [
                'agent', 'autonomous', 'multi-agent', 'langgraph', 'crewai', 'autogen',
                'agentic', 'workflow', 'orchestration', 'langchain'
            ],
            'Document Processing': [
                'document', 'pdf', 'ocr', 'parsing', 'extraction', 'unstructured',
                'document intelligence', 'text extraction', 'pypdf', 'pdfplumber'
            ],
            'LLM APIs & Integration': [
                'llm', 'gpt', 'claude', 'gemini', 'anthropic', 'openai', 'api',
                'langchain', 'llamaindex', 'model context', 'context window'
            ],
            'Business Automation': [
                'automation', 'workflow', 'pipeline', 'production', 'deployment',
                'scaling', 'enterprise', 'business process'
            ],
            'Web Scraping & Data Collection': [
                'scraping', 'crawling', 'firecrawl', 'beautifulsoup', 'selenium',
                'playwright', 'web data', 'data collection'
            ],
            'Cost & Performance Optimization': [
                'cost', 'pricing', 'optimization', 'efficiency', 'tokens', 'latency',
                'performance', 'caching', 'batch processing'
            ],
            'Prompt Engineering': [
                'prompt', 'prompting', 'few-shot', 'chain-of-thought', 'system prompt',
                'prompt template', 'prompt engineering', 'instruction following'
            ],
            'Training & Fine-tuning': [
                'fine-tuning', 'training', 'dataset', 'model training', 'distillation',
                'lora', 'qlora', 'supervised fine-tuning'
            ],
            'Engineering & Technical': [
                'engineering', 'structural', 'calculation', 'design', 'compliance',
                'code', 'standard', 'specification'
            ]
        }

        analysis = {
            'total_articles': len(articles),
            'total_words': sum(a['word_count'] for a in articles),
            'avg_words': int(sum(a['word_count'] for a in articles) / len(articles)) if articles else 0,
            'by_topic': {},
            'high_value': [],     # 6+ keyword matches
            'medium_value': [],   # 3-5 matches
            'low_value': []       # 0-2 matches
        }

        for article in articles:
            content = (article['content_markdown'] + article['title']).lower()

            matched_topics = []
            score = 0

            for topic, kws in keywords.items():
                matches = sum(1 for kw in kws if kw in content)
                if matches > 0:
                    matched_topics.append(f"{topic} ({matches})")
                    score += matches
                    analysis['by_topic'][topic] = analysis['by_topic'].get(topic, 0) + 1

            summary = {
                'title': article['title'],
                'url': article['url'],
                'published': article['published'],
                'author': article['author'],
                'word_count': article['word_count'],
                'topics': matched_topics,
                'relevance_score': score
            }

            if score >= 6:
                analysis['high_value'].append(summary)
            elif score >= 3:
                analysis['medium_value'].append(summary)
            else:
                analysis['low_value'].append(summary)

        # Sort by score
        analysis['high_value'].sort(key=lambda x: x['relevance_score'], reverse=True)
        analysis['medium_value'].sort(key=lambda x: x['relevance_score'], reverse=True)

        return analysis

    def save_results(self, articles: List[Dict], analysis: Dict, output_dir: str = "./substack_articles"):
        """Save articles and analysis"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save all articles as JSON
        json_path = f"{output_dir}/articles_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved all articles: {json_path}")

        # Save analysis
        analysis_path = f"{output_dir}/analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved analysis: {analysis_path}")

        # Save high-value articles as markdown
        if analysis['high_value']:
            high_dir = f"{output_dir}/high_value"
            os.makedirs(high_dir, exist_ok=True)

            for idx, summary in enumerate(analysis['high_value'], 1):
                article = next(a for a in articles if a['url'] == summary['url'])

                safe_title = re.sub(r'[^\w\s-]', '', article['title'])[:60]
                safe_title = re.sub(r'[-\s]+', '_', safe_title)

                md_path = f"{high_dir}/{idx:02d}_{safe_title}.md"

                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {article['title']}\n\n")
                    f.write(f"**Author**: {article['author']}\n")
                    f.write(f"**Published**: {article['published']}\n")
                    f.write(f"**URL**: {article['url']}\n")
                    f.write(f"**Relevance Score**: {summary['relevance_score']}\n")
                    f.write(f"**Topics**: {', '.join(summary['topics'])}\n")
                    f.write(f"**Words**: {article['word_count']:,}\n\n")
                    f.write("---\n\n")
                    f.write(article['content_markdown'])

                print(f"  📝 {idx:02d}. {article['title'][:60]}")

            print(f"\n✅ Saved {len(analysis['high_value'])} high-value articles to {high_dir}/")

        # Print summary
        self._print_summary(analysis)

    def _print_summary(self, analysis: Dict):
        """Print analysis summary"""
        print("\n" + "=" * 80)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 80)

        print(f"\n📈 Statistics:")
        print(f"  • Total Articles: {analysis['total_articles']}")
        print(f"  • Total Words: {analysis['total_words']:,}")
        print(f"  • Average Words/Article: {analysis['avg_words']:,}")

        print(f"\n🎯 Articles by Topic:")
        for topic, count in sorted(analysis['by_topic'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {topic}: {count}")

        print(f"\n🔥 HIGH VALUE ARTICLES ({len(analysis['high_value'])}):")
        if analysis['high_value']:
            for idx, article in enumerate(analysis['high_value'][:10], 1):  # Top 10
                print(f"\n  {idx}. {article['title']}")
                print(f"     Score: {article['relevance_score']} | Words: {article['word_count']:,}")
                print(f"     Published: {article['published']}")
                print(f"     Topics: {', '.join(article['topics'][:4])}...")
                print(f"     {article['url']}")

            if len(analysis['high_value']) > 10:
                print(f"\n     ... and {len(analysis['high_value']) - 10} more")
        else:
            print("  (None found)")

        print(f"\n⚡ MEDIUM VALUE ARTICLES ({len(analysis['medium_value'])}):")
        if analysis['medium_value']:
            for idx, article in enumerate(analysis['medium_value'][:5], 1):  # Top 5
                print(f"  {idx}. {article['title']} (Score: {article['relevance_score']})")
        else:
            print("  (None found)")

        print(f"\n📄 Low value: {len(analysis['low_value'])} articles")


def main():
    import sys

    print("=" * 80)
    print("📰 Substack RSS Fetcher - FREE & NO API KEY REQUIRED!")
    print("=" * 80)
    print()

    if len(sys.argv) < 2:
        print("❌ No Substack URL provided\n")
        print("Usage:")
        print("  python scrape_substack_rss.py <substack-url>\n")
        print("Examples:")
        print("  python scrape_substack_rss.py https://theunwindai.com")
        print("  python scrape_substack_rss.py https://theunwindai.substack.com")
        print("  python scrape_substack_rss.py https://newsletter.substack.com/feed")
        sys.exit(1)

    url = sys.argv[1]

    try:
        fetcher = SubstackRSSFetcher()

        # Fetch articles
        articles = fetcher.fetch_feed(url)

        if not articles:
            print("\n❌ No articles found. Check the URL and try:")
            print(f"  • {url}/feed")
            print(f"  • {url.replace('.com', '.substack.com')}/feed")
            sys.exit(1)

        # Analyze
        analysis = fetcher.analyze_for_signx(articles)

        # Save
        fetcher.save_results(articles, analysis)

        print("\n" + "=" * 80)
        print("✅ COMPLETE! Check ./substack_articles/ for full content")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
