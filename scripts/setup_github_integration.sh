#!/bin/bash
# Setup script for GitHub integration with CrewAI

set -euo pipefail

WORKDIR="$HOME/ai-dev-team"
ENV_FILE="$WORKDIR/.env"

echo "🔧 Setting up GitHub integration for CrewAI..."
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    touch "$ENV_FILE"
fi

# Check for GitHub token
if ! grep -q "GITHUB_TOKEN" "$ENV_FILE" 2>/dev/null; then
    echo ""
    echo "📝 GitHub Personal Access Token Setup"
    echo "======================================"
    echo ""
    echo "To connect CrewAI to GitHub, you need a Personal Access Token."
    echo ""
    echo "Steps to create a token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token' -> 'Generate new token (classic)'"
    echo "3. Give it a name (e.g., 'CrewAI Integration')"
    echo "4. Select scopes:"
    echo "   - repo (Full control of private repositories)"
    echo "   - read:org (Read org and team membership)"
    echo "5. Click 'Generate token'"
    echo "6. Copy the token (you won't see it again!)"
    echo ""
    read -p "Enter your GitHub token (or press Enter to skip): " github_token
    
    if [ -n "$github_token" ]; then
        echo "GITHUB_TOKEN=$github_token" >> "$ENV_FILE"
        echo "✓ GitHub token added to .env"
    else
        echo "⚠️  Skipping token setup. You can add it later to $ENV_FILE"
    fi
else
    echo "✓ GitHub token already configured"
fi

# Set default repo
if ! grep -q "GITHUB_REPO" "$ENV_FILE" 2>/dev/null; then
    echo ""
    read -p "Enter your GitHub repository (format: owner/repo, or press Enter to skip): " github_repo
    
    if [ -n "$github_repo" ]; then
        echo "GITHUB_REPO=$github_repo" >> "$ENV_FILE"
        echo "✓ GitHub repository configured"
    else
        echo "⚠️  Skipping repo setup. You can add it later to $ENV_FILE"
    fi
else
    echo "✓ GitHub repository already configured"
fi

# Install additional dependencies if needed
echo ""
echo "📦 Checking dependencies..."
cd "$WORKDIR"
source .venv/bin/activate

# Check if composio is installed (optional)
if ! python3 -c "import composio_core" 2>/dev/null; then
    echo ""
    read -p "Install Composio for advanced GitHub actions? (y/n): " install_composio
    if [ "$install_composio" = "y" ] || [ "$install_composio" = "Y" ]; then
        pip install composio-core composio-openai
        echo "✓ Composio installed"
    fi
fi

echo ""
echo "✅ GitHub integration setup complete!"
echo ""
echo "Next steps:"
echo "1. Review your configuration: cat $ENV_FILE"
echo "2. Test the integration:"
echo "   cd $WORKDIR"
echo "   source .venv/bin/activate"
echo "   python3 github_crew.py <issue_number> [repo]"
echo ""
echo "Example:"
echo "   python3 github_crew.py 123 owner/repo"
