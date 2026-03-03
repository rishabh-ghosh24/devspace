# Claude Desktop Test Script for OCI Log Analytics MCP Server

Copy and paste these prompts into Claude Desktop to test the MCP server.
Record PASS/FAIL for each test.

---

## Prerequisites
1. MCP server is running on your VM
2. Claude Desktop is connected to the MCP server
3. Clear any previous conversation (start fresh)

---

## PHASE 1: Critical Tests (P0) - MUST ALL PASS

### Test 1.1: Basic Connectivity
```
What is my current Log Analytics context? Show me the namespace and compartment I'm connected to.
```
**Expected**: Shows namespace, compartment_id, and settings
**PASS/FAIL**: ___

---

### Test 1.2: List Compartments
```
List all compartments I have access to.
```
**Expected**: Returns list of compartments with names and OCIDs
**PASS/FAIL**: ___

---

### Test 1.3: List Log Sources
```
What log sources are available in Log Analytics?
```
**Expected**: Returns list of log source names
**PASS/FAIL**: ___

---

### Test 1.4: Simple Query
```
How many logs do I have in the last hour? Show me the count.
```
**Expected**: Returns a count number AND metadata showing the query, time range, and compartment used
**PASS/FAIL**: ___
**Note the log count**: _____________

---

### Test 1.5: Query with Metadata Verification
```
Count my logs from the last 24 hours. Make sure to show me what query was executed, what time range was used, and which compartment was queried.
```
**Expected**: Response includes metadata block with query, time_start, time_end, compartment_id
**PASS/FAIL**: ___

---

### Test 1.6: CRITICAL - Tenancy-Wide Query
```
Show me the TOTAL log count across ALL compartments in the ENTIRE tenancy for the last 7 days.
```
**Expected**:
- Uses scope=tenancy (check that compartment_id in metadata starts with "ocid1.tenancy")
- Returns a LARGER number than your default compartment
- May take 30-60 seconds to complete
**PASS/FAIL**: ___
**Note the log count**: _____________

---

### Test 1.7: CRITICAL - Compare Default vs Tenancy
First query:
```
How many logs are in my default compartment for the last 7 days?
```
**Note count**: _____________

Second query:
```
Now show me the count across ALL compartments in the entire tenancy for the same time period.
```
**Note count**: _____________

**Expected**: Second count should be >= first count (likely MUCH larger)
**PASS/FAIL**: ___

---

### Test 1.8: Error Search
```
Find all logs containing ERROR or CRITICAL in the last hour. Show me a summary.
```
**Expected**: Returns error logs or a count of errors
**PASS/FAIL**: ___

---

## PHASE 2: Time Range Tests (P1)

### Test 2.1: Last 15 Minutes
```
Show me log count from the last 15 minutes.
```
**Expected**: Uses time_range=last_15_min, returns count
**PASS/FAIL**: ___

---

### Test 2.2: Last 7 Days
```
How many logs were generated in the past week?
```
**Expected**: Uses time_range=last_7_days
**PASS/FAIL**: ___

---

### Test 2.3: Specific Date Range
```
Show me logs from December 25, 2025 to December 26, 2025.
```
**Expected**: Uses time_start and time_end parameters
**PASS/FAIL**: ___

---

## PHASE 3: Visualization Tests (P1)

### Test 3.1: Pie Chart
```
Create a pie chart showing the distribution of logs by log source for the last 24 hours.
```
**Expected**: Returns a pie chart image + raw data
**PASS/FAIL**: ___

---

### Test 3.2: Bar Chart
```
Show me a bar chart of log counts by entity for today.
```
**Expected**: Returns a bar chart image
**PASS/FAIL**: ___

---

### Test 3.3: Tenancy-Wide Visualization
```
Create a pie chart of log distribution across ALL compartments in the entire tenancy.
```
**Expected**: Uses scope=tenancy, returns pie chart
**PASS/FAIL**: ___

---

## PHASE 4: Export Tests (P1)

### Test 4.1: CSV Export
```
Export the last hour's error logs to CSV format.
```
**Expected**: Returns CSV formatted data
**PASS/FAIL**: ___

---

### Test 4.2: JSON Export
```
Export log summary as JSON for the last 24 hours.
```
**Expected**: Returns JSON formatted data
**PASS/FAIL**: ___

---

## PHASE 5: Schema Exploration Tests (P1)

### Test 5.1: List Fields
```
What fields can I query on in Log Analytics?
```
**Expected**: Returns field names with data types
**PASS/FAIL**: ___

---

### Test 5.2: List Entities
```
Show me all monitored entities.
```
**Expected**: Returns list of entities (hosts, databases, etc.)
**PASS/FAIL**: ___

---

### Test 5.3: List by Type
```
Show me only the Host entities.
```
**Expected**: Returns filtered list of Host-type entities
**PASS/FAIL**: ___

---

## PHASE 6: Real-World Scenarios (P1)

### Test 6.1: Security Investigation
```
I need to investigate potential security issues. Show me:
1. Failed login attempts in the last 24 hours
2. Any unusual access patterns
3. Top sources of security-related logs
```
**Expected**: Returns security-relevant information
**PASS/FAIL**: ___

---

### Test 6.2: Troubleshooting
```
Our application is having issues. Find all logs mentioning "timeout", "error", or "failed" in the last hour. Group them by source.
```
**Expected**: Returns relevant troubleshooting logs grouped by source
**PASS/FAIL**: ___

---

### Test 6.3: Organization-Wide Summary
```
Give me an organization-wide summary:
- Total log count across all compartments
- Breakdown by log source
- Top 5 entities by log volume
Use data from the last 24 hours.
```
**Expected**: Uses scope=tenancy, returns comprehensive summary
**PASS/FAIL**: ___

---

### Test 6.4: Compliance Export
```
For compliance purposes, export all access logs from the last 30 days across the entire organization to CSV.
```
**Expected**: Uses scope=tenancy, returns CSV export
**PASS/FAIL**: ___

---

## PHASE 7: Error Handling Tests (P2)

### Test 7.1: Empty Results
```
Find logs containing the text "xyzzy123impossible456" in the last hour.
```
**Expected**: Returns empty result gracefully, not an error
**PASS/FAIL**: ___

---

### Test 7.2: Invalid Query Handling
```
Run this exact query: SELECT * FROM nonexistent
```
**Expected**: Returns helpful error message
**PASS/FAIL**: ___

---

## Test Summary

| Phase | Tests Passed | Tests Failed | Total |
|-------|--------------|--------------|-------|
| Phase 1 (P0 Critical) | ___ | ___ | 8 |
| Phase 2 (Time Range) | ___ | ___ | 3 |
| Phase 3 (Visualization) | ___ | ___ | 3 |
| Phase 4 (Export) | ___ | ___ | 2 |
| Phase 5 (Schema) | ___ | ___ | 3 |
| Phase 6 (Real-World) | ___ | ___ | 4 |
| Phase 7 (Error Handling) | ___ | ___ | 2 |
| **TOTAL** | ___ | ___ | **25** |

---

## Notes on Failures

Document any failures here:

| Test ID | Issue Description | Debug Log Contents |
|---------|-------------------|-------------------|
| | | |
| | | |
| | | |

---

## Quick Validation Commands

After running tests, you can check the debug log on your VM:
```bash
cat ~/.oci-la-mcp/debug.log | tail -50
```

Clear the debug log before a test session:
```bash
> ~/.oci-la-mcp/debug.log
```
