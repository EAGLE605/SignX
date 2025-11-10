# PowerShell wrapper to run KeyedIn connection test
# This loads credentials from .env.keyedin and runs the test

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🔧 KeyedIn Connection Test" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Check if .env.keyedin exists
if (-not (Test-Path ".env.keyedin")) {
    Write-Host "❌ Missing .env.keyedin file!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Run setup_keyedin_windows.ps1 first or create .env.keyedin with:"
    Write-Host "  KEYEDIN_USERNAME=BradyF"
    Write-Host "  KEYEDIN_PASSWORD=Eagle@605!"
    Write-Host "  KEYEDIN_BASE_URL=https://eaglesign.keyedinsign.com"
    exit 1
}

# Check if test script exists
if (-not (Test-Path "test_keyedin_connection.py")) {
    Write-Host "❌ Missing test_keyedin_connection.py!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Copy from SignX/scripts/test_keyedin_connection.py"
    exit 1
}

# Check if main scraper exists
if (-not (Test-Path "scrape_keyedin.py")) {
    Write-Host "❌ Missing scrape_keyedin.py!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Copy from SignX/scripts/scrape_keyedin.py"
    exit 1
}

# Load environment variables from .env.keyedin
Write-Host "📄 Loading credentials from .env.keyedin..."
Get-Content ".env.keyedin" | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        Write-Host "  ✓ Set $name" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🚀 Running connection test..."
Write-Host ""

# Run the Python test script
python test_keyedin_connection.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "✅ Test completed successfully!" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "⚠️  Test completed with errors" -ForegroundColor Yellow
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Check the output above for details."
    Write-Host "Look for saved HTML files in /tmp/ or current directory for debugging."
}

Write-Host ""
