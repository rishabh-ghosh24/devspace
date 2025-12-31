# Product Requirements Document (PRD)
# OCI Log Analytics MCP Server

**Version:** 1.0
**Date:** December 28, 2025
**Author:** PresalesAI
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Overview

The OCI Log Analytics MCP Server is a Model Context Protocol (MCP) server that enables natural language interaction with Oracle Cloud Infrastructure (OCI) Log Analytics data. Users can query logs, explore schemas, run saved searches, and generate visualizations through conversational AI interfaces like Claude Desktop, Cline (VSCode), or any MCP-compatible client.

### 1.2 Problem Statement

Currently, interacting with OCI Log Analytics requires:
- Knowledge of Log Analytics query syntax
- Navigation through the OCI Console
- Manual chart creation and data export

This creates a barrier for users who need quick insights during incident response, debugging, or security investigations.

### 1.3 Solution

An MCP server that:
- Exposes Log Analytics capabilities as tools and resources
- Enables any AI model (Claude, GPT, Gemini, Grok) to construct and execute queries
- Provides visualizations inline in the chat interface
- Offers intelligent query validation and suggestions

### 1.4 Target Users

| User Type | Primary Use Cases |
|-----------|-------------------|
| DevOps/SRE Teams | Incident response, system health checks, trend analysis |
| Developers | Application debugging, error investigation, log correlation |
| Security Teams | Threat hunting, audit log analysis, anomaly detection |
| Operations Staff | Capacity monitoring, service health, compliance reporting |

---

## 2. Goals & Success Metrics

### 2.1 Goals

| Goal | Description |
|------|-------------|
| **Simplify Access** | Enable natural language queries against Log Analytics |
| **Reduce Time to Insight** | From minutes (console navigation) to seconds (conversational) |
| **Democratize Log Analysis** | Users don't need to learn query syntax |
| **Model Agnostic** | Work with any AI model via MCP standard |
| **Easy Setup** | First-run wizard, minimal configuration |

### 2.2 Success Metrics

| Metric | Target |
|--------|--------|
| Query success rate (valid queries) | > 90% |
| Time from question to answer | < 30 seconds |
| Setup time for new users | < 5 minutes |
| Supported visualization types | 100% of LA native types |

---

## 3. User Stories

### 3.1 Core Query & Exploration

| ID | User Story | Priority |
|----|------------|----------|
| US-01 | As a user, I want to ask "Are there any errors in the last hour?" and get a summary | Must |
| US-02 | As a user, I want to see all available log sources so I know what data I can query | Must |
| US-03 | As a user, I want to explore fields available for a specific log source | Must |
| US-04 | As a user, I want to list all entities being monitored | Must |
| US-05 | As a user, I want to see available parsers and labels | Must |
| US-06 | As a user, I want to run complex queries with filters and aggregations | Must |
| US-07 | As a user, I want to switch between compartments without reconfiguring | Must |
| US-08 | As a user, I want to switch namespaces to query different tenancies | Must |
| US-09 | As a user, I want to run saved searches by name | Must |
| US-10 | As a user, I want to list all available saved searches | Must |

### 3.2 Visualization & Export

| ID | User Story | Priority |
|----|------------|----------|
| US-11 | As a user, I want to see a pie chart of error distribution by source | Must |
| US-12 | As a user, I want to see a time series of log volume over the past day | Must |
| US-13 | As a user, I want to see a bar chart of top 10 error-producing hosts | Must |
| US-14 | As a user, I want to export query results to CSV for further analysis | Must |
| US-15 | As a user, I want to export query results to JSON for integration | Must |
| US-16 | As a user, I want visualizations displayed inline in my chat interface | Must |

### 3.3 Query Intelligence

| ID | User Story | Priority |
|----|------------|----------|
| US-17 | As a user, I want the system to validate my query before execution | Must |
| US-18 | As a user, I want suggestions when I use an incorrect field name | Must |
| US-19 | As a user, I want to see example queries for common patterns | Must |
| US-20 | As a user, I want clear error messages with fix suggestions | Must |
| US-21 | As a user, I want the system to warn me if my query is too broad | Must |

### 3.4 Configuration & Setup

