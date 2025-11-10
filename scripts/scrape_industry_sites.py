#!/usr/bin/env python3
"""
Industry Knowledge Scraper for SignX Platform
Scrapes fabrication, sign, and manufacturing industry websites
Monitors for new content and builds knowledge base
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

try:
    import feedparser
    import html2text
except ImportError:
    print("❌ Missing dependencies. Run: pip install feedparser html2text")
    exit(1)


# Curated list of industry websites relevant to sign manufacturing
INDUSTRY_SITES = {
    'fabrication': {
        'The Fabricator': {
            'url': 'https://www.thefabricator.com',
            'rss': 'https://www.thefabricator.com/rss',
            'topics': ['metal fabrication', 'welding', 'cutting', 'bending', 'materials'],
            'relevance': 'high'  # Direct manufacturing techniques
        },
        'Fabricating & Metalworking': {
            'url': 'https://www.fabricatingandmetalworking.com',
            'rss': 'https://www.fabricatingandmetalworking.com/rss',
            'topics': ['metalworking', 'cnc', 'automation'],
            'relevance': 'high'
        },
        'Modern Metals': {
            'url': 'https://modernmetalsmag.com',
            'rss': 'https://modernmetalsmag.com/feed/',
            'topics': ['aluminum', 'steel', 'metal finishing'],
            'relevance': 'medium'
        }
    },
    'signs': {
        'Signs of the Times': {
            'url': 'https://www.signshop.com',
            'rss': 'https://www.signshop.com/rss',
            'topics': ['sign design', 'sign installation', 'sign business'],
            'relevance': 'high'  # Direct sign industry
        },
        'Sign Builder Illustrated': {
            'url': 'https://signbuilder.com',
            'rss': 'https://signbuilder.com/feed/',
            'topics': ['digital printing', 'LED', 'channel letters'],
            'relevance': 'high'
        },
        'SignCraft Magazine': {
            'url': 'https://signcraft.com',
            'rss': 'https://signcraft.com/feed/',
            'topics': ['hand-painted signs', 'design', 'techniques'],
            'relevance': 'medium'
        }
    },
    'construction': {
        'Construction Dive': {
            'url': 'https://www.constructiondive.com',
            'rss': 'https://www.constructiondive.com/feeds/news/',
            'topics': ['building codes', 'regulations', 'construction trends'],
            'relevance': 'medium'  # Building codes affect sign installation
        },
        'Engineering News-Record': {
            'url': 'https://www.enr.com',
            'rss': 'https://www.enr.com/rss/all',
            'topics': ['engineering', 'construction', 'infrastructure'],
            'relevance': 'low'
        }
    },
    'materials': {
        'Aluminum Association': {
            'url': 'https://www.aluminum.org',
            'rss': 'https://www.aluminum.org/rss',
            'topics': ['aluminum', 'alloys', 'specifications'],
            'relevance': 'high'  # Primary sign material
        },
        'Steel Market Update': {
            'url': 'https://www.steelmarketupdate.com',
            'rss': 'https://www.steelmarketupdate.com/feed/',
            'topics': ['steel pricing', 'market trends'],
            'relevance': 'medium'
        }
    },
    'coatings': {
        'CoatingsTech': {
            'url': 'https://www.paint.org',
            'rss': 'https://www.paint.org/coatingstech-magazine/rss/',
            'topics': ['powder coating', 'paint', 'finishes'],
            'relevance': 'high'  # Sign finishing
        }
    },
    'led_lighting': {
        'LEDs Magazine': {
            'url': 'https://www.ledsmagazine.com',
            'rss': 'https://www.ledsmagazine.com/rss',
            'topics': ['LED technology', 'lighting design', 'efficiency'],
            'relevance': 'high'  # LED signs
        }
    },
    'automation': {
        'Automation World': {
            'url': 'https://www.automationworld.com',
            'rss': 'https://www.automationworld.com/rss',
            'topics': ['manufacturing automation', 'robotics', 'AI'],
            'relevance': 'medium'
        }
    }
}


class IndustryKnowledgeScraper:
    """Scrape and monitor industry websites for SignX knowledge base"""

    def __init__(self, output_dir: str = "./industry_knowledge"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0

    def discover_rss_feed(self, base_url: str) -> Optional[str]:
        """Try to discover RSS feed from a website"""
        # Common RSS feed patterns
        patterns = [
            f"{base_url}/rss",
            f"{base_url}/rss.xml",
            f"{base_url}/feed",
            f"{base_url}/feed/",
            f"{base_url}/feeds/news/",
            f"{base_url}/atom.xml",
        ]

        for feed_url in patterns:
            try:
                feed = feedparser.parse(feed_url)
                if feed.entries and not feed.bozo:
                    print(f"  ✅ Found RSS feed: {feed_url}")
                    return feed_url
            except:
                continue

        return None

    def scrape_site(self, site_name: str, site_info: Dict) -> List[Dict]:
        """Scrape a single industry site"""
        print(f"\n📰 Scraping: {site_name}")
        print(f"   URL: {site_info['url']}")
        print(f"   Relevance: {site_info['relevance']}")

        # Try provided RSS feed first
        rss_url = site_info.get('rss')
        if not rss_url:
            # Try to discover
            print(f"   🔍 No RSS provided, attempting discovery...")
            rss_url = self.discover_rss_feed(site_info['url'])

        if not rss_url:
            print(f"   ⚠️  No RSS feed found for {site_name}")
            return []

        # Fetch feed
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            print(f"   ⚠️  Feed parsing error: {feed.bozo_exception}")

        if not feed.entries:
            print(f"   ⚠️  No articles found")
            return []

        print(f"   ✅ Found {len(feed.entries)} articles")

        articles = []
        for entry in feed.entries:
            content_html = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
            content_md = self.html_converter.handle(content_html)

            published = entry.get('published_parsed')
            pub_date = datetime(*published[:6]) if published else None

            articles.append({
                'site': site_name,
                'site_category': site_info.get('category', 'unknown'),
                'title': entry.get('title', 'Untitled'),
                'url': entry.get('link', ''),
                'published': pub_date.isoformat() if pub_date else None,
                'content_markdown': content_md,
                'content_preview': content_md[:300] + '...',
                'topics': site_info.get('topics', []),
                'relevance': site_info['relevance'],
                'word_count': len(content_md.split()),
                'fetched_at': datetime.now().isoformat()
            })

        return articles

    def scrape_all(self, categories: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Scrape all industry sites"""
        if categories:
            sites_to_scrape = {k: v for k, v in INDUSTRY_SITES.items() if k in categories}
        else:
            sites_to_scrape = INDUSTRY_SITES

        all_articles = {}
        total_count = 0

        for category, sites in sites_to_scrape.items():
            print(f"\n{'='*80}")
            print(f"📂 Category: {category.upper()}")
            print(f"{'='*80}")

            category_articles = []

            for site_name, site_info in sites.items():
                site_info_with_cat = {**site_info, 'category': category}
                articles = self.scrape_site(site_name, site_info_with_cat)
                category_articles.extend(articles)
                total_count += len(articles)

            all_articles[category] = category_articles

        print(f"\n{'='*80}")
        print(f"✅ Total articles scraped: {total_count}")
        print(f"{'='*80}")

        return all_articles

    def analyze_for_signx(self, all_articles: Dict[str, List[Dict]]) -> Dict:
        """Analyze scraped content for SignX relevance"""
        # SignX-specific keywords
        keywords = {
            'Manufacturing Techniques': [
                'welding', 'cutting', 'bending', 'forming', 'fabrication',
                'cnc', 'laser', 'plasma', 'waterjet', 'brake press'
            ],
            'Materials & Finishes': [
                'aluminum', 'steel', 'acrylic', 'polycarbonate',
                'powder coating', 'paint', 'vinyl', 'galvanize'
            ],
            'Sign-Specific': [
                'monument sign', 'channel letter', 'led', 'illuminated',
                'pylon', 'cabinet', 'dimensional', 'wayfinding'
            ],
            'Engineering & Codes': [
                'wind load', 'structural', 'foundation', 'permit',
                'building code', 'ibc', 'asce', 'engineering'
            ],
            'Business & Operations': [
                'quoting', 'estimating', 'pricing', 'workflow',
                'automation', 'efficiency', 'margins', 'profit'
            ],
            'Installation': [
                'installation', 'mounting', 'anchor', 'crane',
                'rigging', 'safety', 'site work'
            ]
        }

        analysis = {
            'total_articles': sum(len(arts) for arts in all_articles.values()),
            'by_category': {},
            'by_topic': {},
            'by_site': {},
            'high_value': [],
            'medium_value': [],
            'low_value': []
        }

        # Flatten all articles
        all_flat = []
        for category, articles in all_articles.items():
            all_flat.extend(articles)
            analysis['by_category'][category] = len(articles)

        # Analyze each article
        for article in all_flat:
            content = (article['content_markdown'] + article['title']).lower()

            matched_topics = []
            score = 0

            for topic, kws in keywords.items():
                matches = sum(1 for kw in kws if kw in content)
                if matches > 0:
                    matched_topics.append(f"{topic} ({matches})")
                    score += matches
                    analysis['by_topic'][topic] = analysis['by_topic'].get(topic, 0) + 1

            # Track by site
            site = article['site']
            if site not in analysis['by_site']:
                analysis['by_site'][site] = {'count': 0, 'high_value': 0}
            analysis['by_site'][site]['count'] += 1

            summary = {
                'title': article['title'],
                'url': article['url'],
                'site': article['site'],
                'category': article['site_category'],
                'published': article['published'],
                'word_count': article['word_count'],
                'topics': matched_topics,
                'relevance_score': score,
                'site_relevance': article['relevance']
            }

            if score >= 5 or article['relevance'] == 'high':
                analysis['high_value'].append(summary)
                analysis['by_site'][site]['high_value'] += 1
            elif score >= 2:
                analysis['medium_value'].append(summary)
            else:
                analysis['low_value'].append(summary)

        # Sort by score
        analysis['high_value'].sort(key=lambda x: x['relevance_score'], reverse=True)
        analysis['medium_value'].sort(key=lambda x: x['relevance_score'], reverse=True)

        return analysis

    def save_results(self, all_articles: Dict[str, List[Dict]], analysis: Dict):
        """Save scraped articles and analysis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save all articles by category
        for category, articles in all_articles.items():
            if not articles:
                continue

            category_dir = self.output_dir / category
            category_dir.mkdir(exist_ok=True)

            json_path = category_dir / f"articles_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {category}: {len(articles)} articles")

        # Save analysis
        analysis_path = self.output_dir / f"analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved analysis: {analysis_path}")

        # Save high-value articles as markdown
        high_value_dir = self.output_dir / "high_value"
        high_value_dir.mkdir(exist_ok=True)

        for idx, summary in enumerate(analysis['high_value'][:50], 1):  # Top 50
            # Find full article
            for category, articles in all_articles.items():
                article = next((a for a in articles if a['url'] == summary['url']), None)
                if article:
                    break

            if not article:
                continue

            safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_'))[:60]
            md_path = high_value_dir / f"{idx:03d}_{safe_title}.md"

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {article['title']}\n\n")
                f.write(f"**Site**: {article['site']}\n")
                f.write(f"**Category**: {article['site_category']}\n")
                f.write(f"**Published**: {article['published']}\n")
                f.write(f"**URL**: {article['url']}\n")
                f.write(f"**Relevance Score**: {summary['relevance_score']}\n")
                f.write(f"**Topics**: {', '.join(summary['topics'])}\n\n")
                f.write("---\n\n")
                f.write(article['content_markdown'])

        print(f"💾 Saved {len(analysis['high_value'])} high-value articles")

        self._print_summary(analysis)

    def _print_summary(self, analysis: Dict):
        """Print analysis summary"""
        print(f"\n{'='*80}")
        print("📊 INDUSTRY KNOWLEDGE ANALYSIS")
        print(f"{'='*80}")

        print(f"\n📈 Overview:")
        print(f"  Total Articles: {analysis['total_articles']}")

        print(f"\n📂 By Category:")
        for cat, count in sorted(analysis['by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {cat}: {count} articles")

        print(f"\n📰 By Site:")
        for site, stats in sorted(analysis['by_site'].items(), key=lambda x: x[1]['high_value'], reverse=True):
            print(f"  • {site}: {stats['count']} total ({stats['high_value']} high-value)")

        print(f"\n🎯 By Topic:")
        for topic, count in sorted(analysis['by_topic'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {topic}: {count} articles")

        print(f"\n🔥 TOP HIGH-VALUE ARTICLES ({len(analysis['high_value'])}):\n")
        for idx, article in enumerate(analysis['high_value'][:10], 1):
            print(f"  {idx}. {article['title']}")
            print(f"     Site: {article['site']} | Score: {article['relevance_score']}")
            print(f"     Topics: {', '.join(article['topics'][:3])}")
            print(f"     {article['url']}\n")


def main():
    import sys

    print("="*80)
    print("🏭 Industry Knowledge Scraper for SignX Platform")
    print("="*80)
    print()

    # Parse arguments
    categories = sys.argv[1:] if len(sys.argv) > 1 else None

    if categories:
        print(f"📂 Scraping categories: {', '.join(categories)}")
        invalid = [c for c in categories if c not in INDUSTRY_SITES]
        if invalid:
            print(f"\n❌ Invalid categories: {', '.join(invalid)}")
            print(f"\nAvailable: {', '.join(INDUSTRY_SITES.keys())}")
            sys.exit(1)
    else:
        print("📂 Scraping all categories")

    print(f"\nAvailable sites: {sum(len(sites) for sites in INDUSTRY_SITES.values())}")
    print()

    try:
        scraper = IndustryKnowledgeScraper()

        # Scrape all sites
        all_articles = scraper.scrape_all(categories)

        if not any(all_articles.values()):
            print("\n❌ No articles found")
            sys.exit(1)

        # Analyze
        analysis = scraper.analyze_for_signx(all_articles)

        # Save
        scraper.save_results(all_articles, analysis)

        print(f"\n{'='*80}")
        print("✅ COMPLETE! Check ./industry_knowledge/ for results")
        print(f"{'='*80}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
