"""
OCI Audit Log — Filter, Trim & Mask Function (Part 2)
======================================================
Deploy as a "Configure function task" in OCI Service Connector Hub.

Builds on audit-log-masking (Part 1) with three additional capabilities:

  1. EVENT FILTERING  — Drops all GET requests; only POST, DELETE, PUT/PATCH
     (update) events are forwarded to the SIEM target.
  2. PAYLOAD TRIMMING — Strips verbose fields (full headers, stateChange
     diffs, additionalDetails) to dramatically reduce per-event size
     from ~16K chars to ~2-3K chars.
  3. CREDENTIAL MASKING — Same redaction logic as Part 1 for any
     remaining sensitive values.

Author:  Rishabh Ghosh (rishabh.g.ghosh@oracle.com)
Version: 1.0.0
Date:    2026-03-16

Changelog:
  1.0.0  2026-03-16  Initial release — filtering + trimming + masking
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

# HTTP methods to KEEP — everything else (GET, HEAD, OPTIONS, etc.) is dropped
ALLOWED_METHODS = frozenset({"POST", "DELETE", "PUT", "PATCH"})

# Top-level audit event fields to KEEP (everything else is stripped)
# This whitelist approach gives the best size reduction while preserving
# all the fields a SIEM needs for detection and correlation.
KEEP_TOP_LEVEL = frozenset({
    "eventType",
    "eventName",
    "compartmentId",
    "compartmentName",
    "eventTime",
    "principalId",
    "resourceId",
    "resourceName",
    "availabilityDomain",
    "freeformTags",
    "definedTags",
    "identity",
    "request",
    "response",
    "stateChange",
})

# Fields to REMOVE from request/response sub-objects (bulkiest parts)
STRIP_FROM_REQUEST = frozenset({
    "headers",        # Authorization, opc-principal, etc. — bulk of the 16K
})

STRIP_FROM_RESPONSE = frozenset({
    "headers",        # Verbose response headers (opc-request-id, etc.)
})

# Within stateChange, only keep current state (drop previous — often huge)
KEEP_STATE_CHANGE_KEYS = frozenset({
    "current",
})

# Key names whose string values should be fully redacted (safety net for
# any remaining credential values after trimming)
REDACT_KEYS = frozenset({
    "credentials",
    "authorization",
    "Authorization",
    "opc-principal-token",
    "opc-principal",
    "opc-obo-principal",
    "x-auth-token",
})

# Value patterns that indicate a replayable secret
SECRET_VALUE_PATTERNS = [
    re.compile(r"ST\$"),
    re.compile(r"Signature\s+keyId=", re.IGNORECASE),
    re.compile(r"^Bearer\s+", re.IGNORECASE),
    re.compile(r"^Basic\s+", re.IGNORECASE),
]

REDACTION_PLACEHOLDER = "[REDACTED]"

# Pre-computed lowercase set for fast key lookups during masking
REDACT_KEYS_LOWER = frozenset(k.lower() for k in REDACT_KEYS)

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("audit-log-filter-trim")


# ---------------------------------------------------------------------------
# Event filtering — decide whether to keep or drop an event
# ---------------------------------------------------------------------------

def _find_audit_data(event):
    """Locate the actual audit data inside an event.

    Service Connector sends audit events wrapped as:
      - { "data": { "request": ..., "identity": ... } }   (common)
      - { "request": ..., "identity": ... }                (direct)

    NOTE: The verify_filtering.py script has a more permissive version of
    this function that also handles logContent wrappers (seen when reading
    from OCI Streaming). This function only needs to handle what Service
    Connector Hub sends to the function task.
    """
    if not isinstance(event, dict):
        return None
    # Wrapped under "data"
    if "data" in event and isinstance(event["data"], dict):
        if "request" in event["data"] or "identity" in event["data"]:
            return event["data"]
    # Direct audit data
    if "request" in event or "identity" in event:
        return event
    return None


def _extract_http_method(event):
    """Extract the HTTP method from an audit event.

    OCI audit events store the method in request.action (e.g. "GET", "POST").
    Handles both direct and "data"-wrapped event structures.
    """
    audit = _find_audit_data(event)
    if audit is None:
        return None
    request = audit.get("request")
    if not isinstance(request, dict):
        return None
    action = request.get("action")
    if isinstance(action, str):
        return action.strip().upper()
    return None


def _should_keep_event(event):
    """Return True if the event should be forwarded to SIEM."""
    method = _extract_http_method(event)
    if method is None:
        # If we can't determine the method, keep the event to be safe
        return True
    return method in ALLOWED_METHODS


# ---------------------------------------------------------------------------
# Payload trimming — strip verbose fields to reduce size
# ---------------------------------------------------------------------------

def _trim_audit_data(audit):
    """Strip unnecessary fields from audit data to reduce payload size."""
    # Keep only whitelisted fields
    trimmed = {}
    for key in KEEP_TOP_LEVEL:
        if key in audit:
            trimmed[key] = audit[key]

    # Strip bulky sub-fields from request
    if "request" in trimmed and isinstance(trimmed["request"], dict):
        trimmed["request"] = {
            k: v for k, v in trimmed["request"].items()
            if k not in STRIP_FROM_REQUEST
        }

    # Strip bulky sub-fields from response
    if "response" in trimmed and isinstance(trimmed["response"], dict):
        trimmed["response"] = {
            k: v for k, v in trimmed["response"].items()
            if k not in STRIP_FROM_RESPONSE
        }

    # Trim stateChange — keep only current state
    if "stateChange" in trimmed and isinstance(trimmed["stateChange"], dict):
        trimmed["stateChange"] = {
            k: v for k, v in trimmed["stateChange"].items()
            if k in KEEP_STATE_CHANGE_KEYS
        }

    return trimmed


def trim_event(event):
    """Strip unnecessary fields from an audit event.

    Handles both direct audit data and "data"-wrapped events from
    Service Connector Hub.
    """
    if not isinstance(event, dict):
        return event

    # Wrapped under "data" — trim the inner audit data, preserve wrapper
    if "data" in event and isinstance(event["data"], dict):
        inner = event["data"]
        if "request" in inner or "identity" in inner:
            result = {k: v for k, v in event.items() if k != "data"}
            result["data"] = _trim_audit_data(inner)
            return result

    # Direct audit data
    if "request" in event or "identity" in event:
        return _trim_audit_data(event)

    return event


# ---------------------------------------------------------------------------
# Credential masking (same logic as Part 1)
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
            if parent_key and parent_key.lower() in REDACT_KEYS_LOWER:
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
                if key.lower() in REDACT_KEYS_LOWER:
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

    Pipeline: Filter (drop GETs) → Trim (strip bulk) → Mask (redact creds)
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

        # --- STEP 1: Filter — keep only POST/DELETE/PUT/PATCH ---
        filtered = [e for e in events if _should_keep_event(e)]

        if not filtered:
            # All events were filtered out — return empty array
            return _json_response(ctx, [])

        # --- STEP 2: Trim — strip verbose fields ---
        trimmed = [trim_event(e) for e in filtered]

        # --- STEP 3: Mask — redact any remaining credentials ---
        masked = [mask_sensitive_fields(e) for e in trimmed]

        # Return same shape as received (single object if input was single)
        if was_single:
            output = masked[0] if masked else {}
        else:
            output = masked

        return _json_response(ctx, output)

    except Exception as e:
        logger.error(f"Unhandled error in function: {e}", exc_info=True)
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
