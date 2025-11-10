#!/usr/bin/env python3
"""
KeyedIn Informer Portal Scraper
Modern interface for reporting/analytics (separate from CGI system)
https://eaglesign.keyedinsign.com:8443/eaglesign/Informer.html
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("❌ Selenium not installed. Run: pip install selenium")
    print("   Also need Chrome/Chromium browser installed")
    exit(1)


class KeyedInInformerScraper:
    """
    Scrape work orders from KeyedIn Informer portal
    Uses Selenium because Informer is likely a JavaScript-heavy SPA
    """

    def __init__(self, username: str = None, password: str = None, headless: bool = True):
        self.base_url = "https://eaglesign.keyedinsign.com:8443/eaglesign"
        self.username = username or os.getenv("KEYEDIN_USERNAME")
        self.password = password or os.getenv("KEYEDIN_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("KEYEDIN_USERNAME and KEYEDIN_PASSWORD required")

        # Setup Chrome with options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        print(f"🌐 Starting Chrome browser (headless={headless})...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        self.logged_in = False

    def login(self) -> bool:
        """Authenticate with KeyedIn Informer portal"""

        print(f"🔐 Logging into KeyedIn Informer as {self.username}...")

        try:
            # Navigate to Informer portal
            login_url = f"{self.base_url}/Informer.html?locale=en_US#action=Home"
            self.driver.get(login_url)

            # Wait for page to load
            time.sleep(3)

            # Take screenshot for debugging
            self.driver.save_screenshot("/tmp/keyedin_informer_login.png")
            print("  📸 Screenshot saved: /tmp/keyedin_informer_login.png")

            # Try to find login form
            # Common selectors for login fields
            username_selectors = [
                "input[name='username']",
                "input[name='user']",
                "input[name='login']",
                "input[type='text']",
                "#username",
                "#user",
                "#login"
            ]

            password_selectors = [
                "input[name='password']",
                "input[name='pass']",
                "input[type='password']",
                "#password",
                "#pass"
            ]

            username_field = None
            password_field = None

            # Try to find username field
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"  Found username field: {selector}")
                    break
                except:
                    continue

            # Try to find password field
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"  Found password field: {selector}")
                    break
                except:
                    continue

            if not username_field or not password_field:
                print("  ⚠️  Could not auto-detect login fields")
                print("  Please check screenshot: /tmp/keyedin_informer_login.png")

                # Save page source for analysis
                with open("/tmp/keyedin_informer_page.html", 'w') as f:
                    f.write(self.driver.page_source)
                print("  📄 Page source saved: /tmp/keyedin_informer_page.html")

                return False

            # Enter credentials
            username_field.clear()
            username_field.send_keys(self.username)

            password_field.clear()
            password_field.send_keys(self.password)

            # Find and click login button
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "#login-button",
                ".login-button"
            ]

            for selector in login_button_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"  Found login button: {selector}")
                    button.click()
                    break
                except:
                    continue

            # Wait for login to complete (check for redirect or dashboard elements)
            time.sleep(5)

            # Take screenshot after login
            self.driver.save_screenshot("/tmp/keyedin_informer_after_login.png")
            print("  📸 Post-login screenshot: /tmp/keyedin_informer_after_login.png")

            # Check if we're logged in
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()

            if 'logout' in page_source or 'sign out' in page_source or 'dashboard' in page_source:
                print("✅ Login successful!")
                self.logged_in = True
                return True
            elif 'invalid' in page_source or 'error' in page_source:
                print("❌ Login failed: Invalid credentials")
                return False
            else:
                print("⚠️  Login status unclear. Check screenshots.")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def discover_reports(self) -> List[Dict]:
        """Discover available reports in Informer"""

        if not self.logged_in:
            if not self.login():
                return []

        print("\n🔍 Discovering available reports...")

        try:
            # Look for report links/menus
            # Informer typically has a reports menu or list

            time.sleep(2)

            # Try to find navigation elements
            nav_items = self.driver.find_elements(By.CSS_SELECTOR, "a, button, .menu-item")

            reports = []
            for item in nav_items:
                text = item.text.strip()
                if any(keyword in text.lower() for keyword in ['work order', 'service order', 'invoice', 'job', 'project', 'report']):
                    reports.append({
                        'text': text,
                        'element': item
                    })

            print(f"  Found {len(reports)} potential report links:")
            for r in reports[:20]:  # Limit output
                print(f"    • {r['text']}")

            return reports

        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return []

    def export_work_orders_report(self, report_name: str = None) -> Optional[str]:
        """
        Export work orders report to CSV
        This is often the easiest way to get data from Informer
        """

        if not self.logged_in:
            if not self.login():
                return None

        print(f"\n📊 Attempting to export work orders report...")

        try:
            # Common Informer patterns:
            # 1. Navigate to Reports section
            # 2. Find "Work Orders" or similar report
            # 3. Click export/download button
            # 4. Save CSV file

            # Look for export/download buttons
            export_selectors = [
                "button:contains('Export')",
                "button:contains('Download')",
                "a:contains('CSV')",
                "a:contains('Excel')",
                ".export-button",
                "#export"
            ]

            for selector in export_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"  Found export button: {selector}")
                    button.click()
                    time.sleep(3)
                    break
                except:
                    continue

            # Check downloads folder
            # Note: This requires configuring Chrome to download to specific folder
            print("  ⚠️  Export feature needs manual configuration")
            print("  Please use --interactive mode to click through the UI")

            return None

        except Exception as e:
            print(f"❌ Export error: {e}")
            return None

    def interactive_mode(self):
        """
        Run in non-headless mode for manual exploration
        Useful for discovering the exact UI flow
        """

        print("\n🖱️  INTERACTIVE MODE")
        print("="*80)
        print("Browser window will open. You can:")
        print("  1. Explore the UI manually")
        print("  2. Navigate to work order reports")
        print("  3. Identify element selectors")
        print("  4. Test export functionality")
        print("\nPress Ctrl+C when done to save state and exit")
        print("="*80)

        try:
            # Keep browser open
            input("\nPress Enter to start exploration...")

            if not self.logged_in:
                self.login()

            # Wait for user to explore
            input("\nExplore the UI, then press Enter when done...")

            # Save final state
            self.driver.save_screenshot("/tmp/keyedin_informer_final.png")
            with open("/tmp/keyedin_informer_final.html", 'w') as f:
                f.write(self.driver.page_source)

            print("\n💾 Saved final state:")
            print("  Screenshot: /tmp/keyedin_informer_final.png")
            print("  HTML: /tmp/keyedin_informer_final.html")

        except KeyboardInterrupt:
            print("\n\n👋 Exiting interactive mode...")

        finally:
            self.close()

    def close(self):
        """Clean up browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="KeyedIn Informer Portal Scraper")
    parser.add_argument('--username', help='KeyedIn username')
    parser.add_argument('--password', help='KeyedIn password')
    parser.add_argument('--discover', action='store_true', help='Discover available reports')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode (non-headless)')
    parser.add_argument('--export', action='store_true', help='Attempt to export work orders')
    args = parser.parse_args()

    print("="*80)
    print("🌐 KeyedIn Informer Portal Scraper")
    print("="*80)
    print()

    scraper = None

    try:
        scraper = KeyedInInformerScraper(
            username=args.username,
            password=args.password,
            headless=not args.interactive
        )

        if args.interactive:
            scraper.interactive_mode()
        else:
            # Login
            if not scraper.login():
                print("\n❌ Login failed. Cannot proceed.")
                return

            # Discovery
            if args.discover:
                scraper.discover_reports()

            # Export
            if args.export:
                scraper.export_work_orders_report()

            # If no action, show help
            if not (args.discover or args.export):
                print("\n💡 What would you like to do?")
                print("  --discover      Discover available reports")
                print("  --interactive   Open browser for manual exploration")
                print("  --export        Attempt to export work orders")
                print("\nExample:")
                print("  python scrape_keyedin_informer.py --interactive")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
