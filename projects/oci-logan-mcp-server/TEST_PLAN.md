# OCI Log Analytics MCP Server - Test Plan

## Overview
This document contains comprehensive test cases for the OCI Log Analytics MCP Server. Tests are organized by priority and category.

---

## Priority Levels
- **P0 (Critical)**: Must work - core functionality that blocks all usage
- **P1 (High)**: Important features used frequently by most users
- **P2 (Medium)**: Common features, but workarounds may exist
- **P3 (Low)**: Edge cases, nice-to-have features

---

## Test Categories

### Category 1: Connectivity & Configuration (P0)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| C1 | Basic connectivity | "What is my current Log Analytics context?" | Returns namespace, compartment_id, default settings | P0 |
| C2 | List compartments | "List all compartments I have access to" | Returns list of compartments with names and OCIDs | P0 |
| C3 | Server health | "List available log sources" | Returns list without errors | P0 |

---

### Category 2: Schema Exploration (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| S1 | List log sources | "What log sources are available?" | Returns log source names, descriptions | P1 |
| S2 | List fields | "What fields can I query on?" | Returns field names, types, descriptions | P1 |
| S3 | List fields for source | "What fields are available for Linux Syslog logs?" | Returns fields specific to that source | P2 |
| S4 | List entities | "Show me all monitored entities" | Returns entities with names and types | P1 |
| S5 | List entities by type | "Show me all Host entities" | Returns only Host-type entities | P2 |
| S6 | List parsers | "What log parsers are available?" | Returns parser list | P2 |
| S7 | List labels | "What labels are defined?" | Returns label definitions | P2 |
| S8 | List log groups | "Show me the log groups" | Returns log groups in compartment | P2 |
| S9 | List saved searches | "What saved searches do I have?" | Returns saved search list | P2 |

---

### Category 3: Basic Query Execution (P0)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| Q1 | Simple count query | "How many logs do I have in the last hour?" | Returns count with metadata showing query, time range | P0 |
| Q2 | Count by source | "Show me log count by source for today" | Returns breakdown by log source | P0 |
| Q3 | Search for errors | "Find all ERROR logs in the last 24 hours" | Returns error logs | P0 |
| Q4 | Top entities | "Which hosts generated the most logs today?" | Returns sorted list of hosts | P1 |
| Q5 | Query with filter | "Show me logs from host 'webserver01' in the last hour" | Returns filtered logs | P1 |

---

### Category 4: Time Range Handling (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| T1 | Last 15 minutes | "Show me logs from the last 15 minutes" | Uses time_range=last_15_min | P1 |
| T2 | Last hour | "Get logs from the past hour" | Uses time_range=last_1_hour | P1 |
| T3 | Last 24 hours | "Show me yesterday's logs" | Uses time_range=last_24_hours | P1 |
| T4 | Last 7 days | "Get logs from the past week" | Uses time_range=last_7_days | P1 |
| T5 | Last 30 days | "Show me last month's log summary" | Uses time_range=last_30_days | P1 |
| T6 | Specific date range | "Show me logs from December 25th to December 26th 2025" | Uses time_start and time_end | P1 |
| T7 | Natural language time | "Show me logs from last Monday" | Interprets and converts to appropriate time range | P2 |
| T8 | Metadata verification | "How many logs in the last hour?" + verify response | Response includes metadata.time_start and metadata.time_end | P0 |

---

### Category 5: Scope & Compartment Handling (P0) - CRITICAL

These tests verify the scope/compartment feature we just implemented.

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| SC1 | Default compartment | "How many logs in my compartment?" | Queries default compartment only | P0 |
| SC2 | Tenancy-wide query | "Show me total logs across ALL compartments in the tenancy" | Uses scope=tenancy, returns significantly more logs | P0 |
| SC3 | Tenancy scope keywords | "Give me organization-wide log count" | AI uses scope=tenancy | P0 |
| SC4 | Tenancy scope keywords 2 | "How many logs across the entire tenancy?" | AI uses scope=tenancy | P0 |
| SC5 | Compare default vs tenancy | First: "Count logs in my compartment" then "Count logs across all compartments" | Second query should return MORE logs | P0 |
| SC6 | Metadata shows compartment | Run any query | Response metadata.compartment_id shows which compartment was queried | P0 |
| SC7 | Include subcompartments | "Show me logs including all sub-compartments" | Uses include_subcompartments=true | P1 |
| SC8 | Specific compartment | "Query logs from compartment [OCID]" | Uses the specified compartment_id | P2 |

---

### Category 6: Query Result Metadata (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| M1 | Query in metadata | Run any query | Response includes metadata.query showing exact query run | P1 |
| M2 | Time in metadata | Run any query | Response includes metadata.time_start and metadata.time_end | P1 |
| M3 | Compartment in metadata | Run any query | Response includes metadata.compartment_id | P1 |
| M4 | Execution time | Run any query | Response includes metadata.execution_time_seconds | P2 |
| M5 | Subcompartments flag | Query with include_subcompartments | Response includes metadata.include_subcompartments=true | P2 |

---

