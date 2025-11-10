#!/usr/bin/env python3
"""
Quick test script for KeyedIn connection
Loads credentials from .env.keyedin and tests login
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env.keyedin
env_file = Path(__file__).parent / ".env.keyedin"
if env_file.exists():
    print(f"📄 Loading credentials from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"  ✓ Set {key}")
else:
    print(f"⚠️  No .env.keyedin file found at {env_file}")
    print("Using environment variables instead...")

# Now import and test
try:
    from scrape_keyedin import KeyedInScraper
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nInstall dependencies:")
    print("  pip install requests beautifulsoup4 lxml")
    sys.exit(1)

def main():
    print("\n" + "="*80)
    print("🔧 KeyedIn Connection Test")
    print("="*80)
    print()

    # Show what we're using (masked password)
    username = os.getenv("KEYEDIN_USERNAME")
    password = os.getenv("KEYEDIN_PASSWORD")
    base_url = os.getenv("KEYEDIN_BASE_URL")

    if not username or not password:
        print("❌ Missing credentials!")
        print("\nCreate scripts/.env.keyedin with:")
        print("  KEYEDIN_USERNAME=your_username")
        print("  KEYEDIN_PASSWORD=your_password")
        print("  KEYEDIN_BASE_URL=http://eaglesign.keyedinsign.com")
        sys.exit(1)

    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"Base URL: {base_url}")
    print()

    try:
        # Create scraper
        scraper = KeyedInScraper()

        # Test login
        print("🔐 Testing login...\n")
        if scraper.login():
            print("\n✅ LOGIN SUCCESSFUL!")
            print()

            # Try to discover navigation
            print("🔍 Discovering navigation...\n")
            links = scraper.discover_navigation()

            if links:
                print(f"\n✅ Found {len(links)} relevant pages")
                print("\nNext steps:")
                print("  1. Run: python scripts/scrape_keyedin.py --discover")
                print("  2. Find work order list URL")
                print("  3. Get a work order ID and test scraping")
            else:
                print("\n⚠️  No work order links found")
                print("Check the saved HTML files in keyedin_samples/")

            # Try to find work order list
            print("\n🔍 Searching for work order list page...\n")
            wo_url = scraper.find_work_order_list()

            if wo_url:
                print(f"\n✅ FOUND WORK ORDER LIST: {wo_url}")
                print("\nNext: Get a work order ID and run:")
                print("  python scripts/scrape_keyedin.py --order-id YOUR_ID")
            else:
                print("\n⚠️  Could not auto-find work order list")
                print("You may need to navigate manually and find the URL")

        else:
            print("\n❌ LOGIN FAILED")
            print("\nCheck:")
            print("  1. Credentials are correct")
            print("  2. URL is correct (http vs https)")
            print("  3. Saved response: /tmp/keyedin_login_response.html")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
