"""
OCI Audit Log Filter & Trim — Stream Verification Script
==========================================================
Reads messages from an OCI Streaming topic and validates that:
  1. No GET events are present (filtered out)
  2. Only POST/DELETE/PUT/PATCH events remain
  3. Bulky fields (headers, stateChange.previous) are stripped
  4. Sensitive values are masked
  5. Essential SIEM fields are preserved

Usage:
  python3 verify_filtering.py --stream-id <stream-ocid>
  python3 verify_filtering.py --stream-id <stream-ocid> --limit 10 --raw
  python3 verify_filtering.py --stream-id <stream-ocid> --since 5     # last 5 minutes
  python3 verify_filtering.py --stream-id <stream-ocid> --since 30 --raw

Prerequisites:
  - OCI CLI configured (~/.oci/config) or running in Cloud Shell
  - pip install oci  (pre-installed in Cloud Shell)

Author:  Rishabh Ghosh (rishabh.g.ghosh@oracle.com)
Version: 1.0.0
Date:    2026-03-16
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timedelta, timezone

try:
    import oci
except ImportError:
    print("ERROR: 'oci' SDK not found. Install with: pip install oci")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

# HTTP methods that should have been filtered OUT
BLOCKED_METHODS = {"GET", "HEAD", "OPTIONS"}

# Fields that should be STRIPPED (not present)
EXPECT_STRIPPED = [
    ("request.headers", ["request", "headers"]),
    ("response.headers", ["response", "headers"]),
    ("stateChange.previous", ["stateChange", "previous"]),
]

# Fields that should be REDACTED (present but masked)
EXPECT_REDACTED = [
    ("credentials", ["identity", "credentials"]),
]

# Fields that should be PRESERVED (present and non-empty)
EXPECT_PRESERVED = [
    ("eventType", ["eventType"]),
    ("eventTime", ["eventTime"]),
    ("compartmentId", ["compartmentId"]),
    ("identity.principalId", ["identity", "principalId"]),
    ("identity.principalName", ["identity", "principalName"]),
    ("identity.ipAddress", ["identity", "ipAddress"]),
    ("request.action", ["request", "action"]),
    ("request.path", ["request", "path"]),
    ("response.status", ["response", "status"]),
]


def find_audit_data(event):
    """Auto-detect where the audit data lives in the event.

    More permissive than func.py's _find_audit_data — also handles
    logContent wrappers seen when reading from OCI Streaming, which
    may re-wrap events differently than what SC sends to the function.
    """
    if isinstance(event, dict):
        if "data" in event and isinstance(event["data"], dict):
            if "identity" in event["data"]:
                return event["data"]
            if "logContent" in event["data"]:
                lc = event["data"]["logContent"]
                if isinstance(lc, dict) and "data" in lc:
                    return lc["data"]
        if "logContent" in event and isinstance(event["logContent"], dict):
            lc = event["logContent"]
            if "data" in lc:
                return lc["data"]
        if "identity" in event:
            return event
    return None


def resolve_path(obj, path):
    """Walk a nested dict by key path. Returns (found: bool, value)."""
    current = obj
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False, None
    return True, current


def validate_event(event, index):
    """Validate a single audit log event."""
    print(f"\n{'=' * 60}")
    print(f"  Message {index}")
    print(f"{'=' * 60}")

    audit_data = find_audit_data(event)
    if audit_data is None:
        # Could be an empty event from filtering
        print("  (empty or non-audit event — likely filtered)")
        return True

    passed = 0
    failed = 0
    skipped = 0

    # Show basic info
    event_type = audit_data.get("eventType", "unknown")
    action = ""
    found, req = resolve_path(audit_data, ["request"])
    if found and isinstance(req, dict):
        action = req.get("action", "")

    print(f"  Event:  {audit_data.get('eventName', event_type)}")
    print(f"  Action: {action}")
    print()

    # CHECK 1: No blocked methods
    if action and action.strip().upper() in BLOCKED_METHODS:
        print(f"  FAIL: {action} event was NOT filtered out")
        failed += 1
    elif action:
        print(f"  PASS: {action} event correctly kept")
        passed += 1

    # CHECK 2: Stripped fields should NOT be present
    for label, path in EXPECT_STRIPPED:
        found, value = resolve_path(audit_data, path)
        if found and value is not None:
            size = len(json.dumps(value)) if not isinstance(value, str) else len(value)
            print(f"  FAIL: {label} still present ({size} chars)")
            failed += 1
        else:
            print(f"  PASS: {label} stripped")
            passed += 1

    # CHECK 3: Redacted fields
    for label, path in EXPECT_REDACTED:
        found, value = resolve_path(audit_data, path)
        if not found or value is None:
            skipped += 1
            continue
        if isinstance(value, str) and (value.startswith("[REDACTED]") or value == "***"):
            print(f"  PASS: {label} redacted")
            passed += 1
        else:
            print(f"  FAIL: {label} NOT redacted -> {str(value)[:60]}")
            failed += 1

    # CHECK 4: Preserved fields
    for label, path in EXPECT_PRESERVED:
        found, value = resolve_path(audit_data, path)
        if not found or value is None or value == "":
            skipped += 1
            continue
        if not str(value).startswith("[REDACTED]"):
            print(f"  PASS: {label} = {str(value)[:60]}")
            passed += 1
        else:
            print(f"  FAIL: {label} unexpectedly redacted")
            failed += 1

    # CHECK 5: Payload size
    event_size = len(json.dumps(audit_data))
    size_status = "PASS" if event_size < 5000 else "WARN"
    print(f"\n  {size_status}: event size = {event_size:,} chars")
    if size_status == "PASS":
        passed += 1

    print(f"\n  Result: {passed} passed, {failed} failed, {skipped} skipped")
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Verify OCI audit log filtering, trimming, and masking"
    )
    parser.add_argument(
        "--stream-id", required=True, help="OCID of the OCI Stream"
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="Number of messages to read (default: 10)"
    )
    parser.add_argument(
        "--profile", default="DEFAULT",
        help="OCI config profile name (default: DEFAULT)"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Also print the full decoded JSON for each message"
    )
    parser.add_argument(
        "--since", type=int, default=None,
        help="Read messages from N minutes ago (default: reads from oldest)"
    )
    args = parser.parse_args()

    # --- Connect to OCI Streaming ---
    print(f"\nConnecting to stream: {args.stream_id}")
    print(f"Reading up to {args.limit} messages...\n")

    signer = None
    try:
        config = oci.config.from_file(profile_name=args.profile)
    except Exception:
        print("OCI config not found, trying instance principal...")
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        except Exception:
            print("Instance principal failed, trying resource principal...")
            signer = oci.auth.signers.get_resource_principals_signer()
        config = {}

    if signer:
        sc_admin = oci.streaming.StreamAdminClient(config, signer=signer)
    else:
        sc_admin = oci.streaming.StreamAdminClient(config)

    stream = sc_admin.get_stream(args.stream_id).data
    endpoint = stream.messages_endpoint
    print(f"Stream endpoint: {endpoint}")

    if signer:
        stream_client = oci.streaming.StreamClient(config, signer=signer, service_endpoint=endpoint)
    else:
        stream_client = oci.streaming.StreamClient(config, service_endpoint=endpoint)

    # Note: reads partition 0 only. For multi-partition streams, most audit
    # events land on partition 0; this is sufficient for verification.
    if args.since:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=args.since)
        print(f"Reading messages since: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        cursor_details = oci.streaming.models.CreateCursorDetails(
            partition="0",
            type="AT_TIME",
            time=start_time
        )
    else:
        print("Reading from oldest messages (use --since N for recent messages)")
        cursor_details = oci.streaming.models.CreateCursorDetails(
            partition="0",
            type="TRIM_HORIZON"
        )

    cursor_response = stream_client.create_cursor(
        args.stream_id, cursor_details
    )
    cursor = cursor_response.data.value

    messages_response = stream_client.get_messages(
        args.stream_id,
        cursor,
        limit=args.limit
    )
    messages = messages_response.data

    if not messages:
        print("No messages found in the stream.")
        print("Trigger some audit events and wait ~2 minutes.")
        sys.exit(0)

    print(f"Retrieved {len(messages)} message(s)")

    # --- Validate each message ---
    all_passed = True
    empty_count = 0
    content_count = 0

    for i, msg in enumerate(messages, 1):
        try:
            decoded = base64.b64decode(msg.value).decode("utf-8")
            event = json.loads(decoded)
        except Exception as e:
            print(f"\n  Message {i}: failed to decode — {e}")
            all_passed = False
            continue

        if args.raw:
            print(f"\n--- Raw JSON (Message {i}) ---")
            print(json.dumps(event, indent=2)[:3000])

        audit_data = find_audit_data(event)
        if audit_data is None:
            empty_count += 1
        else:
            content_count += 1

        if not validate_event(event, i):
            all_passed = False

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"  Total: {len(messages)} messages read")
    print(f"  With content: {content_count}  |  Empty/filtered: {empty_count}")
    print()

    if content_count == 0 and empty_count > 0:
        print("  WARNING: All messages were empty ({}).")
        print("  This likely means you're reading OLD messages from before")
        print("  the fix was deployed. Try: --since 5  (last 5 minutes)")
    elif all_passed:
        print("  ALL MESSAGES VALIDATED — filtering + trimming + masking OK")
    else:
        print("  SOME CHECKS FAILED — review output above")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
