# Technical Design Document (TDD)
# OCI Log Analytics MCP Server

**Version:** 1.0
**Date:** December 28, 2025
**Author:** PresalesAI
**Status:** Draft

---

## 1. System Overview

### 1.1 Architecture Diagram

```
+-----------------------------------------------------------------------------+
|                              MCP Clients                                    |
|  +-----------+  +-----------+  +-----------+  +-----------+                 |
|  |   Claude  |  |   Cline   |  |   Cursor  |  |   Other   |                 |
|  |   Desktop |  |  (VSCode) |  |           |  | MCP Client|                 |
|  +-----+-----+  +-----+-----+  +-----+-----+  +-----+-----+                 |
|        |              |              |              |                       |
|        +--------------+--------------+--------------+                       |
|                                |                                            |
|                                | MCP Protocol (stdio/SSE)                   |
|                                v                                            |
|  +----------------------------------------------------------------------+   |
|  |                      OCI Log Analytics MCP Server                     |  |
|  |  +----------------------------------------------------------------+  |   |
|  |  |                        MCP Layer                               |  |   |
|  |  |  +-----------+  +-----------+  +---------------------+         |  |   |
|  |  |  | Resources |  |   Tools   |  |  Protocol Handler   |         |  |   |
|  |  |  +-----------+  +-----------+  +---------------------+         |  |   |
|  |  +----------------------------------------------------------------+  |   |
|  |                                |                                     |   |
|  |  +----------------------------------------------------------------+  |   |
|  |  |                      Core Services                             |  |   |
|  |  |  +--------+ +--------+ +--------+ +------------------+         |  |   |
|  |  |  | Query  | | Schema | | Visual | | Query Validator  |         |  |   |
|  |  |  | Engine | |Manager | | Engine | | & Intelligence   |         |  |   |
|  |  |  +--------+ +--------+ +--------+ +------------------+         |  |   |
|  |  +----------------------------------------------------------------+  |   |
|  |                                |                                     |   |
|  |  +----------------------------------------------------------------+  |   |
|  |  |                   Infrastructure Layer                         |  |   |
|  |  |  +--------+ +--------+ +--------+ +------------------+         |  |   |
|  |  |  |  OCI   | | Cache  | | Config | |  Query Logger    |         |  |   |
|  |  |  | Client | |Manager | |Manager | |                  |         |  |   |
|  |  |  +--------+ +--------+ +--------+ +------------------+         |  |   |
|  |  +----------------------------------------------------------------+  |   |
|  +----------------------------------------------------------------------+   |
|                                   |                                         |
+-----------------------------------|-----------------------------------------+
                                    |
                                    | HTTPS (OCI SDK)
                                    v
+-----------------------------------------------------------------------------+
|                           Oracle Cloud Infrastructure                        |
|  +----------------------------------------------------------------------+   |
|  |                        Log Analytics Service                         |   |
|  |  +--------+ +--------+ +--------+ +--------+ +--------+              |   |
|  |  | Query  | | Schema | | Saved  | | Entity | | Parser |              |   |
|  |  |  API   | |  API   | |Searches| |  API   | |  API   |              |   |
|  |  +--------+ +--------+ +--------+ +--------+ +--------+              |   |
|  +----------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------+
```

### 1.2 Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Runtime | Python | 3.9+ |
| MCP Protocol | mcp Python SDK | >= 0.9.0 |
| OCI Integration | oci Python SDK | >= 2.90.0 |
| Visualization | matplotlib, seaborn | >= 3.7.0 |
| Data Processing | pandas | >= 2.0.0 |
| Configuration | PyYAML | >= 6.0 |
| Image Processing | Pillow | >= 10.0.0 |
| Async Support | asyncio | stdlib |
| Fuzzy Matching | rapidfuzz | >= 3.0.0 |

---

## 2. Project Structure

