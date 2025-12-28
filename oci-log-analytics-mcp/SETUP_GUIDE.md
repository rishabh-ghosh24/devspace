# OCI Log Analytics MCP Server - Setup Guide for Oracle Enterprise Linux 9

This guide provides step-by-step instructions for setting up the OCI Log Analytics MCP Server on a fresh OEL9 VM.

## Quick Start (Automated)

For a fully automated setup, run:

```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/rishabh-ghosh24/devspace/main/oci-log-analytics-mcp/setup_oel9.sh | bash

# Or if you have the repo cloned:
cd oci-log-analytics-mcp
chmod +x setup_oel9.sh
./setup_oel9.sh
```

---

## Manual Setup Instructions

### Prerequisites

Before you begin, ensure you have:
- A fresh Oracle Enterprise Linux 9 VM
- Internet connectivity
- OCI account with Log Analytics enabled
- Your OCI credentials:
  - Tenancy OCID
  - User OCID
  - API Key (or will generate one)
  - Region identifier

---

### Step 1: Update System and Install Basic Tools

```bash
# Update system packages
sudo dnf update -y

# Install development tools
sudo dnf install -y git curl wget unzip tar gcc make \
    openssl-devel libffi-devel bzip2-devel readline-devel sqlite-devel
```

---

### Step 2: Install Python 3.9+

OEL9 comes with Python 3.9, but we recommend Python 3.11:

```bash
# Check current Python version
python3 --version

# If needed, install Python 3.11
sudo dnf install -y python3.11 python3.11-pip python3.11-devel

# Set Python 3.11 as default (optional)
sudo alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
python3 -m pip install --user --upgrade pip

# Install pipx (optional, for isolated tool installations)
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Add local bin to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

### Step 3: Install OCI CLI

```bash
# Install OCI CLI using the official installer
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults

# Add to PATH
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
oci --version
```

---

### Step 4: Configure OCI CLI

```bash
# Start the interactive configuration
oci setup config
```

You will be prompted for:
1. **Config file location**: Press Enter for default (`~/.oci/config`)
2. **User OCID**: Get from OCI Console → Identity → Users → Your User
3. **Tenancy OCID**: Get from OCI Console → Tenancy Details
4. **Region**: e.g., `us-phoenix-1`, `us-ashburn-1`, `eu-frankfurt-1`
5. **Generate API key**: Press `Y` to generate a new key pair

After setup, **upload the public key to OCI**:

```bash
# Display your public key
cat ~/.oci/oci_api_key_public.pem
```

1. Go to OCI Console → Identity → Users → Your User
2. Click "API Keys" → "Add API Key"
3. Choose "Paste Public Key"
4. Paste the public key content

**Test the connection**:

```bash
# This should list OCI regions
oci iam region list --output table
```

---

### Step 5: Clone/Download the MCP Server

```bash
# Option 1: Clone from repository
git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace/oci-log-analytics-mcp

# Option 2: If you have the files locally, copy them
# cp -r /path/to/oci-log-analytics-mcp ~/oci-log-analytics-mcp
# cd ~/oci-log-analytics-mcp
```

---

### Step 6: Create Virtual Environment and Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the MCP server
pip install -e .

# Install development dependencies (optional, for testing)
pip install -e ".[dev]"
```

---

### Step 7: Configure the MCP Server

#### Option A: Run the Setup Wizard

The first time you run the server, it will prompt for configuration:

```bash
oci-la-mcp
```

#### Option B: Create Configuration Manually

```bash
# Create configuration directory
mkdir -p ~/.oci-la-mcp/logs

# Create configuration file
cat > ~/.oci-la-mcp/config.yaml << 'EOF'
# OCI Authentication
oci:
  config_path: ~/.oci/config
  profile: DEFAULT
  auth_type: config_file

# Log Analytics Settings
log_analytics:
  namespace: YOUR_NAMESPACE       # Usually your tenancy name in lowercase
  default_compartment_id: ocid1.compartment.oc1..xxxxx  # Your compartment OCID

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
```

**To find your Log Analytics namespace**:

```bash
# Get your tenancy name (namespace is typically this in lowercase)
oci iam tenancy get --tenancy-id <your-tenancy-ocid> --query 'data.name' --raw-output
```

**To list compartments**:

