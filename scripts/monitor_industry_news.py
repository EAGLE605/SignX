#!/usr/bin/env python3
"""
Industry News Monitor for SignX Platform
Checks industry sites for new articles and sends notifications
Can be run as a cron job or scheduled task
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set
import hashlib

try:
    import feedparser
    import html2text
except ImportError:
    print("❌ Missing dependencies. Run: pip install feedparser html2text")
    exit(1)

# Import site list from main scraper
import sys
sys.path.insert(0, str(Path(__file__).parent))
from scrape_industry_sites import INDUSTRY_SITES


class IndustryNewsMonitor:
    """Monitor industry sites for new content"""

    def __init__(self, state_dir: str = "./industry_monitor_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "seen_articles.json"
        self.seen_articles = self._load_state()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0

    def _load_state(self) -> Dict[str, Set[str]]:
        """Load previously seen article URLs"""
        if not self.state_file.exists():
            return {}

        with open(self.state_file, 'r') as f:
            data = json.load(f)
            # Convert lists back to sets
            return {k: set(v) for k, v in data.items()}

    def _save_state(self):
        """Save seen article URLs"""
        # Convert sets to lists for JSON
        data = {k: list(v) for k, v in self.seen_articles.items()}
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _article_hash(self, url: str, title: str) -> str:
        """Generate unique hash for article"""
        content = f"{url}|{title}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def check_site(self, site_name: str, site_info: Dict) -> List[Dict]:
        """Check a site for new articles"""
        rss_url = site_info.get('rss')
        if not rss_url:
            return []

        feed = feedparser.parse(rss_url)

        if not feed.entries:
            return []

        # Get or create site's seen set
        if site_name not in self.seen_articles:
            self.seen_articles[site_name] = set()

        new_articles = []
        cutoff_date = datetime.now() - timedelta(days=7)  # Only articles from last week

        for entry in feed.entries:
            url = entry.get('link', '')
            title = entry.get('title', 'Untitled')
            article_hash = self._article_hash(url, title)

            # Skip if seen before
            if article_hash in self.seen_articles[site_name]:
                continue

            # Check if recent
            published = entry.get('published_parsed')
            if published:
                pub_date = datetime(*published[:6])
                if pub_date < cutoff_date:
                    continue  # Too old
            else:
                pub_date = None

            # New article!
            content_html = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
            content_md = self.html_converter.handle(content_html)

            new_articles.append({
                'hash': article_hash,
                'site': site_name,
                'site_url': site_info['url'],
                'title': title,
                'url': url,
                'published': pub_date.isoformat() if pub_date else None,
                'content_preview': content_md[:500] + '...',
                'content_full': content_md,
                'topics': site_info.get('topics', []),
                'relevance': site_info['relevance'],
                'discovered_at': datetime.now().isoformat()
            })

            # Mark as seen
            self.seen_articles[site_name].add(article_hash)

        return new_articles

    def check_all(self, high_priority_only: bool = False) -> Dict[str, List[Dict]]:
        """Check all sites for new articles"""
        all_new = {}
        total_count = 0

        for category, sites in INDUSTRY_SITES.items():
            category_new = []

            for site_name, site_info in sites.items():
                # Skip low-relevance sites if high-priority mode
                if high_priority_only and site_info['relevance'] != 'high':
                    continue

                new_articles = self.check_site(site_name, site_info)
                if new_articles:
                    print(f"🆕 {site_name}: {len(new_articles)} new articles")
                    category_new.extend(new_articles)
                    total_count += len(new_articles)

            if category_new:
                all_new[category] = category_new

        # Save state
        self._save_state()

        print(f"\n✅ Found {total_count} new articles across {len(all_new)} categories")
        return all_new

    def generate_report(self, new_articles: Dict[str, List[Dict]], output_file: str = None) -> str:
        """Generate a report of new articles"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d')
            output_file = self.state_dir / f"new_articles_{timestamp}.md"

        total = sum(len(arts) for arts in new_articles.values())

        report = f"# Industry News Update - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"**New Articles**: {total}\n\n"
        report += "---\n\n"

        for category, articles in new_articles.items():
            report += f"## {category.upper()} ({len(articles)} articles)\n\n"

            # Group by site
            by_site = {}
            for article in articles:
                site = article['site']
                if site not in by_site:
                    by_site[site] = []
                by_site[site].append(article)

            for site, site_articles in by_site.items():
                report += f"### {site}\n\n"

                for article in site_articles:
                    report += f"**{article['title']}**\n"
                    report += f"- Published: {article['published'] or 'Unknown'}\n"
                    report += f"- URL: {article['url']}\n"
                    report += f"- Relevance: {article['relevance']}\n"
                    report += f"- Topics: {', '.join(article['topics'])}\n"
                    report += f"\n{article['content_preview']}\n\n"
                    report += "---\n\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📝 Report saved: {output_file}")
        return str(output_file)

    def send_notification(self, new_articles: Dict[str, List[Dict]]):
        """Send notification about new articles (placeholder for future email/Slack)"""
        total = sum(len(arts) for arts in new_articles.values())

        if total == 0:
            print("📭 No new articles to notify about")
            return

        print(f"\n{'='*80}")
        print(f"📬 NEW ARTICLE NOTIFICATION")
        print(f"{'='*80}\n")

        print(f"Found {total} new articles:\n")

        for category, articles in new_articles.items():
            high_value = [a for a in articles if a['relevance'] == 'high']
            if high_value:
                print(f"🔥 {category}: {len(high_value)} high-value articles")
                for article in high_value[:3]:  # Top 3
                    print(f"   • {article['title']}")
                    print(f"     {article['url']}")

        print(f"\n💡 TIP: Run with --report to generate full markdown report")
        print(f"{'='*80}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor industry sites for new articles")
    parser.add_argument('--high-priority', action='store_true',
                        help='Only check high-relevance sites')
    parser.add_argument('--report', action='store_true',
                        help='Generate markdown report')
    parser.add_argument('--silent', action='store_true',
                        help='Silent mode (no output except errors)')
    args = parser.parse_args()

    print("="*80)
    print("📡 Industry News Monitor for SignX Platform")
    print("="*80)
    print()

    try:
        monitor = IndustryNewsMonitor()

        # Check for new articles
        new_articles = monitor.check_all(high_priority_only=args.high_priority)

        if not new_articles:
            if not args.silent:
                print("✅ No new articles found")
            return

        # Generate report if requested
        if args.report:
            monitor.generate_report(new_articles)

        # Send notification (console for now)
        if not args.silent:
            monitor.send_notification(new_articles)

        print("\n✅ Monitoring complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
