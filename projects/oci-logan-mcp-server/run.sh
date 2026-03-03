#!/bin/bash
#
# OCI Log Analytics MCP Server - Run
#
# Just starts the server (no update check)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "  OCI Log Analytics MCP Server"
echo "=============================================="
echo ""
echo "Server is running. Press Ctrl+C to stop."
echo ""

source "$SCRIPT_DIR/venv/bin/activate"
exec python -m oci_la_mcp