| ID | User Story | Priority |
|----|------------|----------|
| US-22 | As a new user, I want a guided setup wizard on first run | Must |
| US-23 | As a user, I want to configure via config file for persistence | Must |
| US-24 | As a user, I want to override settings via environment variables | Must |
| US-25 | As a user, I want to use OCI config file authentication | Must |
| US-26 | As a user, I want to use Instance Principal when running on OCI | Must |
| US-27 | As a user, I want to use Resource Principal in OCI Functions | Must |

### 3.5 Reliability & Security

| ID | User Story | Priority |
|----|------------|----------|
| US-28 | As a user, I want queries logged for debugging and audit | Must |
| US-29 | As a user, I want the system to handle rate limits gracefully | Must |
| US-30 | As a user, I want results cached briefly for follow-up questions | Must |
| US-31 | As a user, I want a warning if query results may contain sensitive data | Must |
| US-32 | As a user, I want configurable timeouts for long queries | Must |
| US-33 | As a user, I want to run multiple queries in one request | Must |

---

## 4. Functional Requirements

### 4.1 MCP Resources (Read-Only Context)

Resources provide context that AI models can read to understand the environment.

| Resource URI | Description | Contents |
|--------------|-------------|----------|
| `loganalytics://schema` | Complete schema information | Log sources, fields with types, entities, parsers, labels |
| `loganalytics://query-templates` | Common query patterns | Templates sourced from Oracle documentation |
| `loganalytics://syntax-guide` | Query language reference | Operators, functions, commands |
| `loganalytics://recent-queries` | Last 10 successful queries | Query text, timestamp, result count |

### 4.2 MCP Tools (Actions)

#### 4.2.1 Schema Exploration Tools

| Tool | Parameters | Returns |
|------|------------|---------|
| `list_log_sources` | `compartment_id` (optional) | List of log sources with metadata |
| `list_fields` | `source_name`, `compartment_id` (optional) | Fields with types, possible values, semantic hints |
| `list_entities` | `compartment_id` (optional), `entity_type` (optional) | Monitored entities |
| `list_parsers` | `compartment_id` (optional) | Available parsers |
| `list_labels` | `compartment_id` (optional) | Label definitions |
| `list_saved_searches` | `compartment_id` (optional) | Saved searches with metadata |
| `list_log_groups` | `compartment_id` (optional) | Log groups |

#### 4.2.2 Query Execution Tools

| Tool | Parameters | Returns |
|------|------------|---------|
| `validate_query` | `query`, `time_start`, `time_end` | Validation result, errors, suggestions, estimated cost |
| `run_query` | `query`, `time_start`, `time_end`, `max_results`, `compartment_id` | Query results with metadata |
| `run_saved_search` | `saved_search_name` or `saved_search_id` | Query results |
| `run_batch_queries` | `queries[]` (array of query objects) | Array of results |

#### 4.2.3 Visualization Tools

| Tool | Parameters | Returns |
|------|------------|---------|
| `visualize` | `query`, `chart_type`, `time_start`, `time_end`, `options` | PNG/SVG image (base64), raw data (JSON) |

Supported chart types:
- `pie` - Distribution charts
- `bar` - Comparisons, Top N
- `line` - Time series trends
- `area` - Volume over time
- `table` - Raw/aggregated data
- `tile` - Single value KPIs
- `bubble` - Multi-dimensional
- `treemap` - Hierarchical distribution
- `geo_map` - Location-based

#### 4.2.4 Export Tools

| Tool | Parameters | Returns |
|------|------------|---------|
| `export_results` | `query`, `format` (csv/json), `time_start`, `time_end` | File content or file path |

#### 4.2.5 Configuration Tools

| Tool | Parameters | Returns |
|------|------------|---------|
| `set_compartment` | `compartment_id` | Confirmation |
| `set_namespace` | `namespace` | Confirmation |
| `get_current_context` | None | Current namespace, compartment, log group |
| `list_compartments` | None | Available compartments |
| `list_namespaces` | None | Available namespaces |

### 4.3 Query Validation & Intelligence

#### 4.3.1 Pre-flight Validation

Before query execution, the system validates:
- Syntax correctness
- Field existence (with fuzzy matching for suggestions)
- Time range validity
- Estimated result size

#### 4.3.2 Fuzzy Field Matching

