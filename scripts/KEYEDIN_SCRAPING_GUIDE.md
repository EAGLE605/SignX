# KeyedIn CRM Data Extraction Guide

Your KeyedIn system has **two interfaces** we can scrape:

1. **Legacy CGI System** - `https://eaglesign.keyedinsign.com/cgi-bin/mvi.exe/LOGIN.START`
2. **Informer Portal** - `https://eaglesign.keyedinsign.com:8443/eaglesign/Informer.html`

---

## 🎯 Which One to Use?

### **Informer Portal** (Recommended) ⭐
- Modern reporting interface
- Likely has CSV/Excel export
- Better for batch data extraction
- **Use this if**: You can access work order reports and export them

### **Legacy CGI** (Fallback)
- Older interface (1990s-2000s technology)
- Page-by-page navigation
- More brittle but works when Informer doesn't have the data
- **Use this if**: Informer doesn't have work orders or you need specific order details

---

## 🚀 Quick Start

### **Step 1: Install Dependencies**

```bash
# For both scrapers
pip install requests beautifulsoup4 lxml

# For Informer scraper (requires browser)
pip install selenium

# Install Chrome/Chromium
# Windows: Download from https://www.google.com/chrome/
# Linux: sudo apt install chromium-browser chromium-chromedriver
```

### **Step 2: Set Credentials**

```bash
# Option A: Environment variables (recommended)
export KEYEDIN_USERNAME="your_username"
export KEYEDIN_PASSWORD="your_password"

# Option B: Pass as arguments
python scrape_keyedin.py --username your_username --password your_password
```

### **Step 3: Discovery (Find Where Data Lives)**

#### **Try Informer First** (Modern UI)

```bash
# Interactive mode - opens browser, you explore manually
python scripts/scrape_keyedin_informer.py --interactive

# What to do:
# 1. Browser opens and logs in
# 2. Look for "Reports" or "Work Orders" menu
# 3. Find "Work Order Report" or similar
# 4. Check if there's an "Export" or "Download" button
# 5. Note the URL and button locations
# 6. Press Enter when done - saves screenshots
```

#### **Fallback: Try Legacy CGI**

```bash
# Discover navigation structure
python scripts/scrape_keyedin.py --discover

# Export sample pages for analysis
python scripts/scrape_keyedin.py --export-samples

# Check: ./keyedin_samples/*.html
```

---

## 📊 Extracting Work Order Data

### **Method 1: Informer Export (Best)**

If Informer has a work order report with export:

1. **Manual first run** (figure out the workflow):
   ```bash
   python scripts/scrape_keyedin_informer.py --interactive
   ```

   - Login
   - Navigate to Reports → Work Orders
   - Click Export → CSV
   - Download shows up in Downloads folder
   - Note the exact clicks you made

2. **Automate it** (after you know the workflow):
   - I'll update the script with the exact selectors you found
   - Run in headless mode
   - Auto-download CSVs daily

3. **Import to database**:
   ```bash
   python scripts/import_keyedin_csv.py --file ~/Downloads/work_orders_export.csv
   ```

### **Method 2: Legacy CGI Scraping (Slower)**

If you have work order IDs (like WO-12345):

```bash
# Scrape single work order
python scripts/scrape_keyedin.py --order-id WO-12345

# Scrape batch (create file with IDs)
echo "WO-12345" >> order_ids.txt
echo "WO-12346" >> order_ids.txt
python scripts/scrape_keyedin_batch.py --file order_ids.txt
```

### **Method 3: Manual Export + Parser**

If automated scraping is too complex:

1. **You manually export** from KeyedIn:
   - Login to KeyedIn Informer
   - Go to Work Orders report
   - Export to CSV/Excel
   - Save to: `SignX/data/keyedin_exports/work_orders_2025.csv`

2. **I parse it**:
   ```bash
   python scripts/parse_keyedin_export.py \
     --file data/keyedin_exports/work_orders_2025.csv \
     --import-to-db
   ```

---

## 🗂️ Data We Need to Extract

For each work order, we want:

```json
{
  "order_id": "WO-12345",
  "customer_name": "Valley Church",
  "project_name": "Monument Sign",
  "sign_type": "monument",
  "completed_date": "2024-08-15",

  "costs": {
    "materials": 2100.00,
    "labor_hours": 24.0,
    "labor_cost": 1560.00,
    "subcontractors": 0.00,
    "total": 4500.00
  },

  "materials_detail": [
    {"item": "Aluminum sheet", "qty": 20, "cost": 800.00},
    {"item": "LED modules", "qty": 4, "cost": 400.00},
    {"item": "Matthews paint", "qty": 2, "cost": 150.00}
  ],

  "dimensions": {
    "width_ft": 10,
    "height_ft": 4,
    "depth_ft": 1.5
  },

  "location": "Grimes, IA"
}
```

