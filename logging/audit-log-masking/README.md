# OCI Audit Log Masking for External SIEM

Use Configure Function Task option in Service Connector to mask sensitive data present in OCI Audit Logs while integrating this log data with an external SIEM solution.
This OCI Function masks replayable authentication credentials from OCI Audit Logs before they leave your tenancy.

## Why

OCI Audit Logs may carry sensitive headers and tokens in cleartext:

- `request.headers.Authorization` - API signing keys (`Signature keyId="ST$..."`)
- `request.headers.opc-principal` - full service auth context with embedded JWTs and session tokens
- `request.headers.opc-obo-principal` - delegated auth tokens
- `identity.credentials` - session tokens (when not pre-masked by OCI)
- Bearer / Basic tokens in any header value

Shipping these to an external SIEM (Securonix, Splunk, QRadar, Sentinel) creates a credential exfiltration risk. This function redacts them in-flight while preserving everything the SIEM needs for detection: who, from where, what, on what resource, and outcome.

## Architecture

```
                         Service Connector Hub
                        ┌─────────────────────┐
  ┌──────────────┐      │                     │      ┌───────────────────┐
  │  OCI Audit   │─────▶│  ┌───────────────┐  │─────▶│  OCI Streaming    │
  │  Logs        │      │  │ OCI Function  │  │      └────────┬──────────┘
  └──────────────┘      │  │ (mask task)   │  │               │
                        │  └───────────────┘  │               ▼
                        └─────────────────────┘      ┌───────────────────┐
                                                     │  External SIEM    │
                                                     │ (Splunk, Sentinel │
                                                     │ etc)              │
                                                     └───────────────────┘
```

**Source:** Logging → `_Audit` (all compartments)
**Task:** This function masks sensitive fields
**Target:** OCI Streaming → forwarded to external SIEM

> **Note:** Service Connector Hub does not support the function task when the target is OCI Log Analytics directly. Use Streaming as an intermediary.

## What Gets Masked vs Preserved

| Masked (redacted) | Preserved (intact) |
|---|---|
| `request.headers.Authorization` | `identity.principalId` |
| `request.headers.opc-principal` | `identity.principalName` |
| `request.headers.opc-obo-principal` | `identity.ipAddress` / `userAgent` |
| `identity.credentials` | `identity.tenantId` |
| Any value containing `ST$` tokens | `eventType` / `eventName` |
| Any `Bearer` / `Basic` auth strings | `request.action` / `request.path` |
| `opc-principal-token` / `x-auth-token` | `compartmentId` / `resourceId` |
| | `response.status` / `responseTime` |
| | All timestamps and state changes |

Redacted fields appear as `[REDACTED]` in the output.

## Files

```
audit-log-masking/
├── func.py              # Masking function (deploy this)
└── verify_masking.py    # Verification script for testing
```

## Deployment

**1. Deploy the function**

- Deploy the Function as per guidelines in OCI under 'Getting started'
- replace the default func.py with the one in this repo and finally run the **fn deploy** command

**2. Create the Service Connector**

| Setting | Value |
|---|---|
| Source | Logging → `_Audit` log group |
| Task | Function → select the deployed function |
| Target | Streaming → your stream (or SIEM endpoint) |

**3. Verify in your SIEM**

`Authorization` headers should show `[REDACTED]`. All identity and request metadata should be intact.

## Testing Without a SIEM

Use OCI Streaming as the target and read the masked messages directly:

```
Audit Logs → SC (with function task) → OCI Streaming
                                            ↓
                                     verify_masking.py
```

```bash
# From Cloud Shell or any host with OCI SDK configured:
python3 verify_masking.py --stream-id <stream-ocid>

# More messages + full JSON output:
python3 verify_masking.py --stream-id <stream-ocid> --limit 10 --raw
```

To also verify in Logging Analytics, chain a second connector:

```
Stream → SC2 (no task) → Logging Analytics
```

Then search in Log Explorer:

```
'Log Source' = 'OCI Audit Logs' and 'Log Group' = <your-log-group> and 'ST$eyJ'
```

Zero results = no tokens leaking through.

## Customization

Add fields to `REDACT_KEYS` or patterns to `SECRET_VALUE_PATTERNS` in `func.py`:

```python
REDACT_KEYS = frozenset({
    ...
    "your-custom-header",     # mask by key name
})

SECRET_VALUE_PATTERNS = [
    ...
    re.compile(r"your-pattern"),  # mask by value pattern
]
```

## Fault Tolerance

The function never breaks the log pipeline. On any error (bad JSON, unexpected structure, exception), it returns the original payload unchanged with HTTP 200. Worst case: unmasked logs. Never lost logs.