When a field name is incorrect:
```
Input: "stats count by 'Server Name'"
Response: "Field 'Server Name' not found. Did you mean:
  - 'Host Name (Server)' (95% match)
  - 'Server' (80% match)
  - 'Entity Name' (60% match)"
```

#### 4.3.3 Query Complexity Guard

| Check | Threshold | Action |
|-------|-----------|--------|
| Time range | > 7 days | Warning + confirmation required |
| No filters on large source | Estimated > 100K rows | Warning + suggestion to add filter |
| Result limit | > 10,000 | Auto-cap with notice |

### 4.4 Error Handling

All errors return:
- Error code and message
- Likely cause
- Suggested fix with example
- Similar/correct field names (if applicable)

Example:
```json
{
  "error": "FIELD_NOT_FOUND",
  "message": "Field 'Serverity' not found in source 'Linux Syslog'",
  "suggestion": "Did you mean 'Severity'?",
  "example_fix": "'Severity' = 'Error' | stats count by 'Host Name'",
  "available_fields": ["Severity", "Facility", "Message", "Host Name", "..."]
}
```

### 4.5 Caching

| Cache Type | TTL | Purpose |
|------------|-----|---------|
| Query results | 5 minutes | Follow-up questions on same data |
| Schema information | 15 minutes | Reduce API calls for field lookups |
| Saved searches list | 10 minutes | Quick access without re-fetching |

Cache is stored in memory (not persisted across restarts).

### 4.6 Rate Limiting & Throttling

- Detect OCI 429 responses
- Implement exponential backoff (1s, 2s, 4s, 8s, max 30s)
- Queue concurrent requests if needed
- Surface rate limit status to AI for user communication

### 4.7 Query Logging

Log file location: `~/.oci-la-mcp/logs/queries.log`

Each entry contains:
- Timestamp
- Query text
- Time range
- Compartment/Namespace
- Execution time
- Result count
- Success/failure status
- Error details (if any)

Log rotation: 10MB max, 5 files retained

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Requirement |
|--------|-------------|
| Query execution | < 60 seconds (configurable timeout) |
| Schema refresh | < 5 seconds |
| Visualization generation | < 10 seconds |
| MCP tool response | < 100ms (excluding OCI API time) |

### 5.2 Reliability

| Requirement | Description |
|-------------|-------------|
| Graceful degradation | If one tool fails, others continue working |
| Connection retry | Auto-retry on transient network failures |
| State recovery | Reload context on MCP client reconnection |

### 5.3 Security

| Requirement | Description |
|-------------|-------------|
| Credential handling | Never log or expose OCI credentials |
| Sensitive data warning | Alert when results may contain PII patterns |
| Local execution | No data sent to external services (except OCI) |
| Config file permissions | Warn if config file is world-readable |

### 5.4 Compatibility

| Client | Support Level |
|--------|---------------|
| Claude Desktop | Full |
| Cline (VSCode) | Full |
| Cursor | Full |
| Other MCP clients | Should work (not tested) |

| Python Version | Support |
|----------------|---------|
| 3.9+ | Full |
| 3.8 | Best effort |

---

## 6. Configuration

### 6.1 Configuration File

Location: `~/.oci-la-mcp/config.yaml`

```yaml
# OCI Authentication
oci:
  config_path: ~/.oci/config
  profile: DEFAULT
  # Auth type: config_file | instance_principal | resource_principal
  auth_type: config_file

# Log Analytics Settings
log_analytics:
  namespace: <tenancy_namespace>
  default_compartment_id: ocid1.compartment.oc1..xxx
  default_log_group_id: ocid1.loganalyticsloggroup.oc1..xxx  # optional

# Query Defaults
query:
  default_time_range: last_1_hour  # last_15_min | last_1_hour | last_24_hours | last_7_days
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
  log_path: ~/.oci-la-mcp/logs/
  log_level: INFO  # DEBUG | INFO | WARNING | ERROR

# Guardrails
guardrails:
  max_time_range_days: 7
  warn_on_large_results: true
  large_result_threshold: 10000
```

### 6.2 Environment Variable Overrides