### Category 7: Visualization (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| V1 | Pie chart | "Show me a pie chart of logs by source" | Returns PNG pie chart + raw data | P1 |
| V2 | Bar chart | "Create a bar chart of error counts by host" | Returns PNG bar chart + raw data | P1 |
| V3 | Line chart | "Show me a line chart of log volume over time" | Returns PNG line chart | P1 |
| V4 | Table visualization | "Display logs as a table" | Returns table visualization | P2 |
| V5 | Chart with title | "Create a pie chart titled 'Log Distribution'" | Chart has custom title | P2 |
| V6 | Chart with time range | "Bar chart of errors in the last 7 days" | Uses correct time range | P1 |
| V7 | Chart with scope | "Pie chart of logs across entire tenancy" | Uses scope=tenancy | P1 |
| V8 | Area chart | "Show an area chart of log trends" | Returns area chart | P2 |
| V9 | Treemap | "Create a treemap of log sources" | Returns treemap visualization | P3 |

---

### Category 8: Export (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| E1 | Export to CSV | "Export error logs to CSV" | Returns CSV formatted data | P1 |
| E2 | Export to JSON | "Export logs as JSON" | Returns JSON formatted data | P1 |
| E3 | Export with time range | "Export last week's logs to CSV" | Uses correct time range | P1 |
| E4 | Export with scope | "Export all tenancy logs to JSON" | Uses scope=tenancy | P1 |
| E5 | Export specific query | "Export logs where severity='ERROR' to CSV" | Filters correctly | P2 |

---

### Category 9: Batch Queries (P2)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| B1 | Multiple queries | "Run these queries: 1) count all logs, 2) count errors, 3) count warnings" | Returns results for all three | P2 |
| B2 | Batch with different times | "Compare last hour vs last 24 hours error count" | Runs both with different time ranges | P2 |

---

### Category 10: Saved Searches (P2)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| SS1 | List saved searches | "What saved searches are available?" | Returns list of saved searches | P2 |
| SS2 | Run by name | "Run the saved search called 'Error Summary'" | Executes saved search | P2 |
| SS3 | Run by ID | "Run saved search [OCID]" | Executes saved search | P3 |

---

### Category 11: Error Handling (P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| ER1 | Invalid query syntax | "Run query: SELECT * FROM" | Returns helpful error message | P1 |
| ER2 | Non-existent field | "Query logs where nonexistent_field = 'value'" | Handles gracefully | P2 |
| ER3 | Empty results | "Find logs with message containing 'xyzzy123impossible'" | Returns empty result set gracefully | P1 |
| ER4 | Invalid time range | Query with future dates | Handles gracefully | P2 |
| ER5 | Invalid compartment | "Query compartment ocid1.invalid..." | Returns meaningful error | P2 |

---

### Category 12: Real-World Use Cases (P0-P1)

| ID | Test Case | User Prompt | Expected Behavior | Priority |
|----|-----------|-------------|-------------------|----------|
| RW1 | Security audit | "Show me all failed login attempts in the last 24 hours" | Returns security-relevant logs | P1 |
| RW2 | Error investigation | "What errors occurred in the last hour and which hosts had them?" | Returns errors grouped by host | P0 |
| RW3 | Capacity planning | "Show me log volume trends for the past week" | Returns time-series data | P1 |
| RW4 | Compliance check | "Export all access logs from last month to CSV" | Returns CSV export | P1 |
| RW5 | Troubleshooting | "Find logs mentioning 'timeout' or 'connection refused'" | Returns relevant logs | P0 |
| RW6 | Dashboard data | "Give me a summary: total logs, error count, top 5 sources for today" | Returns multi-part summary | P1 |
| RW7 | Cross-team visibility | "Show me log counts by compartment across the entire organization" | Uses scope=tenancy, groups by compartment | P1 |
| RW8 | Alerting context | "What happened in the 5 minutes before and after 2PM today?" | Uses specific time window | P2 |

---

## Test Execution Checklist

### Before Testing
- [ ] Server is running (`./run.sh` or `./update.sh`)
- [ ] Claude Desktop is configured with MCP server
- [ ] Default compartment is set (not tenancy)

### P0 Tests (Must Pass)
- [ ] C1: Basic connectivity
- [ ] C2: List compartments
- [ ] C3: Server health (list sources)
- [ ] Q1: Simple count query
- [ ] Q2: Count by source
- [ ] **SC1: Default compartment query**
- [ ] **SC2: Tenancy-wide query (scope=tenancy)**
- [ ] **SC5: Compare default vs tenancy counts**
- [ ] SC6: Metadata shows compartment
- [ ] T8: Metadata verification
- [ ] RW2: Error investigation
- [ ] RW5: Troubleshooting

### P1 Tests (Should Pass)
- [ ] All Schema Exploration (S1-S9)
- [ ] All Time Range (T1-T7)
- [ ] All Metadata (M1-M5)
- [ ] Visualization (V1-V3, V6-V7)
- [ ] Export (E1-E4)
- [ ] Error handling (ER1, ER3)
- [ ] Real-world (RW1, RW3, RW4, RW6, RW7)

### P2/P3 Tests (Nice to Have)
- [ ] Remaining tests

---

## Known Expected Behaviors

1. **Tenancy queries are slower**: When using `scope=tenancy`, the server iterates through all compartments. This can take 30-60+ seconds for large tenancies.

2. **Metadata always present**: Every query response should include a `metadata` object with query details.

3. **Scope vs compartment_id**:
   - `scope=tenancy` is the easy way for AI to understand "query everything"
   - `compartment_id` allows specific OCID override
   - Both can be used, but `scope` takes precedence

4. **Cache behavior**: Repeated identical queries may return faster from cache. The response will show `"source": "cache"` instead of `"source": "live"`.

---

## Reporting Issues

When a test fails, document:
1. Test ID
2. Exact prompt used
3. Actual response received
4. Expected vs actual behavior
5. Debug log contents (`~/.oci-la-mcp/debug.log`)