```
oci-log-analytics-mcp/
├── docs/
│   ├── PRD.md
│   └── TDD.md
├── src/
│   └── oci_la_mcp/
│       ├── __init__.py
│       ├── server.py                 # MCP server entry point
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py           # Configuration dataclasses
│       │   ├── loader.py             # Config file & env loading
│       │   └── wizard.py             # First-run setup wizard
│       ├── oci_client/
│       │   ├── __init__.py
│       │   ├── auth.py               # Authentication handlers
│       │   ├── client.py             # OCI client wrapper
│       │   └── rate_limiter.py       # Rate limiting & backoff
│       ├── services/
│       │   ├── __init__.py
│       │   ├── query_engine.py       # Query execution
│       │   ├── schema_manager.py     # Schema exploration
│       │   ├── visualization.py      # Chart generation
│       │   ├── query_validator.py    # Validation & intelligence
│       │   ├── saved_search.py       # Saved search operations
│       │   └── export.py             # CSV/JSON export
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── tools.py              # MCP tool definitions
│       │   ├── resources.py          # MCP resource definitions
│       │   └── handlers.py           # Request handlers
│       ├── cache/
│       │   ├── __init__.py
│       │   └── manager.py            # In-memory cache
│       ├── logging/
│       │   ├── __init__.py
│       │   └── query_logger.py       # Query audit logging
│       ├── templates/
│       │   └── query_templates.yaml  # Query pattern templates
│       └── utils/
│           ├── __init__.py
│           ├── time_parser.py        # Time range parsing
│           └── fuzzy_match.py        # Field name matching
├── tests/
│   ├── __init__.py
│   ├── test_query_engine.py
│   ├── test_schema_manager.py
│   ├── test_visualization.py
│   ├── test_query_validator.py
│   └── test_config.py
├── pyproject.toml
├── README.md
├── LICENSE
└── .env.example
```

---

## 3. Component Design

### 3.1 Configuration Manager

#### 3.1.1 Settings Dataclass

```python
# src/oci_la_mcp/config/settings.py

from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path

@dataclass
class OCIConfig:
    config_path: Path = Path.home() / ".oci" / "config"
    profile: str = "DEFAULT"
    auth_type: Literal["config_file", "instance_principal", "resource_principal"] = "config_file"

@dataclass
class LogAnalyticsConfig:
    namespace: str = ""
    default_compartment_id: str = ""
    default_log_group_id: Optional[str] = None

@dataclass
class QueryConfig:
    default_time_range: str = "last_1_hour"
    max_results: int = 1000
    timeout_seconds: int = 60

@dataclass
class CacheConfig:
    enabled: bool = True
    query_ttl_minutes: int = 5
    schema_ttl_minutes: int = 15

@dataclass
class LoggingConfig:
    query_logging: bool = True
    log_path: Path = Path.home() / ".oci-la-mcp" / "logs"
    log_level: str = "INFO"

@dataclass
class GuardrailsConfig:
    max_time_range_days: int = 7
    warn_on_large_results: bool = True
    large_result_threshold: int = 10000

@dataclass
class Settings:
    oci: OCIConfig = field(default_factory=OCIConfig)
    log_analytics: LogAnalyticsConfig = field(default_factory=LogAnalyticsConfig)
    query: QueryConfig = field(default_factory=QueryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    guardrails: GuardrailsConfig = field(default_factory=GuardrailsConfig)
```

---

## 4. Data Flow Diagrams

### 4.1 Query Execution Flow

```
+------------------------------------------------------------------------------+
|                            Query Execution Flow                              |
+------------------------------------------------------------------------------+

+---------+     +---------+     +-------------+     +-----------+
|   AI    |---->|  MCP    |---->|   Query     |---->|   Query   |
|  Model  |     | Server  |     |  Validator  |     |  Engine   |
+---------+     +---------+     +-------------+     +-----------+
                                      |                   |
                                      v                   v
                                +-----------+     +-----------+
                                |  Schema   |     |   Cache   |
                                |  Manager  |     |  Manager  |
                                +-----------+     +-----------+
                                                        |
                                                        | Cache miss
                                                        v
                                                  +-----------+
                                                  |    OCI    |
                                                  |  Client   |
                                                  +-----------+
                                                        |
                                                        v
                                                  +-----------+
                                                  |  Rate     |
                                                  |  Limiter  |
                                                  +-----------+
                                                        |
                                                        v
                                                  +-----------+
                                                  |  OCI Log  |
                                                  | Analytics |
                                                  |   API     |
                                                  +-----------+
```

### 4.2 Visualization Flow

