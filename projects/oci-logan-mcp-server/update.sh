#!/bin/bash
#
# OCI Log Analytics MCP Server - Update & Restart
#
# Updates to latest version and restarts the server
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  OCI Log Analytics MCP Server - Update"
echo "=============================================="
echo ""

# Check if this is a git repo
if [ ! -d ".git" ]; then
    echo "ERROR: Not a git repository. Cannot update."
    echo "Run a fresh install: rm -rf ~/oci-log-analytics-mcp && bash setup_oel9.sh"
    exit 1
fi

BRANCH="claude/restore-oci-analytics-ZxSQg"

# Fetch and check for updates
echo "Checking for updates..."
if git fetch origin "$BRANCH" 2>/dev/null; then
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "origin/$BRANCH")

    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Updates available. Pulling..."
        git pull origin "$BRANCH"

        echo ""
        echo "Reinstalling package..."
        source "$SCRIPT_DIR/venv/bin/activate"
        pip install -e . --quiet

        echo ""
        echo "Changes applied:"
        git log --oneline "$LOCAL..$REMOTE"
    else
        echo "Already up to date."
    fi
else
    echo "Could not fetch updates (offline?). Continuing with current version."
fi

echo ""
echo "Current version: $(git rev-parse --short HEAD)"

# Verify fixes
echo ""
echo "Verifying installation..."
if grep -q "_is_tenancy_ocid" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "  ✓ Tenancy subcompartments fix"
else
    echo "  ✗ Tenancy subcompartments fix MISSING"
fi

if grep -q "include_subcompartments" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "  ✓ include_subcompartments parameter"
else
    echo "  ✗ include_subcompartments parameter MISSING"
fi

# Start server
echo ""
echo "=============================================="
echo "  Starting MCP Server"
echo "=============================================="
echo ""
echo "Server is running. Press Ctrl+C to stop."
echo ""

source "$SCRIPT_DIR/venv/bin/activate"
exec python -m oci_la_mcp
