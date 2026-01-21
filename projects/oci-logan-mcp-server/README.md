# OCI Log Analytics MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude to query and analyze OCI Log Analytics data.

## Features

- **Query Execution**: Run Log Analytics queries with full syntax support
- **Scope Control**: Query your compartment or entire tenancy with `scope=tenancy`
- **Visualizations**: Generate pie, bar, line, and other chart types
- **Export**: Export results to CSV or JSON format
- **Schema Exploration**: List log sources, fields, entities, parsers, and labels
- **Helper Tools**: Connection testing, compartment lookup by name, query examples

## Quick Start

### Prerequisites

- Oracle Linux 9 (or compatible) VM
- OCI CLI configured with valid credentials (`~/.oci/config`)
- Python 3.10+

### Installation

```bash
# Clone and navigate to project
git clone <repo-url>
cd projects/oci-logan-mcp-server

# Run setup (installs dependencies, creates venv)
./setup_oel9.sh

# Configure the server
cp .env.example ~/.oci-la-mcp/.env
# Edit ~/.oci-la-mcp/.env with your settings
```

### Running the Server

```bash
# Start the server
./run.sh

# Or update and start
./update.sh
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "ssh",
      "args": ["-t", "user@your-vm", "cd /path/to/oci-logan-mcp-server && ./run.sh"]
    }
  }
}
```

## Available Tools

### Query Tools
| Tool | Description |
|------|-------------|
| `run_query` | Execute Log Analytics queries |
| `run_batch_queries` | Run multiple queries concurrently |
| `validate_query` | Validate query syntax before execution |
| `run_saved_search` | Execute saved searches by name or ID |

### Visualization & Export
| Tool | Description |
|------|-------------|
| `visualize` | Generate charts (pie, bar, line, area, table, treemap) |
| `export_results` | Export to CSV or JSON |

### Schema Exploration
| Tool | Description |
|------|-------------|
| `list_log_sources` | Available log sources |
| `list_fields` | Queryable fields |
| `list_entities` | Monitored entities |
| `list_parsers` | Log parsers |
| `list_labels` | Label definitions |
| `list_log_groups` | Log groups |
| `list_saved_searches` | Saved searches |

### Configuration
| Tool | Description |
|------|-------------|
| `get_current_context` | Show current namespace/compartment |
| `set_compartment` | Change compartment context |
| `set_namespace` | Change namespace |
| `list_compartments` | List accessible compartments |

### Helper Tools
| Tool | Description |
|------|-------------|
| `test_connection` | Health check - verify OCI connectivity |
| `find_compartment` | Look up compartment by name |
| `get_query_examples` | Get example queries by category |
| `get_log_summary` | See which log sources have data |

## Key Parameters

### Scope Parameter
Use `scope` to control query range:
- `scope: "default"` - Query your configured compartment
- `scope: "tenancy"` - Query ALL compartments across the tenancy

Example:
```
"Show me total logs across the entire tenancy"
→ Uses scope=tenancy automatically
```

### Time Range
- Relative: `last_15_min`, `last_1_hour`, `last_24_hours`, `last_7_days`, `last_30_days`
- Absolute: `time_start` and `time_end` in ISO 8601 format

## Testing

```bash
# Run automated test suite
source venv/bin/activate
python run_tests.py
```

See `TEST_PLAN.md` and `CLAUDE_DESKTOP_TESTS.md` for comprehensive test cases.

## Documentation

- `SETUP_GUIDE.md` - Detailed installation instructions
- `TEST_PLAN.md` - Full test plan with 60+ test cases
- `CLAUDE_DESKTOP_TESTS.md` - Copy-paste test prompts
- `docs/PRD.md` - Product requirements
- `docs/TDD.md` - Technical design

## License

MIT - See LICENSE file
