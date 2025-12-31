#!/bin/bash
#
# OCI Log Analytics MCP Server - Start Script
#
# Usage:
#   ./start.sh              # Check for updates, then start server
#   ./start.sh --no-update  # Skip update check, just start server
#   ./start.sh --update     # Update only, don't start server
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
UPDATE=true
RUN=true
for arg in "$@"; do
    case $arg in
        --no-update)
            UPDATE=false
            ;;
        --update)
            RUN=false
            ;;
        --help|-h)
            echo "OCI Log Analytics MCP Server"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-update  Skip checking for updates"
            echo "  --update     Update only, don't start server"
            echo "  --help, -h   Show this help message"
            echo ""
            exit 0
            ;;
    esac
done

# ============================================
# UPDATE SECTION
# ============================================
if [ "$UPDATE" = true ]; then
    echo "=============================================="
    echo "  Checking for updates..."
    echo "=============================================="

    # Check if this is a git repo
    if [ -d ".git" ]; then
        BRANCH="claude/restore-oci-analytics-ZxSQg"

        # Try to fetch updates
        if git fetch origin "$BRANCH" 2>/dev/null; then
            LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
            REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "unknown")

            if [ "$LOCAL" != "$REMOTE" ] && [ "$REMOTE" != "unknown" ]; then
                echo "Updates available. Pulling..."
                git pull origin "$BRANCH"

                echo ""
                echo "Reinstalling package..."
                source "$SCRIPT_DIR/venv/bin/activate"
                pip install -e . --quiet

                echo "Update complete!"
                echo ""
            else
                echo "Already up to date."
                echo ""
            fi
        else
            echo "Could not check for updates (offline or network error)."
            echo "Continuing with current version..."
            echo ""
        fi
    else
        echo "Not a git repository. Skipping update check."
        echo ""
    fi
fi

# ============================================
# VERIFY INSTALLATION
# ============================================
echo "Verifying installation..."

# Check for key fixes
FIXES_OK=true
if grep -q "_is_tenancy_ocid" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "  ✓ Tenancy subcompartments fix"
else
    echo "  ✗ Tenancy subcompartments fix MISSING"
    FIXES_OK=false
fi

if grep -q "include_subcompartments" "$SCRIPT_DIR/src/oci_la_mcp/oci_client/client.py" 2>/dev/null; then
    echo "  ✓ include_subcompartments parameter"
else
    echo "  ✗ include_subcompartments parameter MISSING"
    FIXES_OK=false
fi

if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "  ✓ Virtual environment"
else
    echo "  ✗ Virtual environment MISSING"
    FIXES_OK=false
fi

echo ""

# ============================================
# RUN SERVER
# ============================================
if [ "$RUN" = true ]; then
    if [ "$FIXES_OK" = false ]; then
        echo "WARNING: Some components are missing. Server may not work correctly."
        echo ""
    fi

    echo "=============================================="
    echo "  Starting OCI Log Analytics MCP Server"
    echo "=============================================="
    echo ""
    echo "Server is running. Press Ctrl+C to stop."
    echo ""

    # Activate virtual environment and run
    source "$SCRIPT_DIR/venv/bin/activate"

    # Run the MCP server
    exec python -m oci_la_mcp
else
    echo "Update complete. Run ./start.sh to start the server."
fi
