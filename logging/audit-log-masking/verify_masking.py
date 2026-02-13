"""
OCI Audit Log Masking — Stream Verification Script
====================================================
Reads messages from an OCI Streaming topic, decodes them,
and validates that sensitive fields are masked while
operational fields are preserved.

Usage:
  python3 verify_masking.py --stream-id <stream-ocid>
  python3 verify_masking.py --stream-id <stream-ocid> --limit 5 --raw

Prerequisites:
  - OCI CLI configured (~/.oci/config) or running in Cloud Shell
  - pip install oci  (pre-installed in Cloud Shell)

Author:  Rishabh Ghosh (rishabh.g.ghosh@oracle.com)
Version: 1.1.0
Date:    2026-02-13

Changelog:
  1.0.0  2026-02-13  Initial release
  1.1.0  2026-02-13  Auto-detect field paths (data.* vs logContent.data.*)
"""

import argparse
import base64
import json
import sys

try:
    import oci
except ImportError:
    print("ERROR: 'oci' SDK not found. Install with: pip install oci")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Fields to check
# ---------------------------------------------------------------------------

# These should be redacted
EXPECT_REDACTED = [
    ("credentials", ["identity", "credentials"]),
    ("Authorization", ["request", "headers", "Authorization"]),
    ("opc-principal", ["request", "headers", "opc-principal"]),
    ("opc-obo-principal", ["request", "headers", "opc-obo-principal"]),
]

# These should be preserved (non-empty)
EXPECT_PRESERVED = [
    ("principalId", ["identity", "principalId"]),
    ("principalName", ["identity", "principalName"]),
    ("ipAddress", ["identity", "ipAddress"]),
    ("tenantId", ["identity", "tenantId"]),
    ("request.action", ["request", "action"]),
    ("request.path", ["request", "path"]),
]


def find_audit_data(event):
    """Auto-detect where the audit data lives in the event.
    Service Connector may wrap it as:
      - { data: { identity: ... } }            (Streaming target)
      - { logContent: { data: { identity: ... } } }  (other targets)
    """
    if isinstance(event, dict):
        # Direct: data.identity
        if "data" in event and isinstance(event["data"], dict):
            if "identity" in event["data"]:
                return event["data"]
            # Wrapped: data.logContent.data or logContent.data
            if "logContent" in event["data"]:
                lc = event["data"]["logContent"]
                if isinstance(lc, dict) and "data" in lc:
                    return lc["data"]
        if "logContent" in event and isinstance(event["logContent"], dict):
            lc = event["logContent"]
            if "data" in lc:
                return lc["data"]
        # Fallback: maybe the event itself is the audit data
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


def check_redacted(value):
    """Check if a value looks properly redacted."""
    if isinstance(value, str):
        return value.startswith("[REDACTED]")
    if isinstance(value, list):
        return all(
            isinstance(v, str) and v.startswith("[REDACTED]") for v in value
        )
    return False


def validate_event(event, index):
    """Validate a single audit log event and print results."""
    print(f"\n{'=' * 60}")
    print(f"  Message {index}")
    print(f"{'=' * 60}")

    audit_data = find_audit_data(event)
    if audit_data is None:
        print("  ⚠  Could not locate audit data in message")
        return False

    # Show basic event info
    event_type = event.get("type") or audit_data.get("eventType") or "unknown"
    event_name = audit_data.get("eventName", "")
    auth_type = ""
    found, identity = resolve_path(audit_data, ["identity"])
    if found and isinstance(identity, dict):
        auth_type = identity.get("authType", "")

    print(f"  Event:     {event_name or event_type}")
    print(f"  Auth type: {auth_type}")
    print()

    passed = 0
    failed = 0
    skipped = 0

    # Check redacted fields
    for label, path in EXPECT_REDACTED:
        found, value = resolve_path(audit_data, path)
        if not found or value is None:
            skipped += 1
            continue
        if check_redacted(value):
            display = value if isinstance(value, str) else value[0]
            print(f"  ✅ {label}: {display}")
            passed += 1
        elif value == "***":
            # OCI already masked it at source
            print(f"  ✅ {label}: *** (masked by OCI at source)")
            passed += 1
        else:
            display = str(value)[:80]
            print(f"  ❌ {label}: NOT REDACTED → {display}")
            failed += 1

    # Check preserved fields
    for label, path in EXPECT_PRESERVED:
        found, value = resolve_path(audit_data, path)
        if not found or value is None or value == "":
            skipped += 1
            continue
        if not str(value).startswith("[REDACTED]"):
            display = str(value)[:80]
            print(f"  ✅ {label}: {display}")
            passed += 1
        else:
            print(f"  ❌ {label}: unexpectedly redacted")
            failed += 1

    print()
    if passed == 0 and failed == 0:
        print(f"  Result: no checkable fields (all {skipped} skipped)")
    else:
        print(f"  Result: {passed} passed, {failed} failed, {skipped} skipped")
    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="Verify OCI audit log masking by reading from a Streaming topic"
    )
    parser.add_argument(
        "--stream-id", required=True, help="OCID of the OCI Stream"
    )
    parser.add_argument(
        "--limit", type=int, default=5,
        help="Number of messages to read (default: 5)"
    )
    parser.add_argument(
        "--profile", default="DEFAULT",
        help="OCI config profile name (default: DEFAULT)"
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Also print the full decoded JSON for each message"
    )
    args = parser.parse_args()

    # --- Connect to OCI Streaming ---
    print(f"\nConnecting to stream: {args.stream_id}")
    print(f"Reading up to {args.limit} messages...\n")

    try:
        config = oci.config.from_file(profile_name=args.profile)
    except Exception:
        print("OCI config not found, trying instance principal...")
        signer = oci.auth.signers.get_resource_principals_signer()
        config = {}
        stream_client = oci.streaming.StreamClient(
            config={}, signer=signer, service_endpoint=""
        )

    # Get stream info to find the endpoint
    sc_admin = oci.streaming.StreamAdminClient(config)
    stream = sc_admin.get_stream(args.stream_id).data
    endpoint = stream.messages_endpoint
    print(f"Stream endpoint: {endpoint}")

    stream_client = oci.streaming.StreamClient(config, service_endpoint=endpoint)

    # Create cursor from the beginning
    cursor_response = stream_client.create_cursor(
        args.stream_id,
        oci.streaming.models.CreateCursorDetails(
            partition="0",
            type="TRIM_HORIZON"
        )
    )
    cursor = cursor_response.data.value

    # Read messages
    messages_response = stream_client.get_messages(
        args.stream_id,
        cursor,
        limit=args.limit
    )
    messages = messages_response.data

    if not messages:
        print("No messages found in the stream.")
        print("Trigger some audit events (browse OCI console) and wait ~2 minutes.")
        sys.exit(0)

    print(f"Retrieved {len(messages)} message(s)")

    # --- Validate each message ---
    all_passed = True
    has_checkable = False
    for i, msg in enumerate(messages, 1):
        try:
            decoded = base64.b64decode(msg.value).decode("utf-8")
            event = json.loads(decoded)
        except Exception as e:
            print(f"\n⚠  Message {i}: failed to decode — {e}")
            all_passed = False
            continue

        if args.raw:
            print(f"\n--- Raw JSON (Message {i}) ---")
            print(json.dumps(event, indent=2)[:3000])

        if not validate_event(event, i):
            all_passed = False

    # --- Summary ---
    print(f"\n{'=' * 60}")
    if all_passed:
        print("  🎉 ALL MESSAGES VALIDATED — masking is working correctly")
    else:
        print("  ⚠  SOME CHECKS FAILED — review output above")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
