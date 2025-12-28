#!/bin/bash
#
# OCI Log Analytics MCP Server - Setup Script for Oracle Enterprise Linux 9
#
# This script installs all prerequisites and sets up the MCP server.
# Run with: bash setup_oel9.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo ""
echo "============================================================"
echo "  OCI Log Analytics MCP Server - Setup Script"
echo "  For Oracle Enterprise Linux 9"
echo "============================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warning "Running as root. Will create user-level configurations."
    SUDO=""
else
    SUDO="sudo"
fi

# ============================================================
# STEP 1: System Updates and Basic Tools
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 1: System Updates and Basic Tools"
echo "============================================================"

log_info "Updating system packages..."
$SUDO dnf update -y

log_info "Installing basic development tools..."
$SUDO dnf install -y \
    git \
    curl \
    wget \
    unzip \
    tar \
    gcc \
    make \
    openssl-devel \
    libffi-devel \
    bzip2-devel \
    readline-devel \
    sqlite-devel

log_success "Basic tools installed."

# ============================================================
# STEP 2: Python Installation
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 2: Python Installation"
echo "============================================================"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "0.0.0")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

log_info "Current Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    log_success "Python $PYTHON_VERSION is sufficient (>= 3.9 required)."
else
    log_info "Installing Python 3.11..."
    $SUDO dnf install -y python3.11 python3.11-pip python3.11-devel

    # Set as default alternatives (optional)
    $SUDO alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

    log_success "Python 3.11 installed."
fi

# Ensure pip is up to date
log_info "Upgrading pip..."
python3 -m pip install --user --upgrade pip

# Install pipx for isolated tool installations
log_info "Installing pipx..."
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Add to current PATH
export PATH="$HOME/.local/bin:$PATH"

log_success "Python setup complete."

# ============================================================
# STEP 3: OCI CLI Installation
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 3: OCI CLI Installation"
echo "============================================================"

if command -v oci &> /dev/null; then
    OCI_VERSION=$(oci --version 2>/dev/null || echo "unknown")
    log_info "OCI CLI already installed: $OCI_VERSION"
else
    log_info "Installing OCI CLI..."

    # Option 1: Using the official installer script
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults

    # Add to PATH
    export PATH="$HOME/bin:$PATH"

    log_success "OCI CLI installed."
fi

# Verify OCI CLI
if command -v oci &> /dev/null; then
    log_success "OCI CLI is available: $(oci --version)"
else
    log_warning "OCI CLI not in PATH. You may need to restart your shell or add ~/bin to PATH."
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi

# ============================================================
# STEP 4: OCI Configuration
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 4: OCI Configuration"
echo "============================================================"

if [ -f ~/.oci/config ]; then
    log_info "OCI config file found at ~/.oci/config"
    echo ""
    echo "Current profiles:"
    grep '^\[' ~/.oci/config || true
    echo ""
    read -p "Do you want to reconfigure OCI? (y/N): " RECONFIG
    if [[ "$RECONFIG" =~ ^[Yy]$ ]]; then
        oci setup config
    fi
else
    log_info "No OCI configuration found. Starting OCI setup..."
    echo ""
    echo "You will need:"
    echo "  1. Your OCI Tenancy OCID"
    echo "  2. Your User OCID"
    echo "  3. Your region (e.g., us-phoenix-1)"
    echo "  4. A new API key will be generated"
    echo ""
    read -p "Press Enter to continue with OCI setup..."

    oci setup config

    echo ""
    log_warning "IMPORTANT: You need to upload the public key to OCI Console!"
    echo ""
    echo "1. Go to OCI Console -> Identity -> Users -> Your User"
    echo "2. Click 'API Keys' -> 'Add API Key'"
    echo "3. Choose 'Paste Public Key' and paste the contents of:"
    echo "   ~/.oci/oci_api_key_public.pem"
    echo ""
    echo "Public key content:"
    echo "-------------------"
    cat ~/.oci/oci_api_key_public.pem
    echo "-------------------"
    echo ""
    read -p "Press Enter after you've uploaded the public key to OCI..."
fi

# Test OCI connection
log_info "Testing OCI connection..."
if oci iam region list --output table 2>/dev/null | head -5; then
    log_success "OCI CLI is working correctly!"
else
    log_error "OCI CLI test failed. Please check your configuration."
    echo "Try running: oci iam region list"
fi

# ============================================================
# STEP 5: Clone/Setup the MCP Server
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 5: Setup MCP Server"
echo "============================================================"

# Determine installation directory
INSTALL_DIR="$HOME/oci-log-analytics-mcp"

