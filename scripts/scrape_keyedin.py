#!/usr/bin/env python3
"""
KeyedIn Sign CRM Scraper
Authenticates and extracts work orders from legacy CGI system
https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN.START
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing dependencies. Run: pip install requests beautifulsoup4 lxml")
    exit(1)


class KeyedInScraper:
    """Scrape work orders from KeyedIn legacy CGI system"""

    def __init__(self, username: str = None, password: str = None):
        self.base_url = "https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe"
        self.username = username or os.getenv("KEYEDIN_USERNAME")
        self.password = password or os.getenv("KEYEDIN_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("KEYEDIN_USERNAME and KEYEDIN_PASSWORD required")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        self.logged_in = False

    def login(self) -> bool:
        """Authenticate with KeyedIn system"""

        print(f"🔐 Logging into KeyedIn as {self.username}...")

        try:
            # Step 1: Get login page to check for CSRF tokens or session cookies
            login_url = f"{self.base_url}/LOGIN.START"
            response = self.session.get(login_url)

            if response.status_code != 200:
                print(f"❌ Failed to load login page: {response.status_code}")
                return False

            # Parse login form to find field names
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')

            if not form:
                print("❌ No login form found on page")
                return False

            # Find input field names (they might not be standard)
            username_field = None
            password_field = None

            for input_tag in soup.find_all('input'):
                input_type = input_tag.get('type', '').lower()
                input_name = input_tag.get('name', '')

                # Common username field patterns
                if input_type == 'text' or 'user' in input_name.lower() or 'login' in input_name.lower():
                    username_field = input_name

                # Common password field patterns
                if input_type == 'password' or 'pass' in input_name.lower():
                    password_field = input_name

            print(f"  Found username field: {username_field}")
            print(f"  Found password field: {password_field}")

            # Step 2: Submit login
            # CGI systems often POST to the same URL or a specific action
            login_action = form.get('action', '/LOGIN')

            # Build full login URL
            if login_action.startswith('http'):
                post_url = login_action
            elif login_action.startswith('/'):
                post_url = f"https://eaglesign.keyedinsign.com{login_action}"
            else:
                post_url = f"{self.base_url}/{login_action}"

            # Prepare login payload
            payload = {
                username_field or 'username': self.username,
                password_field or 'password': self.password
            }

            # Add any hidden fields from the form
            for hidden in soup.find_all('input', type='hidden'):
                if hidden.get('name'):
                    payload[hidden['name']] = hidden.get('value', '')

            print(f"  Posting to: {post_url}")

            response = self.session.post(post_url, data=payload, allow_redirects=True)

            # Check if login was successful
            # Common indicators: redirect to dashboard, presence of logout link, absence of login form
            if 'logout' in response.text.lower() or 'sign out' in response.text.lower():
                print("✅ Login successful!")
                self.logged_in = True
                return True
            elif 'invalid' in response.text.lower() or 'incorrect' in response.text.lower():
                print("❌ Login failed: Invalid credentials")
                return False
            else:
                # Ambiguous - save response for debugging
                with open('/tmp/keyedin_login_response.html', 'w') as f:
                    f.write(response.text)
                print("⚠️  Login status unclear. Response saved to /tmp/keyedin_login_response.html")

                # Ask user to verify
                print("\nDoes the page contain a logout link or dashboard? (y/n): ", end='')
                # For automated use, assume success if no error message
                self.logged_in = 'error' not in response.text.lower()
                return self.logged_in

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def discover_navigation(self) -> Dict:
        """Discover available pages/sections after login"""

        if not self.logged_in:
            if not self.login():
                return {}

        print("\n🔍 Discovering site navigation...")

        try:
            # Get main page after login
            response = self.session.get(f"{self.base_url}/MAIN")
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links
            links = {}
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)

                # Look for work order related links
                if any(keyword in text.lower() for keyword in ['work', 'order', 'service', 'job', 'project', 'invoice']):
                    links[text] = href

            print(f"  Found {len(links)} relevant links:")
            for text, href in links.items():
                print(f"    • {text}: {href}")

            return links

        except Exception as e:
            print(f"❌ Navigation discovery error: {e}")
            return {}

    def find_work_order_list(self) -> Optional[str]:
        """Try to find the work order list page URL"""

        # Common URL patterns for work orders in legacy systems
        possible_urls = [
            f"{self.base_url}/WORKORDER.LIST",
            f"{self.base_url}/WORK_ORDER.LIST",
            f"{self.base_url}/SERVICE.ORDER.LIST",
            f"{self.base_url}/ORDERS.LIST",
            f"{self.base_url}/JOBS.LIST",
            f"{self.base_url}/PROJECTS.LIST",
        ]

        print("\n🔍 Searching for work order list page...")

        for url in possible_urls:
            try:
                print(f"  Trying: {url}")
                response = self.session.get(url)

                if response.status_code == 200:
                    # Check if page looks like a work order list
                    if any(keyword in response.text.lower() for keyword in ['work order', 'service order', 'job number']):
                        print(f"  ✅ Found work order list: {url}")
                        return url
            except:
                continue

        print("  ⚠️  Could not auto-discover work order list page")
        return None

    def scrape_work_order(self, order_id: str) -> Optional[Dict]:
        """Scrape a single work order by ID"""

        if not self.logged_in:
            if not self.login():
                return None

        print(f"\n📋 Scraping work order: {order_id}")

        try:
            # Try common URL patterns
            possible_urls = [
                f"{self.base_url}/WORKORDER.VIEW?id={order_id}",
                f"{self.base_url}/ORDER.VIEW?orderid={order_id}",
                f"{self.base_url}/JOB.DETAIL?jobno={order_id}",
            ]

            for url in possible_urls:
                response = self.session.get(url)

                if response.status_code == 200 and len(response.text) > 500:
                    # Found the page, now extract data
                    return self._parse_work_order_page(response.text, order_id)

            print(f"  ❌ Could not find work order {order_id}")
            return None

        except Exception as e:
            print(f"  ❌ Error scraping work order: {e}")
            return None

    def _parse_work_order_page(self, html: str, order_id: str) -> Dict:
        """Parse work order HTML page and extract cost data"""

        soup = BeautifulSoup(html, 'html.parser')

        # Save raw HTML for debugging
        debug_file = f"/tmp/keyedin_workorder_{order_id}.html"
        with open(debug_file, 'w') as f:
            f.write(html)

        print(f"  💾 Saved raw HTML to {debug_file}")

        # Extract data - this is highly dependent on KeyedIn's HTML structure
        # We'll use common patterns but may need to adjust

        data = {
            'order_id': order_id,
            'scraped_at': datetime.now().isoformat(),
            'raw_html_path': debug_file
        }

        # Try to extract key fields by common labels
        text = soup.get_text()

        # Common patterns
        patterns = {
            'customer': r'customer[:\s]+([^\n]+)',
            'project': r'project[:\s]+([^\n]+)',
            'total': r'total[:\s]+\$?([\d,\.]+)',
            'materials': r'materials?[:\s]+\$?([\d,\.]+)',
            'labor': r'labor[:\s]+\$?([\d,\.]+)',
            'date': r'date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[field] = match.group(1).strip()

        # Try to find tables with line items
        tables = soup.find_all('table')
        if tables:
            data['tables_found'] = len(tables)
            # Extract first table as sample
            data['first_table_html'] = str(tables[0])

        return data

    def export_sample_pages(self, num_orders: int = 5):
        """Export sample work order pages for analysis"""

        if not self.logged_in:
            if not self.login():
                return

        output_dir = Path("./keyedin_samples")
        output_dir.mkdir(exist_ok=True)

        print(f"\n📦 Exporting {num_orders} sample work orders to {output_dir}/")

        # You'll need to provide actual order IDs
        # For now, save the navigation page
        try:
            response = self.session.get(f"{self.base_url}/MAIN")

            with open(output_dir / "main_page.html", 'w') as f:
                f.write(response.text)

            print(f"  ✅ Saved main page")

            # Save a few more pages for discovery
            pages_to_try = ['WORKORDER.LIST', 'REPORTS', 'SEARCH']

            for page in pages_to_try:
                try:
                    resp = self.session.get(f"{self.base_url}/{page}")
                    if resp.status_code == 200:
                        with open(output_dir / f"{page.lower()}.html", 'w') as f:
                            f.write(resp.text)
                        print(f"  ✅ Saved {page}")
                except:
                    pass

        except Exception as e:
            print(f"  ❌ Export error: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KeyedIn Sign CRM Scraper")
    parser.add_argument('--username', help='KeyedIn username')
    parser.add_argument('--password', help='KeyedIn password')
    parser.add_argument('--discover', action='store_true', help='Discover site navigation')
    parser.add_argument('--export-samples', action='store_true', help='Export sample pages for analysis')
    parser.add_argument('--order-id', help='Scrape specific work order')
    args = parser.parse_args()

    print("="*80)
    print("🔧 KeyedIn Sign CRM Scraper")
    print("="*80)
    print()

    try:
        scraper = KeyedInScraper(
            username=args.username,
            password=args.password
        )

        # Login
        if not scraper.login():
            print("\n❌ Login failed. Cannot proceed.")
            return

        # Discovery mode
        if args.discover:
            scraper.discover_navigation()
            scraper.find_work_order_list()

        # Export samples
        if args.export_samples:
            scraper.export_sample_pages()

        # Scrape specific order
        if args.order_id:
            data = scraper.scrape_work_order(args.order_id)
            if data:
                print("\n📊 Extracted data:")
                print(json.dumps(data, indent=2))

        # If no action specified, just show what's possible
        if not (args.discover or args.export_samples or args.order_id):
            print("\n💡 What would you like to do?")
            print("  --discover          Discover navigation and find work order pages")
            print("  --export-samples    Export sample pages for analysis")
            print("  --order-id <id>     Scrape a specific work order")
            print("\nExample:")
            print("  python scrape_keyedin.py --discover")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
