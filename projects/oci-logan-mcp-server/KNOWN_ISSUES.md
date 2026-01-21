# Known Issues

Technical debt and improvements to address in future releases.

## Medium Priority

### 1. Debug Log Exposure
**Location**: `src/oci_la_mcp/oci_client/client.py:16-26`

Debug logs are written to a fixed path (`~/.oci-la-mcp/debug.log`) without rotation. The exception handler silently swallows errors.

**Recommendation**: Make debug logging configurable via settings, use rotating file handler, don't silently ignore write failures.

### 2. Broad Exception Handling
**Locations**:
- `src/oci_la_mcp/oci_client/auth.py:99`
- `src/oci_la_mcp/oci_client/client.py:25`
- `src/oci_la_mcp/services/query_validator.py:144, 240`
- `src/oci_la_mcp/mcp/handlers.py` (multiple locations)

**Issue**: Using `except Exception:` hides specific errors and makes debugging harder.

**Recommendation**: Catch specific exceptions (e.g., `oci.exceptions.ServiceError`, `oci.exceptions.ConfigFileNotFound`).

### 3. Timeout Not Enforced
**Location**: `src/oci_la_mcp/oci_client/client.py`

The `timeout_seconds` setting exists but is not actually used. Queries can hang indefinitely if OCI API is unresponsive.

**Recommendation**: Implement actual timeout enforcement using asyncio.wait_for() or similar.

### 4. Infinite Retry Possible
**Location**: `src/oci_la_mcp/oci_client/client.py:240-247`

Rate limit retry logic uses recursion without a depth limit. Could theoretically retry infinitely.

**Recommendation**: Add a max retry count or pass depth parameter.

## Low Priority

### 5. Print Statement in Production Code
**Location**: `src/oci_la_mcp/services/visualization.py:150`

Uses `print()` instead of proper logging.

**Recommendation**: Replace with `logger.error()` or `logger.warning()`.

### 6. Missing Test Coverage
No unit tests for:
- `OCILogAnalyticsClient._query_all_compartments()` - cross-compartment query logic
- `QueryValidator.validate()` with actual field names
- `VisualizationEngine._to_dataframe()` edge cases
- `ExportService` row materialization
- Rate limiter exponential backoff accuracy

### 7. Import Location
**Location**: `src/oci_la_mcp/oci_client/rate_limiter.py:85`

`random` module imported inside method rather than at top of file (PEP 8 violation).

### 8. Magic Numbers
Various hardcoded values that should be named constants:
- 5 minute default cache TTL (`cache/manager.py`)
- 10 MB max file size for query logger (`logging/query_logger.py`)
- 100 entry memory limit for query logger (`logging/query_logger.py`)

### 9. Private Attribute Access
**Location**: `src/oci_la_mcp/mcp/handlers.py:216-220`

Uses `self.oci_client._config` (private attribute) instead of a public property.