| Variable | Overrides |
|----------|-----------|
| `OCI_LA_MCP_CONFIG` | Config file path |
| `OCI_LA_NAMESPACE` | `log_analytics.namespace` |
| `OCI_LA_COMPARTMENT` | `log_analytics.default_compartment_id` |
| `OCI_CONFIG_PATH` | `oci.config_path` |
| `OCI_CONFIG_PROFILE` | `oci.profile` |
| `OCI_LA_AUTH_TYPE` | `oci.auth_type` |
| `OCI_LA_TIMEOUT` | `query.timeout_seconds` |
| `OCI_LA_LOG_LEVEL` | `logging.log_level` |

### 6.3 First-Run Setup Wizard

On first run (no config file exists):

```
Welcome to OCI Log Analytics MCP Server!

Let's configure your connection to OCI Log Analytics.

Step 1/5: OCI Configuration
  Path to OCI config file [~/.oci/config]:
  Profile name [DEFAULT]:

Step 2/5: Authentication Type
  Select authentication method:
  1. Config file (local development)
  2. Instance Principal (OCI VM)
  3. Resource Principal (OCI Functions)
  Choice [1]:

Step 3/5: Log Analytics Namespace
  Fetching available namespaces...
  Found: mytenancy-namespace
  Use this namespace? [Y/n]:

Step 4/5: Default Compartment
  Fetching compartments...
  1. root
  2. Production
  3. Development
  Select default compartment [1]:

Step 5/5: Confirm Configuration
  Namespace: mytenancy-namespace
  Compartment: Production
  Auth: config_file (profile: DEFAULT)

  Save this configuration? [Y/n]:

Configuration saved to ~/.oci-la-mcp/config.yaml
MCP Server is ready!
```

---

## 7. Out of Scope (V1)

The following are explicitly excluded from V1:

| Feature | Reason | Planned For |
|---------|--------|-------------|
| Alerts/Ingest status | Nice-to-have, not core query functionality | V2 |
| Dashboard interaction | Complex, requires additional UI considerations | V2 |
| Scheduled tasks status | Lower priority monitoring feature | V2 |
| Web UI wrapper | MCP client provides UI; can add later | V2 |
| Create saved search | Write operation, focus on read-first | V2 |
| PII redaction | Complex regex, needs tuning per environment | V2 |
| Multi-tenancy session | V1 supports switching, V2 adds simultaneous | V2 |

---

## 8. Dependencies

### 8.1 External Dependencies

| Dependency | Purpose | Version |
|------------|---------|---------|
| OCI Python SDK | OCI API interaction | >= 2.90.0 |
| MCP Python SDK | MCP protocol implementation | >= 0.9.0 |
| Matplotlib | Chart generation | >= 3.7.0 |
| Pandas | Data manipulation | >= 2.0.0 |
| PyYAML | Configuration parsing | >= 6.0 |
| Pillow | Image processing | >= 10.0.0 |

### 8.2 OCI Services

| Service | API Endpoints Used |
|---------|-------------------|
| Log Analytics | Query, Saved Searches, Schema, Sources, Entities, Parsers |
| Identity | Compartment listing, Tenancy info |

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| OCI API rate limiting | Degraded experience | Medium | Exponential backoff, request queuing |
| Large result sets | Timeout, memory issues | Medium | Result limits, pagination, warnings |
| AI model query errors | Bad queries, errors | Low | Validation, fuzzy matching, examples |
| OCI SDK breaking changes | Server failures | Low | Pin SDK version, test on updates |
| Credential misconfiguration | Auth failures | Medium | First-run wizard, clear error messages |

---

## 10. Appendix

### 10.1 Log Analytics Query Syntax Reference

Key operators:
- `|` - Pipe (chain operations)
- `where` - Filter
- `stats` - Aggregate
- `timestats` - Time-based aggregation
- `sort` - Order results
- `head` / `tail` - Limit results
- `fields` - Select columns
- `rename` - Rename fields
- `eval` - Calculate new fields

Reference: https://docs.oracle.com/en-us/iaas/log-analytics/doc/command-reference.html

### 10.2 Common Query Templates

```
# Errors in last hour
'Error' or 'Critical' | timestats count by 'Log Source'

# Top 10 by field
* | stats count by 'Host Name' | sort -count | head 10

# Trend over time
* | timestats count span=1hour

# Search keyword
'{keyword}' | fields 'Log Source', 'Entity', 'Message', 'Time'

# Filter by severity and source
'Severity' = 'Error' and 'Log Source' = 'Linux Syslog' | stats count by 'Host Name'
```

---

**End of Product Requirements Document**
