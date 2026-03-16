# OCI Audit Log — Filter, Trim & Mask for SIEM (Part 2)

Extends [Part 1 (audit-log-masking)](../audit-log-masking/) with event filtering and payload trimming to reduce audit log volume and size before shipping to an external SIEM.

## Problem

A typical OCI tenancy generates ~1.6 million audit events/day. Most are GET (read) requests that add noise for SIEM analysis. Each event is ~16,000 characters, largely due to verbose headers and state diffs. This function solves both issues.

## What This Function Does

| # | Capability | Effect |
|---|---|---|
| 1 | **Filter events** | Drops all GET/HEAD/OPTIONS requests — only POST, DELETE, PUT, PATCH reach the SIEM |
| 2 | **Trim payload** | Strips request headers, response headers, and previous state diffs — reduces ~16K chars to ~2-3K |
| 3 | **Mask credentials** | Redacts any remaining sensitive values (same logic as Part 1) |

### Expected Volume Reduction

GET requests typically account for 70-80% of audit events. Combined with payload trimming, expect:
- **Event count**: ~1.6M/day → ~350-500K/day
- **Per-event size**: ~16K chars → ~2-3K chars
- **Total data volume**: ~85-90% reduction

## Architecture

```
                         Service Connector Hub
                        ┌─────────────────────────────┐
  ┌──────────────┐      │                             │      ┌────────────────┐
  │  OCI Audit   │─────>│  ┌───────────────────────┐  │─────>│ OCI Streaming  │
  │  Logs        │      │  │ OCI Function          │  │      └───────┬────────┘
  └──────────────┘      │  │ 1. Filter (drop GETs) │  │              │
                        │  │ 2. Trim (strip bulk)  │  │              v
                        │  │ 3. Mask (redact creds)│  │      ┌────────────────┐
                        │  └───────────────────────┘  │      │ External SIEM  │
                        └─────────────────────────────┘      └────────────────┘
```

## What Gets Filtered, Stripped, and Preserved

### Filtered (dropped entirely)
- All `GET` requests
- All `HEAD` requests
- All `OPTIONS` requests

### Stripped (removed from kept events)
| Field | Why |
|---|---|
| `request.headers` | Contains Authorization, opc-principal, etc. — bulk of the 16K size |
| `response.headers` | Verbose OCI response headers (opc-request-id, etag, etc.) |
| `stateChange.previous` | Previous state diff — often huge; current state is kept |

### Preserved (intact in output)
| Field | Purpose |
|---|---|
| `eventType` / `eventName` | What happened |
| `eventTime` | When |
| `compartmentId` / `compartmentName` | Where |
| `identity.principalId` / `principalName` | Who |
| `identity.ipAddress` | From where |
| `request.action` / `request.path` | What action on what resource |
| `request.parameters` | Request parameters (query strings, body fields) |
| `response.status` / `response.responseTime` | Outcome |
| `response.payload` | Response body (if present) |
| `resourceId` / `resourceName` | Target resource |
| `stateChange.current` | Current state after the change |
| `freeformTags` / `definedTags` | Resource tags |

### Masked (redacted as safety net)
- `identity.credentials` → `[REDACTED]`
- Any remaining values matching `ST$` tokens, `Signature keyId=`, `Bearer`, `Basic` patterns

## Files

```
audit-log-masking-part-2/
├── func.py                # Filter + Trim + Mask function (deploy this)
├── verify_filtering.py    # Verification script
└── README.md              # This file
```

## Deployment

**1. Deploy the function**

- Deploy the Function as per guidelines in OCI under 'Getting started'
- Replace the default `func.py` with the one from this repo and run `fn deploy`

**2. Create the Service Connector**

| Setting | Value |
|---|---|
| Source | Logging → `_Audit` log group |
| Task | Function → select the deployed function |
| Target | Streaming → your stream (or SIEM endpoint) |

> This replaces Part 1 in the pipeline — do not chain both functions.

**3. Verify**

```bash
python3 verify_filtering.py --stream-id <stream-ocid> --limit 10

# With full JSON output:
python3 verify_filtering.py --stream-id <stream-ocid> --limit 10 --raw
```

The script checks:
- No GET events present (filtering works)
- Headers are stripped (trimming works)
- Credentials are masked (masking works)
- Essential SIEM fields are preserved
- Event size is under 5K chars

## Customization

### Keep or drop different HTTP methods

Edit `ALLOWED_METHODS` in `func.py`:

```python
# Default: only keep write operations
ALLOWED_METHODS = frozenset({"POST", "DELETE", "PUT", "PATCH"})

# Example: also keep PATCH separately (already included by default)
ALLOWED_METHODS = frozenset({"POST", "DELETE", "PUT", "PATCH"})
```

### Keep additional fields

Add fields to `KEEP_TOP_LEVEL` in `func.py`:

```python
KEEP_TOP_LEVEL = frozenset({
    ...
    "additionalDetails",   # add this to keep additional details
})
```

### Keep request headers (disable trimming for headers)

Remove `"headers"` from `STRIP_FROM_REQUEST`:

```python
STRIP_FROM_REQUEST = frozenset()  # keep all request sub-fields
```

## Part 1 vs Part 2

| Feature | Part 1 | Part 2 |
|---|---|---|
| Credential masking | Yes | Yes |
| Event filtering (drop GETs) | No | Yes |
| Payload trimming | No | Yes |
| Use case | Simple masking, keep all events | High-volume tenancies, SIEM cost optimization |

Use **Part 1** if you need all events with just credential masking.
Use **Part 2** if you need to reduce volume and cost for high-traffic tenancies.

## Fault Tolerance

Same as Part 1 — the function never breaks the log pipeline. On any error, it returns the original payload unchanged with HTTP 200. Worst case: unfiltered/untrimmed logs. Never lost logs.
