#!/bin/bash
# Install Firecrawl MCP Server for Claude Code

echo "🔥 Installing Firecrawl MCP Server for Claude Code"

# Install via npm
npm install -g @firecrawl/mcp-server

# Find Claude config location
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CONFIG_DIR="$HOME/.config/Claude"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    CONFIG_DIR="$APPDATA/Claude"
else
    echo "❌ Unsupported OS"
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

echo "📝 Config location: $CONFIG_FILE"

# Backup existing config
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
    echo "✅ Backed up existing config"
fi

# Create config directory if needed
mkdir -p "$CONFIG_DIR"

# Add Firecrawl MCP server configuration
cat > "$CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "@firecrawl/mcp-server"],
      "env": {
        "FIRECRAWL_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
EOF

echo "✅ Configuration created!"
echo ""
echo "⚠️  IMPORTANT: Edit the config file and replace YOUR_API_KEY_HERE with your actual API key"
echo ""
echo "Then restart Claude Code to activate the MCP server."