```bash
oci iam compartment list --compartment-id-in-subtree true \
    --query 'data[*].{Name:name,OCID:id}' --output table
```

---

### Step 8: Test the Installation

```bash
# Activate the virtual environment (if not already active)
source venv/bin/activate

# Test Python imports
python3 -c "import oci_la_mcp; print(f'Version: {oci_la_mcp.__version__}')"

# Test OCI connection
python3 << 'EOF'
import oci
import yaml
from pathlib import Path

# Load configs
oci_config = oci.config.from_file()
mcp_config = yaml.safe_load(open(Path.home() / ".oci-la-mcp" / "config.yaml"))

# Test identity
identity = oci.identity.IdentityClient(oci_config)
tenancy = identity.get_tenancy(oci_config["tenancy"]).data
print(f"✓ Connected to tenancy: {tenancy.name}")

# Test Log Analytics
namespace = mcp_config["log_analytics"]["namespace"]
compartment = mcp_config["log_analytics"]["default_compartment_id"]
la = oci.log_analytics.LogAnalyticsClient(oci_config)
sources = la.list_sources(namespace_name=namespace, compartment_id=compartment, limit=3)
print(f"✓ Log Analytics: Found {len(sources.data.items)} sources")
print("✓ All tests passed!")
EOF

# Run unit tests
pytest tests/ -v
```

---

### Step 9: Run the MCP Server

```bash
# Activate environment
source venv/bin/activate

# Run the server (it communicates via stdio)
oci-la-mcp
```

The server will start and wait for MCP protocol messages on stdin.

---

## MCP Client Configuration

### For Claude Desktop

Create or edit the Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "/path/to/oci-log-analytics-mcp/venv/bin/oci-la-mcp",
      "args": []
    }
  }
}
```

### For Cline (VSCode)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "/path/to/oci-log-analytics-mcp/venv/bin/oci-la-mcp",
      "args": []
    }
  }
}
```

---

## Environment Variables (Optional Overrides)

You can override configuration using environment variables:

```bash
export OCI_LA_NAMESPACE="my-namespace"
export OCI_LA_COMPARTMENT="ocid1.compartment.oc1..xxxxx"
export OCI_CONFIG_PATH="~/.oci/config"
export OCI_CONFIG_PROFILE="DEFAULT"
export OCI_LA_AUTH_TYPE="config_file"
export OCI_LA_TIMEOUT="60"
export OCI_LA_LOG_LEVEL="INFO"
```

---

## Troubleshooting

### "OCI CLI not found"

```bash
# Add to PATH
export PATH="$HOME/bin:$PATH"

# Or reinstall
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

### "Authentication failed"

1. Verify your API key is uploaded to OCI Console
2. Check fingerprint matches: `grep fingerprint ~/.oci/config`
3. Test with: `oci iam region list`

### "Namespace not found"

1. Ensure Log Analytics is enabled in your tenancy
2. Verify the namespace name (usually tenancy name in lowercase)
3. Check compartment permissions

### "ModuleNotFoundError"

```bash
# Ensure virtual environment is activated
source /path/to/oci-log-analytics-mcp/venv/bin/activate

# Reinstall dependencies
pip install -e .
```

### View server logs

```bash
# Query logs are saved here
cat ~/.oci-la-mcp/logs/queries.log
```

---

## Quick Reference

| Item | Location |
|------|----------|
| MCP Server | `~/oci-log-analytics-mcp/` |
| Virtual Environment | `~/oci-log-analytics-mcp/venv/` |
| MCP Config | `~/.oci-la-mcp/config.yaml` |
| Query Logs | `~/.oci-la-mcp/logs/queries.log` |
| OCI Config | `~/.oci/config` |
| OCI API Keys | `~/.oci/oci_api_key.pem` |

---

## Next Steps

Once setup is complete, you can:

1. **Test queries** in Claude Desktop or Cline:
   - "What log sources are available?"
   - "Show me errors from the last hour"
   - "Create a pie chart of errors by source"

2. **Explore the schema**:
   - "List all fields in the Linux Syslog source"
   - "What entities are being monitored?"

3. **Run specific queries**:
   - "Run query: * | stats count by 'Log Source'"
   - "Search for 'error' in the last 24 hours"

---

## Support

- [OCI Log Analytics Documentation](https://docs.oracle.com/en-us/iaas/log-analytics/index.html)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [OCI CLI Documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm)