if [ -d "$INSTALL_DIR" ]; then
    log_info "Directory $INSTALL_DIR already exists."
    read -p "Remove and reinstall? (y/N): " REINSTALL
    if [[ "$REINSTALL" =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        log_info "Keeping existing installation."
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Creating MCP server directory..."
    mkdir -p "$INSTALL_DIR"

    # Check if we're in a git repo with the MCP server
    if [ -d "./oci-log-analytics-mcp" ]; then
        log_info "Copying from local directory..."
        cp -r ./oci-log-analytics-mcp/* "$INSTALL_DIR/"
    else
        log_info "Cloning from repository..."
        # You can change this URL to your actual repository
        git clone https://github.com/rishabh-ghosh24/devspace.git /tmp/devspace-clone
        if [ -d "/tmp/devspace-clone/oci-log-analytics-mcp" ]; then
            cp -r /tmp/devspace-clone/oci-log-analytics-mcp/* "$INSTALL_DIR/"
            rm -rf /tmp/devspace-clone
        else
            log_error "MCP server not found in repository."
            exit 1
        fi
    fi
fi

log_success "MCP Server files ready at $INSTALL_DIR"

# ============================================================
# STEP 6: Install Python Dependencies
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 6: Install Python Dependencies"
echo "============================================================"

cd "$INSTALL_DIR"

log_info "Creating virtual environment..."
python3 -m venv venv

log_info "Activating virtual environment..."
source venv/bin/activate

log_info "Upgrading pip in virtual environment..."
pip install --upgrade pip

log_info "Installing MCP server and dependencies..."
pip install -e .

# Install dev dependencies for testing
log_info "Installing development dependencies..."
pip install -e ".[dev]"

log_success "All dependencies installed."

# ============================================================
# STEP 7: Configure MCP Server
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 7: Configure MCP Server"
echo "============================================================"

# Get Log Analytics namespace
log_info "Fetching your Log Analytics namespace..."

# Get tenancy OCID from OCI config
TENANCY_OCID=$(grep 'tenancy' ~/.oci/config | head -1 | cut -d'=' -f2 | tr -d ' ')

if [ -n "$TENANCY_OCID" ]; then
    # Get tenancy name
    TENANCY_NAME=$(oci iam tenancy get --tenancy-id "$TENANCY_OCID" --query 'data.name' --raw-output 2>/dev/null || echo "")

    if [ -n "$TENANCY_NAME" ]; then
        # Namespace is typically the tenancy name in lowercase
        NAMESPACE=$(echo "$TENANCY_NAME" | tr '[:upper:]' '[:lower:]' | tr -d ' ')
        log_info "Detected namespace: $NAMESPACE"
    fi
fi

# Get compartment
log_info "Fetching compartments..."
echo ""
echo "Available compartments:"
oci iam compartment list --compartment-id-in-subtree true --query 'data[*].{Name:name,OCID:id}' --output table 2>/dev/null | head -20 || true
echo ""

read -p "Enter the compartment OCID to use (or press Enter to use root): " COMPARTMENT_OCID

if [ -z "$COMPARTMENT_OCID" ]; then
    COMPARTMENT_OCID="$TENANCY_OCID"
    log_info "Using root compartment."
fi

# Create MCP configuration directory
mkdir -p ~/.oci-la-mcp/logs

# Create configuration file
log_info "Creating MCP server configuration..."
cat > ~/.oci-la-mcp/config.yaml << EOF
# OCI Log Analytics MCP Server Configuration
# Generated by setup script

# OCI Authentication
oci:
  config_path: ~/.oci/config
  profile: DEFAULT
  auth_type: config_file

# Log Analytics Settings
log_analytics:
  namespace: ${NAMESPACE:-"your-namespace"}
  default_compartment_id: ${COMPARTMENT_OCID}

# Query Defaults
query:
  default_time_range: last_1_hour
  max_results: 1000
  timeout_seconds: 60

# Caching
cache:
  enabled: true
  query_ttl_minutes: 5
  schema_ttl_minutes: 15

# Logging
logging:
  query_logging: true
  log_path: ~/.oci-la-mcp/logs
  log_level: INFO

# Guardrails
guardrails:
  max_time_range_days: 7
  warn_on_large_results: true
  large_result_threshold: 10000
EOF

log_success "Configuration saved to ~/.oci-la-mcp/config.yaml"

# ============================================================
# STEP 8: Create Helper Scripts
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 8: Create Helper Scripts"
echo "============================================================"

# Create activation script
cat > "$INSTALL_DIR/activate.sh" << 'EOF'
#!/bin/bash
# Activate the MCP server virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
export PATH="$SCRIPT_DIR/venv/bin:$PATH"
echo "MCP Server environment activated."
echo "Run 'oci-la-mcp' to start the server."
EOF
chmod +x "$INSTALL_DIR/activate.sh"

# Create run script
cat > "$INSTALL_DIR/run.sh" << 'EOF'
#!/bin/bash
# Run the MCP server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
exec oci-la-mcp "$@"
EOF
chmod +x "$INSTALL_DIR/run.sh"

# Create test script
cat > "$INSTALL_DIR/test_connection.sh" << 'EOF'
#!/bin/bash
# Test the OCI Log Analytics connection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"

echo "Testing OCI Log Analytics connection..."
echo ""

python3 << 'PYTHON'
import sys
try:
    import oci
    from pathlib import Path
    import yaml

    # Load config
    config_path = Path.home() / ".oci-la-mcp" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            mcp_config = yaml.safe_load(f)
        print(f"✓ MCP config loaded from {config_path}")
    else:
        print(f"✗ MCP config not found at {config_path}")
        sys.exit(1)

    # Load OCI config
    oci_config = oci.config.from_file()
    print("✓ OCI config loaded")

    # Test identity
    identity = oci.identity.IdentityClient(oci_config)
    tenancy = identity.get_tenancy(oci_config["tenancy"]).data
    print(f"✓ Connected to tenancy: {tenancy.name}")

    # Test Log Analytics
    namespace = mcp_config.get("log_analytics", {}).get("namespace", "")
    compartment = mcp_config.get("log_analytics", {}).get("default_compartment_id", "")

    la_client = oci.log_analytics.LogAnalyticsClient(oci_config)

    # Try to list log sources
    sources = la_client.list_sources(
        namespace_name=namespace,
        compartment_id=compartment,
        limit=5
    )
    print(f"✓ Log Analytics connected (namespace: {namespace})")
    print(f"  Found {len(sources.data.items)} log sources")

    print("")
    print("All tests passed! MCP Server is ready to use.")

except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
PYTHON
EOF
chmod +x "$INSTALL_DIR/test_connection.sh"

log_success "Helper scripts created."

# ============================================================
# STEP 9: Test Installation
# ============================================================
echo ""
echo "============================================================"
echo "  STEP 9: Test Installation"
echo "============================================================"

log_info "Running installation tests..."

# Test Python imports
source "$INSTALL_DIR/venv/bin/activate"
python3 -c "
import oci_la_mcp
print(f'✓ oci_la_mcp version: {oci_la_mcp.__version__}')
" || log_error "Failed to import oci_la_mcp"

# Check if command is available
if command -v oci-la-mcp &> /dev/null; then
    log_success "oci-la-mcp command is available"
else
    log_warning "oci-la-mcp not in PATH. Use $INSTALL_DIR/run.sh to run the server."
fi

# ============================================================
# STEP 10: Final Instructions
# ============================================================
echo ""
echo "============================================================"
echo "  SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Installation Summary:"
echo "  • MCP Server installed at: $INSTALL_DIR"
echo "  • Configuration file: ~/.oci-la-mcp/config.yaml"
echo "  • Logs directory: ~/.oci-la-mcp/logs/"
echo ""
echo "Quick Start Commands:"
echo ""
echo "  1. Test the connection:"
echo "     $INSTALL_DIR/test_connection.sh"
echo ""
echo "  2. Run the MCP server:"
echo "     $INSTALL_DIR/run.sh"
echo ""
echo "  3. Activate the environment manually:"
echo "     source $INSTALL_DIR/activate.sh"
echo ""
echo "  4. Run tests:"
echo "     cd $INSTALL_DIR && source venv/bin/activate && pytest"
echo ""
echo "MCP Client Configuration:"
echo ""
echo "For Claude Desktop (add to claude_desktop_config.json):"
echo '  {'
echo '    "mcpServers": {'
echo '      "oci-log-analytics": {'
echo "        \"command\": \"$INSTALL_DIR/run.sh\""
echo '      }'
echo '    }'
echo '  }'
echo ""
echo "============================================================"
echo ""

# Add to PATH permanently (optional)
read -p "Add MCP server to PATH in ~/.bashrc? (y/N): " ADD_PATH
if [[ "$ADD_PATH" =~ ^[Yy]$ ]]; then
    echo "" >> ~/.bashrc
    echo "# OCI Log Analytics MCP Server" >> ~/.bashrc
    echo "export PATH=\"$INSTALL_DIR/venv/bin:\$PATH\"" >> ~/.bashrc
    echo "alias oci-la-mcp-activate='source $INSTALL_DIR/activate.sh'" >> ~/.bashrc
    log_success "Added to ~/.bashrc. Run 'source ~/.bashrc' or restart your shell."
fi

echo ""
log_success "Setup complete! Happy querying!"
