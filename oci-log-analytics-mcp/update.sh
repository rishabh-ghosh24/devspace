#!/bin/bash
# Update the MCP server to the latest version
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  OCI Log Analytics MCP Server - Update"
echo "=============================================="
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
    UPDATED=false
else
    echo "Updates available. Pulling changes..."
    git pull origin "$BRANCH"
    UPDATED=true

    echo ""
    echo "Changes pulled:"
    git log --oneline "$LOCAL..$REMOTE"
fi

# Handle nested directory structure
# The git repo has files in oci-log-analytics-mcp/ subdirectory
# but the installation uses files in the root directory
NESTED_DIR="$SCRIPT_DIR/oci-log-analytics-mcp"

if [ -d "$NESTED_DIR/src" ]; then
    echo ""
    echo "Syncing source files from nested directory..."

    # Sync src directory
    if [ -d "$NESTED_DIR/src/oci_la_mcp" ]; then
        cp -r "$NESTED_DIR/src/oci_la_mcp"/* "$SCRIPT_DIR/src/oci_la_mcp/"
        echo "  ✓ Synced src/oci_la_mcp/"
    fi

    # Sync tests if they exist
    if [ -d "$NESTED_DIR/tests" ] && [ -d "$SCRIPT_DIR/tests" ]; then
        cp -r "$NESTED_DIR/tests"/* "$SCRIPT_DIR/tests/" 2>/dev/null || true
        echo "  ✓ Synced tests/"
    fi

    # Sync docs if they exist
    if [ -d "$NESTED_DIR/docs" ] && [ -d "$SCRIPT_DIR/docs" ]; then
        cp -r "$NESTED_DIR/docs"/* "$SCRIPT_DIR/docs/" 2>/dev/null || true
        echo "  ✓ Synced docs/"
    fi

    # Sync root files
    for file in pyproject.toml SETUP_GUIDE.md README.md; do
        if [ -f "$NESTED_DIR/$file" ]; then
            cp "$NESTED_DIR/$file" "$SCRIPT_DIR/$file"
        fi
    done
    echo "  ✓ Synced configuration files"
fi

# Always reinstall to ensure changes are applied
echo ""
echo "Reinstalling package..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install -e . --quiet

echo ""
echo "=============================================="
echo "  Update Complete!"
echo "=============================================="
echo ""
echo "Current version: $(git rev-parse --short HEAD)"
echo ""

# Verify the fix is in place
if grep -q "_is_tenancy_ocid" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "✓ Tenancy subcompartments fix: INSTALLED"
else
    echo "✗ Tenancy subcompartments fix: NOT FOUND"
    echo "  Try running: ./update.sh again"
fi

if grep -q "include_subcompartments" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "✓ include_subcompartments parameter: INSTALLED"
else
    echo "✗ include_subcompartments parameter: NOT FOUND"
fi

echo ""
echo "Next steps:"
echo "  1. Restart the MCP server: ./run.sh"
echo "  2. Reconnect Claude Desktop"
