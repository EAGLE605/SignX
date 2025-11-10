#!/usr/bin/env python3
"""
Enhanced Substack scraper for The Unwind AI and other newsletters
Handles both custom domains and standard substack.com URLs
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("❌ Firecrawl not installed. Run: pip install firecrawl-py")
    exit(1)


class SubstackScraper:
    """Scraper for Substack newsletters"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY required. Get from https://firecrawl.dev")
        self.app = FirecrawlApp(api_key=self.api_key)

    def scrape_archive(self, base_url: str, max_articles: int = 20) -> List[Dict]:
        """
        Scrape Substack archive page

        Args:
            base_url: Base URL (e.g., https://theunwindai.com or https://theunwindai.substack.com)
            max_articles: Maximum number of articles to scrape

        Returns:
            List of article dictionaries
        """
        # Normalize URL
        base_url = base_url.rstrip('/')

        # Try common Substack archive patterns
        archive_urls = [
            f"{base_url}/archive",
            f"{base_url}/archive?sort=new",
            f"{base_url}/p",  # Sometimes posts are listed at /p
        ]

        articles = []
        article_urls = []

        for archive_url in archive_urls:
            try:
                print(f"🔍 Trying archive: {archive_url}")

                result = self.app.scrape_url(
                    archive_url,
                    params={
                        'formats': ['markdown', 'links'],
                        'onlyMainContent': True,
                        'waitFor': 3000
                    }
                )

                links = result.get('links', [])
                print(f"   Found {len(links)} links")

                # Filter for article links
                # Substack articles are typically at /p/article-slug
                new_articles = [
                    link for link in links
                    if '/p/' in link and link not in article_urls
                ]

                article_urls.extend(new_articles)
                print(f"   Found {len(new_articles)} article links")

                if new_articles:
                    break  # Found articles, no need to try other URLs

            except Exception as e:
                print(f"   ⚠️  Failed: {e}")
                continue

        if not article_urls:
            print("❌ No articles found. The site might not be a Substack or uses different URL patterns.")
            return []

        # Limit to max_articles
        article_urls = article_urls[:max_articles]
        print(f"\n📰 Scraping {len(article_urls)} articles...\n")

        # Scrape each article
        for idx, url in enumerate(article_urls, 1):
            try:
                print(f"[{idx}/{len(article_urls)}] {url}")

                article_result = self.app.scrape_url(
                    url,
                    params={
                        'formats': ['markdown', 'html'],
                        'onlyMainContent': True
                    }
                )

                markdown = article_result.get('markdown', '')

                # Parse Substack metadata
                lines = markdown.split('\n')
                title = lines[0].replace('#', '').strip() if lines else 'Untitled'

                # Extract publication date (Substack usually has it near the top)
                pub_date = None
                for line in lines[:10]:
                    if any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                                                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                        pub_date = line.strip()
                        break

                articles.append({
                    'title': title,
                    'url': url,
                    'publication_date': pub_date,
                    'content_preview': markdown[:500] + '...',
                    'full_content': markdown,
                    'word_count': len(markdown.split()),
                    'scraped_at': datetime.now().isoformat()
                })

                print(f"   ✅ {title[:60]}...")

            except Exception as e:
                print(f"   ❌ Failed: {e}")
                continue

        return articles

    def analyze_for_signx(self, articles: List[Dict]) -> Dict:
        """Analyze articles for SignX Platform relevance"""

        keywords = {
            'RAG & Vector Search': ['rag', 'retrieval', 'vector', 'embedding', 'semantic search', 'pinecone', 'chroma'],
            'AI Agents': ['agent', 'autonomous', 'multi-agent', 'langgraph', 'crewai', 'autogen'],
            'Document Processing': ['document', 'pdf', 'ocr', 'parsing', 'extraction', 'unstructured'],
            'LLM Integration': ['llm', 'gpt', 'claude', 'gemini', 'anthropic', 'openai'],
            'Business Automation': ['automation', 'workflow', 'pipeline', 'orchestration'],
            'Web Scraping': ['scraping', 'crawling', 'firecrawl', 'beautifulsoup', 'selenium'],
            'Cost Optimization': ['cost', 'pricing', 'optimization', 'efficiency', 'tokens'],
            'Prompt Engineering': ['prompt', 'prompting', 'few-shot', 'chain-of-thought'],
            'Fine-tuning & Training': ['fine-tuning', 'training', 'dataset', 'model training'],
        }

        analysis = {
            'total_articles': len(articles),
            'total_words': sum(a['word_count'] for a in articles),
            'by_topic': {},
            'high_value': [],     # 5+ keyword matches
            'medium_value': [],   # 2-4 matches
            'low_value': []       # 0-1 matches
        }

        for article in articles:
            content = (article['full_content'] + article['title']).lower()

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
                'date': article['publication_date'],
                'word_count': article['word_count'],
                'topics': matched_topics,
                'relevance_score': score
            }

            if score >= 5:
                analysis['high_value'].append(summary)
            elif score >= 2:
                analysis['medium_value'].append(summary)
            else:
                analysis['low_value'].append(summary)

        # Sort by score
        analysis['high_value'].sort(key=lambda x: x['relevance_score'], reverse=True)
        analysis['medium_value'].sort(key=lambda x: x['relevance_score'], reverse=True)

        return analysis

    def save_results(self, articles: List[Dict], analysis: Dict, output_dir: str = "./scraped_substack"):
        """Save scraped articles and analysis"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save all articles as JSON
        json_path = f"{output_dir}/articles_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved JSON: {json_path}")

        # Save analysis
        analysis_path = f"{output_dir}/analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved analysis: {analysis_path}")

        # Save individual markdown files (high-value articles only)
        high_value_dir = f"{output_dir}/high_value"
        os.makedirs(high_value_dir, exist_ok=True)

        for idx, summary in enumerate(analysis['high_value'], 1):
            # Find full article
            article = next(a for a in articles if a['url'] == summary['url'])

            safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
            md_path = f"{high_value_dir}/{idx:02d}_{safe_title}.md"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {article['title']}\n\n")
                f.write(f"**URL**: {article['url']}\n")
                f.write(f"**Date**: {article['publication_date']}\n")
                f.write(f"**Relevance Score**: {summary['relevance_score']}\n")
                f.write(f"**Topics**: {', '.join(summary['topics'])}\n\n")
                f.write("---\n\n")
                f.write(article['full_content'])

            print(f"  📝 {md_path}")

        print(f"\n✅ Saved {len(analysis['high_value'])} high-value articles to {high_value_dir}/")

        # Print summary
        print("\n" + "=" * 70)
        print("📊 SCRAPING SUMMARY")
        print("=" * 70)
        print(f"\nTotal Articles: {analysis['total_articles']}")
        print(f"Total Words: {analysis['total_words']:,}")

        print(f"\n🎯 Topics Found:")
        for topic, count in sorted(analysis['by_topic'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {topic}: {count} articles")

        print(f"\n🔥 High Value ({len(analysis['high_value'])} articles):")
        for article in analysis['high_value'][:5]:  # Top 5
            print(f"\n  📌 {article['title']}")
            print(f"     Score: {article['relevance_score']} | Words: {article['word_count']:,}")
            print(f"     Topics: {', '.join(article['topics'][:3])}...")  # Top 3 topics
            print(f"     {article['url']}")

        if len(analysis['high_value']) > 5:
            print(f"\n  ... and {len(analysis['high_value']) - 5} more high-value articles")


if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("📰 Substack Newsletter Scraper for SignX Platform")
    print("=" * 70)

    # Get API key
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if len(sys.argv) > 2:
        api_key = sys.argv[2]

    if not api_key:
        print("\n❌ No Firecrawl API key found!")
        print("\nGet free key: https://firecrawl.dev")
        print("\nUsage:")
        print("  python scrape_substack.py <substack-url> [api-key]")
        print("\nExamples:")
        print("  python scrape_substack.py https://theunwindai.com")
        print("  python scrape_substack.py https://theunwindai.substack.com")
        sys.exit(1)

    # Get URL
    if len(sys.argv) < 2:
        print("\n❌ No URL provided!")
        print("\nUsage:")
        print("  python scrape_substack.py <substack-url>")
        print("\nExamples:")
        print("  python scrape_substack.py https://theunwindai.com")
        print("  python scrape_substack.py https://theunwindai.substack.com")
        sys.exit(1)

    base_url = sys.argv[1]

    try:
        scraper = SubstackScraper(api_key)

        # Scrape articles
        articles = scraper.scrape_archive(base_url, max_articles=20)

        if not articles:
            print("\n❌ No articles found. Check the URL or try:")
            print(f"  • {base_url}/archive")
            print(f"  • {base_url.replace('.com', '.substack.com')}")
            sys.exit(1)

        # Analyze
        analysis = scraper.analyze_for_signx(articles)

        # Save
        scraper.save_results(articles, analysis)

        print("\n✅ Complete! Check ./scraped_substack/ for results")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
