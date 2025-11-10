# Install Firecrawl MCP Server for Claude Code (Windows)

Write-Host "🔥 Installing Firecrawl MCP Server for Claude Code" -ForegroundColor Cyan

# Install via npm (requires Node.js)
Write-Host "`nInstalling @firecrawl/mcp-server..." -ForegroundColor Yellow
npm install -g @firecrawl/mcp-server

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install. Make sure Node.js is installed." -ForegroundColor Red
    exit 1
}

# Find Claude config location
$ConfigDir = "$env:APPDATA\Claude"
$ConfigFile = "$ConfigDir\claude_desktop_config.json"

Write-Host "`n📝 Config location: $ConfigFile" -ForegroundColor Cyan

# Create config directory if needed
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

# Backup existing config
if (Test-Path $ConfigFile) {
    Copy-Item $ConfigFile "$ConfigFile.backup" -Force
    Write-Host "✅ Backed up existing config to $ConfigFile.backup" -ForegroundColor Green
}

# Read API key from environment or prompt
$ApiKey = $env:FIRECRAWL_API_KEY
if (-not $ApiKey) {
    Write-Host "`n⚠️  FIRECRAWL_API_KEY not found in environment" -ForegroundColor Yellow
    $ApiKey = Read-Host "Enter your Firecrawl API key (or press Enter to add it manually later)"
    if (-not $ApiKey) {
        $ApiKey = "YOUR_API_KEY_HERE"
    }
}

# Create MCP server configuration
$Config = @{
    mcpServers = @{
        firecrawl = @{
            command = "npx"
            args = @("-y", "@firecrawl/mcp-server")
            env = @{
                FIRECRAWL_API_KEY = $ApiKey
            }
        }
    }
}

# Save to JSON
$Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile -Encoding UTF8

Write-Host "`n✅ Configuration saved to $ConfigFile" -ForegroundColor Green

if ($ApiKey -eq "YOUR_API_KEY_HERE") {
    Write-Host "`n⚠️  IMPORTANT: Edit the config file and replace YOUR_API_KEY_HERE" -ForegroundColor Yellow
    Write-Host "   Config file: $ConfigFile" -ForegroundColor Yellow
    Write-Host "`n   Or set environment variable:" -ForegroundColor Yellow
    Write-Host "   `$env:FIRECRAWL_API_KEY = 'fc-your-key'" -ForegroundColor Cyan
}

Write-Host "`n🔄 Restart Claude Code to activate the MCP server." -ForegroundColor Cyan
Write-Host "`nOnce active, you can ask Claude Code:" -ForegroundColor White
Write-Host "   'Scrape https://example.com and summarize the content'" -ForegroundColor Gray

# Test if Node.js is installed
Write-Host "`n🔍 Checking dependencies..." -ForegroundColor Cyan
node --version
npm --version

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