---

## 🔧 Troubleshooting

### **Login Fails**

```bash
# Check credentials
echo $KEYEDIN_USERNAME
echo $KEYEDIN_PASSWORD

# Try interactive mode to see what's happening
python scripts/scrape_keyedin_informer.py --interactive

# Check screenshots
ls -lh /tmp/keyedin_*.png
```

### **Can't Find Work Orders**

1. **Check if Informer has them**:
   - Login manually: https://eaglesign.keyedinsign.com:8443/eaglesign/Informer.html
   - Look for Reports → Work Orders
   - If YES: Use Informer scraper
   - If NO: Use legacy CGI scraper

2. **Check URL patterns**:
   - Work orders might be under different names: "Service Orders", "Jobs", "Projects"
   - Try: `scrape_keyedin.py --discover` to find all links

### **Export Doesn't Work**

- Informer exports might download to a specific folder
- Check: Chrome downloads folder
- Configure download location in script
- Or: Manual export + parser (Method 3)

---

## 📝 Next Steps After Extraction

Once you have cost data extracted:

### **1. Import to Database**

```bash
python scripts/import_historical_costs.py \
  --source keyedin_exports/work_orders.csv \
  --years 5
```

### **2. Upload to Gemini RAG**

```bash
python scripts/export_to_gemini_rag.py \
  --include-costs \
  --limit 500
```

### **3. Train ML Pricing Model**

```bash
python scripts/train_pricing_model.py \
  --data-source postgresql \
  --features sign_type,dimensions,materials,location \
  --target total_cost
```

### **4. Build Quote Endpoint with Real Data**

```bash
# Now you can build the quoting endpoint with:
# - Historical cost averages
# - ML price predictions
# - Gemini RAG similar projects
# - All based on YOUR actual data!
```

---

## ⚡ Quick Decision Tree

```
START: Where is your cost data?

├─ "In KeyedIn Informer reports"
│  └─ Use: scrape_keyedin_informer.py --interactive
│     └─ Find export button → CSV → import_keyedin_csv.py
│
├─ "In legacy CGI system"
│  └─ Use: scrape_keyedin.py --discover
│     └─ Find work order URLs → scrape individual orders
│
├─ "I can export manually to CSV"
│  └─ You export → Save to data/ → parse_keyedin_export.py
│
└─ "I don't know"
   └─ Try Informer first: scrape_keyedin_informer.py --interactive
      └─ If no data there, try CGI: scrape_keyedin.py --discover
```

---

## 🎯 Recommended Approach

**For fastest results:**

1. **Today (30 min)**: Try Informer interactive mode
   ```bash
   python scripts/scrape_keyedin_informer.py --interactive
   ```
   - Login and explore
   - Find work order report
   - Try manual export
   - See if CSV works

2. **If Informer works** (2 hours):
   - Manual export to CSV
   - I'll build CSV parser
   - Import to PostgreSQL
   - Upload to Gemini RAG
   - **DONE** - you have cost data!

3. **If Informer doesn't work** (1 day):
   - Use legacy CGI scraper
   - Pull 200 orders at a time
   - Parse HTML tables
   - Import to database

4. **Week 2**: Build quote endpoint with real costs

---

## 📞 Support

If you get stuck:

1. **Check screenshots**: `/tmp/keyedin_*.png`
2. **Check saved HTML**: `/tmp/keyedin_*.html`
3. **Run in interactive mode**: See what's actually happening
4. **Manual export**: Fastest fallback is you export, I parse

---

## 🚀 Ready to Start?

**Recommended first command:**

```bash
# Set credentials
export KEYEDIN_USERNAME="your_username"
export KEYEDIN_PASSWORD="your_password"

# Try Informer (modern interface)
python scripts/scrape_keyedin_informer.py --interactive

# Opens browser → You explore → Find work order reports
```

**After discovery, come back and we'll automate the extraction!**

---

**Files:**
- `scrape_keyedin.py` - Legacy CGI scraper
- `scrape_keyedin_informer.py` - Modern Informer portal scraper
- `KEYEDIN_SCRAPING_GUIDE.md` - This guide

**Next files to create** (after you tell me what you find):
- `import_keyedin_csv.py` - Import exported CSVs
- `parse_keyedin_export.py` - Parse specific export format
- `scrape_keyedin_batch.py` - Bulk scraping