```
+------------------------------------------------------------------------------+
|                           Visualization Flow                                 |
+------------------------------------------------------------------------------+

+---------+     +-------------+     +-------------+     +---------------+
| AI asks |---->| run_query() |---->|  visualize  |---->|  Matplotlib   |
|visualize|     |             |     |   engine    |     |  generates    |
+---------+     +-------------+     +-------------+     |    chart      |
                      |                                  +---------------+
                      v                                         |
                +-------------+                                 v
                |  Query      |                         +---------------+
                |  Results    |                         |  Base64 PNG   |
                +-------------+                         |  + Raw Data   |
                                                        +---------------+
                                                               |
                                                               v
                                                        +---------------+
                                                        | ImageContent  |
                                                        | + TextContent |
                                                        |   returned    |
                                                        +---------------+
```

---

## 5. Error Handling Strategy

### 5.1 Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| **Authentication** | Invalid credentials, expired token | Clear message, prompt reconfiguration |
| **Validation** | Invalid field, syntax error | Suggestions, fuzzy matches, example fix |
| **Rate Limiting** | 429 response | Exponential backoff, retry |
| **Timeout** | Query takes too long | Configurable timeout, cancel option |
| **Not Found** | Entity, source doesn't exist | List available options |
| **Permission** | Insufficient privileges | Clear error, required permissions |

### 5.2 Error Response Format

```python
@dataclass
class MCPError:
    code: str           # e.g., "FIELD_NOT_FOUND"
    message: str        # Human-readable message
    details: dict       # Additional context
    suggestions: list   # Actionable suggestions
    example_fix: str    # Optional corrected query/command
```

---

## 6. Security Considerations

### 6.1 Credential Handling

- Credentials never logged or returned in responses
- Config file permissions checked on startup (warn if world-readable)
- Environment variables preferred for CI/CD

### 6.2 Query Logging

- Queries logged locally only
- No sensitive data in logs (field values truncated)
- Log rotation to prevent unbounded growth

### 6.3 Network Security

- All OCI communication over HTTPS
- No external services contacted (except OCI APIs)
- No telemetry or analytics

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Component | Test Focus |
|-----------|------------|
| QueryValidator | Syntax validation, fuzzy matching |
| TimeParser | Time range parsing |
| CacheManager | TTL, eviction |
| RateLimiter | Backoff calculation |

### 7.2 Integration Tests

| Test | Description |
|------|-------------|
| Query execution | End-to-end query with mock OCI |
| Visualization | Chart generation from sample data |
| Config loading | File + env var override |

### 7.3 Test Fixtures

Mock OCI responses for:
- Log sources
- Fields
- Entities
- Query results

---

## 8. Deployment

### 8.1 Package Structure

```toml
# pyproject.toml
[project]
name = "oci-log-analytics-mcp"
version = "1.0.0"
description = "MCP Server for OCI Log Analytics"
requires-python = ">=3.9"
dependencies = [
    "mcp>=0.9.0",
    "oci>=2.90.0",
    "matplotlib>=3.7.0",
    "pandas>=2.0.0",
    "pyyaml>=6.0",
    "pillow>=10.0.0",
    "rapidfuzz>=3.0.0"
]

[project.scripts]
oci-la-mcp = "oci_la_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 8.2 Installation

```bash
# From PyPI (once published)
pip install oci-log-analytics-mcp

# From source
git clone https://github.com/your-org/oci-log-analytics-mcp.git
cd oci-log-analytics-mcp
pip install -e .
```

### 8.3 MCP Client Configuration

#### Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "oci-log-analytics": {
      "command": "oci-la-mcp",
      "args": []
    }
  }
}
```

#### Cline (VSCode)

```json
// .vscode/settings.json or cline config
{
  "cline.mcpServers": {
    "oci-log-analytics": {
      "command": "oci-la-mcp",
      "args": []
    }
  }
}
```

---

## 9. Future Enhancements (V2)

| Feature | Description | Complexity |
|---------|-------------|------------|
| Alerts integration | Query and acknowledge alerts | Medium |
| Dashboard read | List and view dashboard widgets | Medium |
| Create saved search | Write saved searches from queries | Low |
| PII redaction | Configurable pattern redaction | Medium |
| Web UI | Streamlit/Chainlit wrapper | High |
| Scheduled tasks | View purge/archival job status | Low |

---

## 10. Appendix

### 10.1 OCI SDK References

- [OCI Python SDK Documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- [Log Analytics API Reference](https://docs.oracle.com/en-us/iaas/api/#/en/logan-api-spec/20200601/)
- [Log Analytics Query Language](https://docs.oracle.com/en-us/iaas/log-analytics/doc/command-reference.html)

### 10.2 MCP References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

**End of Technical Design Document**
