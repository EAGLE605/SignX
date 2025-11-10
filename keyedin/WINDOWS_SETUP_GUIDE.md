# KeyedIn Scraper - Windows Setup Guide

Complete walkthrough for extracting historical cost data from KeyedIn CRM on your Windows machine.

---

## Prerequisites

1. **Python 3.8+** installed
   - Check: Open PowerShell and run `python --version`
   - If not installed: Download from https://www.python.org/downloads/
   - ✅ Make sure to check "Add Python to PATH" during installation

2. **Git** (to get the files)
   - Or manually copy files from the repository

3. **KeyedIn Access**
   - You need to be able to login at: https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN.START
   - Credentials: BradyF / Eagle@605!

---

## Step-by-Step Setup

### 1. Create Working Directory

Open PowerShell and run:

```powershell
# Navigate to your SignX project
cd C:\path\to\your\SignX

# Create keyedin folder
New-Item -ItemType Directory -Force -Path "keyedin"
cd keyedin
```

### 2. Copy Files from Repository

You need these files from `SignX/scripts/`:

```
keyedin/
├── .env.keyedin               # Credentials (will create)
├── test_keyedin_connection.py # Connection test
├── scrape_keyedin.py          # Main scraper
├── setup_keyedin_windows.ps1  # Setup script
└── run_keyedin_test.ps1       # Test runner
```

**Option A: Copy from Git repository**
```powershell
# From keyedin/ directory
Copy-Item ..\scripts\test_keyedin_connection.py .
Copy-Item ..\scripts\scrape_keyedin.py .
Copy-Item ..\scripts\setup_keyedin_windows.ps1 .
Copy-Item ..\scripts\run_keyedin_test.ps1 .
```

**Option B: Download from GitHub**
```powershell
# If you cloned from GitHub
git pull origin main
Copy-Item ..\scripts\*.py .
Copy-Item ..\scripts\*.ps1 .
```

### 3. Run Setup Script

```powershell
# This installs dependencies and creates .env.keyedin
.\setup_keyedin_windows.ps1
```

**What it does:**
- ✅ Checks Python installation
- ✅ Installs requests, beautifulsoup4, lxml, selenium
- ✅ Creates .env.keyedin with your credentials

### 4. Test Connection

```powershell
# Run the connection test
.\run_keyedin_test.ps1
```

**Expected output if successful:**

```
🔧 KeyedIn Connection Test
================================================================================

📄 Loading credentials from .env.keyedin
  ✓ Set KEYEDIN_USERNAME
  ✓ Set KEYEDIN_PASSWORD
  ✓ Set KEYEDIN_BASE_URL

Username: BradyF
Password: **********
Base URL: https://eaglesign.keyedinsign.com

🔐 Testing login...
  Found username field: username
  Found password field: password
  Posting to: https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN
✅ Login successful!

🔍 Discovering navigation...
  Found 12 relevant links:
    • Work Orders: /WORKORDER.LIST
    • Service Orders: /SERVICE.LIST
    • Reports: /REPORTS

✅ FOUND WORK ORDER LIST: https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/WORKORDER.LIST

Next: Get a work order ID and run:
  python scrape_keyedin.py --order-id YOUR_ID
```

---

## If Connection Test Succeeds

### Find a Work Order ID

1. **Manually login to KeyedIn**:
   - Go to: https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN.START
   - Login with BradyF / Eagle@605!

2. **Navigate to Work Orders**:
   - Find the work order list page
   - Click on any recent work order
   - Note the work order ID (e.g., "WO-12345" or "24-1234")

3. **Test scraping that order**:
   ```powershell
   python scrape_keyedin.py --order-id WO-12345
   ```

### Expected Output

```
🔧 KeyedIn Sign CRM Scraper
================================================================================

🔐 Logging into KeyedIn as BradyF...
✅ Login successful!

📋 Scraping work order: WO-12345
  💾 Saved raw HTML to /tmp/keyedin_workorder_WO-12345.html

📊 Extracted data:
{
  "order_id": "WO-12345",
  "customer": "Valley Church",
  "project": "Monument Sign",
  "total": "4500.00",
  "materials": "2100.00",
  "labor": "1560.00",
  "date": "08/15/2024",
  "scraped_at": "2025-01-10T10:30:00"
}
```

---

## If Connection Test Fails

### Troubleshooting Steps

#### Error: 403 Forbidden

**Possible causes:**
1. **Wrong URL** - Check if it's http vs https
2. **Credentials changed** - Try logging in manually first
3. **IP restrictions** - KeyedIn might block automated access

**Fix:**
```powershell
# Try http instead of https
notepad .env.keyedin
# Change to: KEYEDIN_BASE_URL=http://eaglesign.keyedinsign.com

# Run test again
.\run_keyedin_test.ps1
```

#### Error: Invalid credentials

**Fix:**
```powershell
# Verify credentials manually first
# Then update .env.keyedin
notepad .env.keyedin

# Test again
.\run_keyedin_test.ps1
```

#### Error: No login form found

