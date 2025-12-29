#!/bin/bash
# Update the MCP server to the latest version
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Updating OCI Log Analytics MCP Server..."
echo ""

# Check if this is a git repo
if [ ! -d ".git" ]; then
    echo "ERROR: This installation is not a git repository."
    echo "To enable updates, you need to reinstall using the setup script."
    echo ""
    echo "Run: rm -rf ~/oci-log-analytics-mcp && bash setup_oel9.sh"
    exit 1
fi

# Pull latest changes
BRANCH="claude/restore-oci-analytics-ZxSQg"
echo "Fetching updates from origin/$BRANCH..."
git fetch origin "$BRANCH"

# Check if there are updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Already up to date!"
else
    echo "Updates available. Pulling changes..."
    git pull origin "$BRANCH"

    echo ""
    echo "Reinstalling package with new changes..."
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install -e .

    echo ""
    echo "Update complete!"
    echo ""
    echo "Changes pulled:"
    git log --oneline "$LOCAL..$REMOTE"
fi

echo ""
echo "Current version: $(git rev-parse --short HEAD)"
