"""
OCI Audit Log Masking Function
================================
Deploy as a "Configure function task" in OCI Service Connector Hub
to mask replayable authentication credentials from audit logs before
shipping to an external SIEM.

Masked fields:
  - identity.credentials (session tokens)
  - request.headers.Authorization (API signature / Bearer / Basic auth)
  - request.headers.opc-principal (service auth context with embedded tokens)
  - request.headers.opc-obo-principal (delegated auth context)
  - opc-principal-token, x-auth-token (delegation tokens)
  - Any string value containing embedded ST$ tokens or Signature keyId

All other fields (principalId, principalName, ipAddress, eventType,
request path, compartmentId, etc.) are preserved for SIEM correlation.

Author:  Rishabh Ghosh (rishabh.g.ghosh@oracle.com)
Version: 1.1.0
Date:    2026-02-13

Changelog:
  1.0.0  2026-02-12  Initial release — credential & auth header masking
  1.1.0  2026-02-13  Added opc-principal/opc-obo-principal header masking;
                      added deep scan for embedded ST$ tokens in string values
"""

import io
import json
import logging
import gzip
import re
from fdk import response

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Key names whose string values should be fully redacted
REDACT_KEYS = frozenset({
    "credentials",
    "authorization",
    "Authorization",
    "opc-principal-token",
    "opc-principal",
    "opc-obo-principal",
    "x-auth-token",
})

# Value patterns that indicate a replayable secret (checked against ALL string values)
SECRET_VALUE_PATTERNS = [
    re.compile(r"ST\$"),                                # OCI session token (anywhere in string)
    re.compile(r"Signature\s+keyId=", re.IGNORECASE),   # OCI API signature
    re.compile(r"^Bearer\s+", re.IGNORECASE),           # Bearer token
    re.compile(r"^Basic\s+", re.IGNORECASE),            # Basic auth
]

REDACTION_PLACEHOLDER = "[REDACTED]"

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("audit-log-masking")


# ---------------------------------------------------------------------------
# Core masking logic
# ---------------------------------------------------------------------------

def _should_redact_value(value: str) -> bool:
    """Check if a string value matches known secret patterns."""
    for pattern in SECRET_VALUE_PATTERNS:
        if pattern.search(value):
            return True
    return False


def _mask_list(parent_key, items: list) -> list:
    """Process a list, masking string elements when appropriate."""
    result = []
    for item in items:
        if isinstance(item, str):
            if parent_key and parent_key.lower() in {k.lower() for k in REDACT_KEYS}:
                result.append(REDACTION_PLACEHOLDER)
            elif _should_redact_value(item):
                result.append(REDACTION_PLACEHOLDER)
            else:
                result.append(item)
        elif isinstance(item, (dict, list)):
            result.append(mask_sensitive_fields(item))
        else:
            result.append(item)
    return result


def mask_sensitive_fields(data):
    """Recursively traverse a parsed JSON structure and redact
    replayable authentication credentials."""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                if key.lower() in {k.lower() for k in REDACT_KEYS}:
                    masked[key] = REDACTION_PLACEHOLDER
                elif _should_redact_value(value):
                    masked[key] = REDACTION_PLACEHOLDER
                else:
                    masked[key] = value
            elif isinstance(value, list):
                masked[key] = _mask_list(key, value)
            elif isinstance(value, dict):
                masked[key] = mask_sensitive_fields(value)
            else:
                masked[key] = value
        return masked

    elif isinstance(data, list):
        return _mask_list(None, data)

    return data


# ---------------------------------------------------------------------------
# FDK handler — entry point for Service Connector "function task"
# ---------------------------------------------------------------------------

def handler(ctx, data: io.BytesIO = None):
    """OCI Functions entry point for Service Connector Hub.

    Accepts audit log batches (JSON array or single object,
    optionally gzip-compressed), masks sensitive fields,
    and returns the result for forwarding to the SIEM target.
    """
    body = b""
    try:
        body = data.getvalue() if data else b""
        if not body:
            return _json_response(ctx, [])

        # Decompress if gzipped
        if body[:2] == b"\x1f\x8b":
            try:
                body = gzip.decompress(body)
            except Exception as e:
                logger.warning(f"Gzip decompression failed, treating as raw: {e}")

        # Parse JSON
        try:
            payload = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"JSON parse failed: {e}")
            return _raw_response(ctx, body)

        # Normalize to list
        if isinstance(payload, dict):
            events = [payload]
            was_single = True
        elif isinstance(payload, list):
            events = payload
            was_single = False
        else:
            return _raw_response(ctx, body)

        # Mask each event
        masked_events = [mask_sensitive_fields(event) for event in events]

        # Return same shape as received
        output = masked_events[0] if was_single else masked_events
        return _json_response(ctx, output)

    except Exception as e:
        logger.error(f"Unhandled error in masking function: {e}", exc_info=True)
        # Never break the pipeline — return original data on failure
        return _raw_response(ctx, body)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------

def _json_response(ctx, data):
    return response.Response(
        ctx,
        response_data=json.dumps(data, separators=(",", ":")),
        headers={"Content-Type": "application/json"},
    )


def _raw_response(ctx, body: bytes):
    return response.Response(
        ctx,
        response_data=body.decode("utf-8", errors="replace"),
        headers={"Content-Type": "application/json"},
    )