**Fix:**
```powershell
# Check saved HTML to see what page you're getting
python
>>> from scrape_keyedin import KeyedInScraper
>>> scraper = KeyedInScraper()
>>> response = scraper.session.get("https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN.START")
>>> with open("login_page.html", "w") as f:
...     f.write(response.text)
>>> exit()

# Open login_page.html in browser to see what's actually there
notepad login_page.html
```

---

## Next Steps After Successful Test

### Phase 1: Discover Work Order Structure

```powershell
# Discover available pages
python scrape_keyedin.py --discover

# Export sample pages for analysis
python scrape_keyedin.py --export-samples

# Check samples
explorer keyedin_samples
```

### Phase 2: Scrape Historical Data

Once you know the work order IDs:

```powershell
# Create list of order IDs
echo WO-12345 > order_ids.txt
echo WO-12346 >> order_ids.txt
echo WO-12347 >> order_ids.txt

# Scrape all orders
foreach ($id in Get-Content order_ids.txt) {
    python scrape_keyedin.py --order-id $id
}
```

### Phase 3: Import to Database

```powershell
# Export scraped data
python scrape_keyedin.py --export-all --output historical_costs.json

# Import to PostgreSQL
cd ..\scripts
python import_historical_costs.py --source ..\keyedin\historical_costs.json
```

---

## Getting Work Order IDs Automatically

If there's a work order list page, we can scrape all IDs:

```powershell
# Discover the work order list URL
python scrape_keyedin.py --discover

# If it finds the list page, scrape all IDs
python scrape_keyedin.py --extract-order-ids --output order_ids.txt

# Then batch scrape
foreach ($id in Get-Content order_ids.txt) {
    python scrape_keyedin.py --order-id $id
    Start-Sleep -Seconds 2  # Be nice to the server
}
```

---

## Alternative: Use Informer Portal

If the legacy CGI scraper doesn't work well, try the modern Informer interface:

```powershell
# Install Selenium
pip install selenium

# Run interactive discovery
python ..\scripts\scrape_keyedin_informer.py --interactive

# This opens a browser where you can:
# 1. Manually explore the interface
# 2. Find work order reports
# 3. Check if there's an export button
# 4. Download CSV exports
```

---

## Manual Export Option (Fastest)

If automated scraping is too complex:

1. **Login to KeyedIn manually**
2. **Navigate to Reports → Work Orders**
3. **Export to CSV/Excel** (if available)
4. **Save to**: `SignX/keyedin/exports/work_orders.csv`
5. **Run parser**:
   ```powershell
   python ..\scripts\parse_keyedin_export.py --file exports\work_orders.csv --import-to-db
   ```

---

## Important Notes

### Security

- ✅ `.env.keyedin` is git-ignored (won't be committed)
- ⚠️ Don't share your credentials
- ⚠️ Don't commit `order_ids.txt` or scraped data files

### Rate Limiting

- 🐢 Add delays between requests: `Start-Sleep -Seconds 2`
- 🐢 Don't overwhelm the server
- 🐢 KeyedIn might block aggressive scraping

### Data Validation

After scraping, verify the data:

```powershell
# Check scraped files
Get-ChildItem /tmp/keyedin_workorder_*.html | Measure-Object

# Verify extracted data
python -c "import json; print(json.load(open('historical_costs.json')))"
```

---

## Quick Reference

### One-Command Test

```powershell
# Full test from scratch
.\setup_keyedin_windows.ps1; .\run_keyedin_test.ps1
```

### Scrape Single Order

```powershell
python scrape_keyedin.py --order-id WO-12345
```

### Batch Scrape

```powershell
Get-Content order_ids.txt | ForEach-Object {
    python scrape_keyedin.py --order-id $_
    Start-Sleep -Seconds 2
}
```

### View Results

```powershell
# Open saved HTML files
explorer /tmp

# View JSON output
notepad historical_costs.json
```

---

## Support

If you get stuck:

1. **Check screenshots/HTML**: Look at saved files in `/tmp/`
2. **Run in debug mode**: `python scrape_keyedin.py --order-id WO-12345 --debug`
3. **Try interactive Informer mode**: Easier UI discovery
4. **Manual export fallback**: You export, we parse

---

## Expected Timeline

- **Today (30 min)**: Run connection test, verify login works
- **Today (1 hour)**: Find work order list, get sample IDs
- **Today (2 hours)**: Scrape 10-20 test orders, verify data quality
- **Tomorrow**: Batch scrape all historical orders (might take hours)
- **Day 3**: Import to database, verify data integrity
- **Day 4**: Upload to Gemini RAG, build quoting endpoint

---

## Ready to Start?

1. ✅ Copy files to `keyedin/` folder
2. ✅ Run `.\setup_keyedin_windows.ps1`
3. ✅ Run `.\run_keyedin_test.ps1`
4. ✅ Report back with results!

**Command to run now:**

```powershell
cd C:\path\to\SignX\keyedin
.\setup_keyedin_windows.ps1
.\run_keyedin_test.ps1
```

Let me know what you see! 🚀
