#!/bin/bash
# ---------------------------------------------------------------------------
# install-otel-apache.sh — Install OpenTelemetry module for Apache httpd
#
# This installs the otel-webserver-module so Apache appears as its own
# service ("stayeasy-webserver") in OCI APM traces and injects traceparent
# headers when proxying to the Quart backend.
#
# Run as root on pyapp1 (OEL 9).
# ---------------------------------------------------------------------------

set -euo pipefail

INSTALL_DIR="/opt/opentelemetry-webserver-sdk"
DOWNLOAD_URL="https://github.com/open-telemetry/opentelemetry-cpp-contrib/releases/download/webserver/v1.1.0/opentelemetry-webserver-sdk-x64-linux.tgz"
TGZ_FILE="/tmp/opentelemetry-webserver-sdk-x64-linux.tgz"

echo "=== OpenTelemetry Apache Module Installer ==="

# 1. Download
if [ ! -f "$TGZ_FILE" ]; then
    echo "Downloading otel-webserver-module v1.1.0..."
    curl -fSL "$DOWNLOAD_URL" -o "$TGZ_FILE"
else
    echo "Using cached download: $TGZ_FILE"
fi

# 2. Extract
echo "Extracting to $INSTALL_DIR..."
sudo mkdir -p "$INSTALL_DIR"
sudo tar -xzf "$TGZ_FILE" -C /opt/

# 3. Run the bundled install script (sets up shared libs)
echo "Running SDK install script..."
cd "$INSTALL_DIR"
sudo ./install.sh

# 4. Verify the module is loadable
echo ""
echo "Verifying module..."
if httpd -M 2>/dev/null | grep -q otel_apache_module; then
    echo "  ✓ otel_apache_module loaded successfully"
else
    echo "  Module not auto-loaded yet — will load after config is placed and Apache restarted"
fi

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /etc/httpd/conf.d/opentelemetry_module.conf"
echo "     - Set ApacheModuleOtelExporterEndpoint to your OCI APM OTLP endpoint"
echo "  2. sudo systemctl restart httpd"
echo "  3. Verify: httpd -M | grep otel"
