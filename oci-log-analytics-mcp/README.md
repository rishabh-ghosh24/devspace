# OCI Log Analytics MCP Server

A Model Context Protocol (MCP) server that enables natural language interaction with Oracle Cloud Infrastructure (OCI) Log Analytics. Query your logs, generate visualizations, and get insights using conversational AI.

## Features

- **Natural Language Queries**: Ask questions about your logs in plain English
- **Query Validation**: Intelligent validation with suggestions and fuzzy field matching
- **Visualizations**: Generate charts (pie, bar, line, area, etc.) inline in your chat
- **Schema Exploration**: Discover log sources, fields, entities, and parsers
- **Saved Searches**: Execute pre-defined searches by name
- **Export**: Export results to CSV or JSON
- **Multi-tenancy**: Switch between namespaces and compartments
- **Caching**: Smart caching for faster follow-up queries
- **Rate Limiting**: Automatic handling of OCI API rate limits

## Prerequisites

- Python 3.9 or higher
- OCI account with Log Analytics enabled
- OCI CLI configured (`~/.oci/config`) or Instance/Resource Principal access
- An MCP-compatible client:
  - [Claude Desktop](https://claude.ai/desktop)
  - [Cline](https://github.com/cline/cline) (VSCode extension)
  - [Cursor](https://cursor.sh/)

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/oci-log-analytics-mcp.git
cd oci-log-analytics-mcp

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### From PyPI (when published)

```bash
pip install oci-log-analytics-mcp
```

## Configuration

### First-Run Setup

On first run, the server will guide you through configuration:

```bash
oci-la-mcp
```

This will:
1. Locate your OCI config file
2. Select authentication method
3. Discover your Log Analytics namespace
4. Choose default compartment

### Manual Configuration

Create `~/.oci-la-mcp/config.yaml`:

```yaml
# OCI Authentication
oci:
  config_path: ~/.oci/config
  profile: DEFAULT
  auth_type: config_file  # or instance_principal, resource_principal

# Log Analytics Settings
log_analytics:
  namespace: your-namespace
  default_compartment_id: ocid1.compartment.oc1..xxxxx

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
```

### Environment Variables

Override any setting with environment variables:

| Variable | Description |
|----------|-------------|
| `OCI_LA_MCP_CONFIG` | Path to config file |
| `OCI_LA_NAMESPACE` | Log Analytics namespace |
| `OCI_LA_COMPARTMENT` | Default compartment OCID |
| `OCI_CONFIG_PATH` | Path to OCI config file |
| `OCI_CONFIG_PROFILE` | OCI config profile name |
| `OCI_LA_AUTH_TYPE` | Auth type: config_file, instance_principal, resource_principal |
| `OCI_LA_TIMEOUT` | Query timeout in seconds |
| `OCI_LA_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING, ERROR |

## MCP Client Setup

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "oci-la-mcp",
      "args": []
    }
  }
}
```

### Cline (VSCode)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "oci-la-mcp",
      "args": []
    }
  }
}
```

### Cursor

Add to Cursor's MCP configuration following their documentation.

## Usage Examples

Once connected, you can interact naturally:

### Finding Errors

```
"Are there any errors in the last hour?"
"Show me critical errors from the database logs"
"What are the top 10 error messages?"
```

### Exploring Data

```
"What log sources are available?"
"Show me the fields in the Linux Syslog source"
"List all monitored hosts"
```

### Visualizations

```
"Create a pie chart of errors by source"
"Show me the error trend over the last 24 hours"
"Generate a bar chart of top hosts by log volume"
```

### Specific Queries

```
"Run the query: 'Error' | stats count by 'Host Name'"
"Show me logs from host prod-server-01 in the last 30 minutes"
"Count logs by severity level"
```

### Comparisons

```
"Compare error rates between production and staging"
"Show me log volume by source for the last 7 days"
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_log_sources` | List available log sources |
| `list_fields` | List fields with types and hints |
| `list_entities` | List monitored entities |
| `list_parsers` | List available parsers |
| `list_labels` | List label definitions |
| `list_saved_searches` | List saved searches |
| `list_log_groups` | List log groups |
| `validate_query` | Validate query before execution |
| `run_query` | Execute a Log Analytics query |
| `run_saved_search` | Run a saved search by name |
| `run_batch_queries` | Run multiple queries at once |
| `visualize` | Generate a chart from query results |
| `export_results` | Export to CSV or JSON |
| `set_compartment` | Change compartment context |
| `set_namespace` | Change namespace context |
| `get_current_context` | Get current settings |
| `list_compartments` | List available compartments |

## Query Syntax

Log Analytics uses a pipe-based query language:

```
# Search for errors
'Error' or 'Critical'

# Count by field
'Error' | stats count by 'Log Source'

# Trend over time
'Error' | timestats count span=1hour

# Filter and select fields
'Severity' = 'Error' | fields 'Time', 'Host Name', 'Message' | head 100

# Top N
* | stats count by 'Host Name' | sort -count | head 10
```

## Architecture

```
+----------------------------------------------------------+
|                    MCP Clients                           |
|  (Claude Desktop / Cline / Cursor)                       |
+-------------------------+--------------------------------+
                          | MCP Protocol (stdio)
+-------------------------v--------------------------------+
|              OCI Log Analytics MCP Server                |
|  +----------------------------------------------------+  |
|  |                  MCP Layer                         |  |
|  |  Tools | Resources | Protocol Handler              |  |
|  +----------------------------------------------------+  |
|  +----------------------------------------------------+  |
|  |               Core Services                        |  |
|  |  Query Engine | Schema Manager | Validator         |  |
|  |  Visualization | Export                            |  |
|  +----------------------------------------------------+  |
|  +----------------------------------------------------+  |
|  |            Infrastructure Layer                    |  |
|  |  OCI Client | Cache | Rate Limiter | Logger        |  |
|  +----------------------------------------------------+  |
+-------------------------+--------------------------------+
                          | HTTPS (OCI SDK)
+-------------------------v--------------------------------+
|           OCI Log Analytics Service                      |
+----------------------------------------------------------+
```

## Development

### Setup

```bash
# Clone and install
git clone https://github.com/your-org/oci-log-analytics-mcp.git
cd oci-log-analytics-mcp
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/

# Type checking
mypy src/
```

### Project Structure

```
oci-log-analytics-mcp/
├── src/oci_la_mcp/
│   ├── config/          # Configuration management
│   ├── oci_client/      # OCI SDK wrapper
│   ├── services/        # Core business logic
│   ├── mcp/             # MCP protocol layer
│   ├── cache/           # Caching
│   ├── logging/         # Query logging
│   ├── templates/       # Query templates
│   ├── utils/           # Utilities
│   └── server.py        # Main entry point
├── tests/               # Test suite
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

## Troubleshooting

### Authentication Errors

1. Verify OCI CLI is configured: `oci iam user list --auth security_token`
2. Check config file permissions: `chmod 600 ~/.oci/config`
3. Ensure API key is valid and not expired

### Connection Issues

1. Verify network connectivity to OCI
2. Check if Log Analytics is enabled in your tenancy
3. Verify compartment permissions

### Query Errors

1. Use `validate_query` before running complex queries
2. Check field names with `list_fields`
3. Review the syntax guide in resources

### Performance

1. Add filters to reduce result set
2. Use appropriate time ranges
3. Enable caching in configuration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Links

- [OCI Log Analytics Documentation](https://docs.oracle.com/en-us/iaas/log-analytics/index.html)
- [Log Analytics Query Reference](https://docs.oracle.com/en-us/iaas/log-analytics/doc/command-reference.html)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [OCI Python SDK](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
