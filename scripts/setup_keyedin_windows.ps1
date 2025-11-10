# PowerShell script to set up KeyedIn scraping on Windows
# Run this from your SignX/keyedin directory

Write-Host "🚀 Setting up KeyedIn Scraper on Windows" -ForegroundColor Green
Write-Host ""

# Check Python installation
Write-Host "📋 Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python not found. Install from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing Python dependencies..."
pip install requests beautifulsoup4 lxml selenium 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Some dependencies may have failed. Try manually:" -ForegroundColor Yellow
    Write-Host "     pip install requests beautifulsoup4 lxml selenium"
}

# Create .env.keyedin file
Write-Host ""
Write-Host "📝 Creating .env.keyedin file..."
$envContent = @"
# KeyedIn CRM Credentials
# DO NOT COMMIT THIS FILE TO GIT

KEYEDIN_USERNAME=BradyF
KEYEDIN_PASSWORD=Eagle@605!
KEYEDIN_BASE_URL=https://eaglesign.keyedinsign.com

"@

Set-Content -Path ".env.keyedin" -Value $envContent
Write-Host "  ✅ Credentials file created" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Files created:"
Write-Host "   - .env.keyedin (with your credentials)"
Write-Host ""
Write-Host "🔧 Next steps:"
Write-Host "   1. Copy the Python scripts from SignX/scripts/ to this directory:"
Write-Host "      - test_keyedin_connection.py"
Write-Host "      - scrape_keyedin.py"
Write-Host ""
Write-Host "   2. Run the connection test:"
Write-Host "      python test_keyedin_connection.py"
Write-Host ""
Write-Host "   3. If login succeeds, you'll see work order discovery results"
Write-Host ""
