#!/usr/bin/env python3
"""
OCI Alarm History Exporter
==========================
Exports alarm state transition history across all compartments in an OCI tenancy to CSV.

This script is STRICTLY READ-ONLY. It only calls:
  - list_compartments()     (READ)
  - list_alarms()           (READ)
  - get_alarm_history()     (READ)
  - get_topic()             (READ) — resolves ONS topic names
  - list_subscriptions()    (READ) — resolves where notifications are sent
No create/update/delete operations are performed.

Prerequisites:
    pip install oci

Authentication:
    Default: Instance Principals (run from an OCI compute instance with a dynamic group).
    Fallback: OCI config file (~/.oci/config) via --use-config-file flag.

Command Options:
    --days <int>              Number of days of history to retrieve.
                              Default: 90 (max allowed by OCI platform).
                              Values above 90 are automatically clamped.

    --output <filename>       Custom output CSV filename.
                              Default: oci_alarm_history_YYYYMMDD_HHMMSS.csv

    --compartment-id <ocid>   Scope the scan to a specific compartment and all its
                              sub-compartments (recursively). If omitted, the entire
                              tenancy is scanned.

    --use-config-file         Use ~/.oci/config file authentication instead of
                              instance principals. Use this when running from a
                              local machine or any non-OCI environment.

    --profile <name>          OCI config profile name. Only applies when used with
                              --use-config-file. Default: DEFAULT

Usage Examples:
    python oci_alarm_history.py                                         # instance principals, 90 days, full tenancy
    python oci_alarm_history.py --days 60                               # last 60 days only
    python oci_alarm_history.py --days 30 --output q1_audit.csv         # 30 days, custom filename
    python oci_alarm_history.py --compartment-id ocid1.compartment...   # specific compartment + children
    python oci_alarm_history.py --use-config-file                       # use ~/.oci/config instead
    python oci_alarm_history.py --use-config-file --profile PROD        # config file with named profile

CSV Output Columns:
    alarm_name                  Alarm display name
    alarm_id                    Alarm OCID
    severity                    Alarm severity (CRITICAL, ERROR, WARNING, INFO)
    parsed_status               Extracted state (FIRING, OK, RESET, SUSPENDED)
    transition_summary          Raw API summary text (e.g. "State transitioned from OK to Firing")
    timestamp                   When the history entry was recorded (UTC, RFC3339)
    timestamp_triggered         When the state actually changed (~3 min before timestamp)
    alarm_compartment_path      Full compartment tree path where the alarm DEFINITION lives
    alarm_compartment_id        Compartment OCID where the alarm is defined
    metric_target_path          Compartment tree path of the MONITORED resource.
                                NOTE: This can differ from alarm_compartment_path. OCI allows
                                cross-compartment monitoring — e.g. Team A creates an alarm in
                                their compartment that monitors metrics in Team B's compartment.
                                This is standard OCI behavior (alarm.metric_compartment_id).
    metric_namespace            OCI metric namespace (e.g. oci_computeagent)
    metric_query                MQL alarm query expression
    is_enabled                  Whether the alarm is currently enabled (True/False)
    lifecycle_state             Alarm lifecycle state (ACTIVE, DELETING, DELETED)
    notification_topic_names    ONS topic display names (semicolon-separated)
    notification_topic_ids      ONS topic OCIDs (semicolon-separated)
    notification_subscriptions  Where alerts go: "PROTOCOL:endpoint(STATE)" per subscription
                                e.g. "EMAIL:ops@acme.com(ACTIVE); SLACK:https://hooks.slack.com/...(ACTIVE)"

OCI Alarm History Retention: 90 days (platform limit).
Reference: https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/get-alarm-history.htm

Author: Rishabh Ghosh
"""

import oci
import csv
import sys
import re
import argparse
import time
from datetime import datetime, timedelta, timezone


# ──────────────────────────────────────────────────────────────────────────────
# Compartment hierarchy helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_all_compartments(identity_client, tenancy_id):
    """
    Retrieve all ACTIVE compartments in the tenancy recursively.
    Returns:
        compartments: list of compartment objects (including a synthetic root entry)
        compartment_map: dict of {ocid: compartment_object} for path building
    """
    print("Fetching all compartments in tenancy...")
    all_compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
        lifecycle_state="ACTIVE"
    ).data

    # Build lookup map
    compartment_map = {}
    for c in all_compartments:
        compartment_map[c.id] = c

    # Add synthetic root entry
    class RootCompartment:
        def __init__(self, ocid):
            self.id = ocid
            self.name = "root (tenancy)"
            self.compartment_id = None  # root has no parent

    root = RootCompartment(tenancy_id)
    compartment_map[tenancy_id] = root

    # Return root + all children
    all_with_root = [root] + list(all_compartments)
    print(f"  Found {len(all_with_root)} compartments (including root).")
    return all_with_root, compartment_map


def build_compartment_path(compartment_id, compartment_map):
    """
    Build the full compartment path from root, e.g.:
        root (tenancy) / NetworkCompartment / ProdSubnet
    """
    path_parts = []
    current_id = compartment_id
    visited = set()  # guard against circular references

    while current_id and current_id not in visited:
        visited.add(current_id)
        comp = compartment_map.get(current_id)
        if comp is None:
            path_parts.append(current_id[:20] + "...")  # truncated OCID as fallback
            break
        path_parts.append(comp.name)
        current_id = getattr(comp, 'compartment_id', None)

    path_parts.reverse()
    return " / ".join(path_parts)


# ──────────────────────────────────────────────────────────────────────────────
# Alarm history retrieval
# ──────────────────────────────────────────────────────────────────────────────

def parse_status_from_summary(summary_text):
    """
    Extract the alarm status from the history entry summary text.

    STATE_TRANSITION_HISTORY entries look like:
        "State transitioned from OK to Firing"
        "State transitioned from Firing to OK"
    STATE_HISTORY entries look like:
        "The alarm state is FIRING"

    Returns the latest status (e.g., "FIRING", "OK", "RESET", "SUSPENDED")
    or the raw summary if parsing fails.
    """
    summary_upper = summary_text.upper()

    # Pattern 1: "State transitioned from X to Y" → return Y
    match = re.search(r'TRANSITIONED\s+FROM\s+\w+\s+TO\s+(\w+)', summary_upper)
    if match:
        return match.group(1)

    # Pattern 2: "The alarm state is X" → return X
    match = re.search(r'STATE\s+IS\s+(\w+)', summary_upper)
    if match:
        return match.group(1)

    # Fallback: look for known status keywords anywhere
    for status in ["FIRING", "OK", "RESET", "SUSPENDED"]:
        if status in summary_upper:
            return status

    return summary_text[:50]  # truncated raw summary as last resort

def get_full_alarm_history(monitoring_client, alarm_id, time_start, time_end):
    """
    Retrieve all alarm history entries for a single alarm within the time window.
    Handles pagination automatically.
    Uses STATE_TRANSITION_HISTORY for cleaner firing/ok transitions.
    """
    all_entries = []
    page = None
    while True:
        kwargs = {
            "timestamp_greater_than_or_equal_to": time_start,
            "timestamp_less_than": time_end,
            "alarm_historytype": "STATE_TRANSITION_HISTORY",
        }
        if page:
            kwargs["page"] = page

        try:
            response = monitoring_client.get_alarm_history(alarm_id=alarm_id, **kwargs)
        except oci.exceptions.ServiceError as e:
            # Handle throttling (429) with a backoff
            if e.status == 429:
                print("    Rate limited, waiting 5s...")
                time.sleep(5)
                continue
            raise

        if response.data and response.data.entries:
            all_entries.extend(response.data.entries)

        # Check for next page
        page = response.headers.get("opc-next-page")
        if not page:
            break

    return all_entries


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def resolve_ons_subscriptions(ons_cp_client, ons_dp_client, all_alarms):
    """
    For all unique ONS topic OCIDs across all alarms, resolve:
      - Topic display name
      - All subscriptions (protocol, endpoint, state)
    Returns a dict: {topic_ocid: {"name": str, "subscriptions": [...]}}
    Caches results to avoid duplicate API calls.
    """
    # Collect unique topic OCIDs (skip stream OCIDs)
    unique_topics = set()
    for alarm, _ in all_alarms:
        for dest in (getattr(alarm, 'destinations', []) or []):
            if dest.startswith("ocid1.onstopic."):
                unique_topics.add(dest)

    if not unique_topics:
        print("  No ONS topics found in alarm destinations.")
        return {}

    print(f"\nResolving {len(unique_topics)} unique ONS topics...")
    topic_cache = {}

    for topic_id in unique_topics:
        topic_info = {"name": "N/A", "subscriptions": []}

        # Step 1: Get topic details (name, compartment_id)
        try:
            topic = ons_cp_client.get_topic(topic_id=topic_id).data
            topic_info["name"] = getattr(topic, 'name', "N/A") or "N/A"
            topic_compartment_id = topic.compartment_id
        except oci.exceptions.ServiceError as e:
            if e.status in (403, 404):
                topic_info["name"] = f"ACCESS_DENIED({e.status})"
                topic_cache[topic_id] = topic_info
                print(f"  SKIP topic {topic_id[:40]}... ({e.status})")
                continue
            elif e.status == 429:
                time.sleep(5)
                try:
                    topic = ons_cp_client.get_topic(topic_id=topic_id).data
                    topic_info["name"] = getattr(topic, 'name', "N/A") or "N/A"
                    topic_compartment_id = topic.compartment_id
                except Exception:
                    topic_info["name"] = "RATE_LIMITED"
                    topic_cache[topic_id] = topic_info
                    continue
            else:
                topic_info["name"] = f"ERROR({e.status})"
                topic_cache[topic_id] = topic_info
                continue
        except Exception as e:
            topic_info["name"] = f"ERROR({e})"
            topic_cache[topic_id] = topic_info
            continue

        # Step 2: List subscriptions for this topic
        try:
            subs = oci.pagination.list_call_get_all_results(
                ons_dp_client.list_subscriptions,
                compartment_id=topic_compartment_id,
                topic_id=topic_id,
            ).data
            for sub in subs:
                topic_info["subscriptions"].append({
                    "id":       getattr(sub, 'id', "N/A"),
                    "protocol": getattr(sub, 'protocol', "N/A") or "N/A",
                    "endpoint": getattr(sub, 'endpoint', "N/A") or "N/A",
                    "state":    getattr(sub, 'lifecycle_state', "N/A") or "N/A",
                })
        except oci.exceptions.ServiceError as e:
            if e.status not in (403, 404):
                print(f"  WARN: Could not list subscriptions for {topic_info['name']}: {e.status}")
        except Exception:
            pass

        topic_cache[topic_id] = topic_info
        sub_count = len(topic_info["subscriptions"])
        print(f"  {topic_info['name']}: {sub_count} subscription(s)")
        time.sleep(0.15)

    return topic_cache


def format_subscription_details(destinations, topic_cache):
    """
    Given an alarm's destination OCIDs and the resolved topic cache,
    return formatted strings for topic names and subscription details.
    """
    topic_names = []
    sub_details = []

    for dest in (destinations or []):
        if dest.startswith("ocid1.onstopic.") and dest in topic_cache:
            info = topic_cache[dest]
            topic_names.append(info["name"])
            for sub in info["subscriptions"]:
                sub_details.append(f"{sub['protocol']}:{sub['endpoint']}({sub['state']})")
        elif dest.startswith("ocid1.stream."):
            topic_names.append(f"Stream:{dest[:50]}...")
        else:
            topic_names.append(dest[:50])

    return (
        "; ".join(topic_names) if topic_names else "None",
        "; ".join(sub_details) if sub_details else "None",
        "; ".join(destinations) if destinations else "None",
    )

def main():
    parser = argparse.ArgumentParser(
        description="Export OCI alarm history to CSV (read-only, tenancy-wide)."
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Number of days of history to retrieve (max 90, default 90)."
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV filename (default: auto-generated with timestamp)."
    )
    parser.add_argument(
        "--compartment-id", type=str, default=None,
        help="Scope to a specific compartment OCID instead of tenancy root. "
             "Sub-compartments are still included."
    )
    parser.add_argument(
        "--use-config-file", action="store_true", default=False,
        help="Use ~/.oci/config file auth instead of instance principals."
    )
    parser.add_argument(
        "--profile", type=str, default="DEFAULT",
        help="OCI config profile name (only used with --use-config-file)."
    )
    args = parser.parse_args()

    # Clamp days to 90 (OCI platform limit)
    days = min(args.days, 90)
    if args.days > 90:
        print(f"WARNING: OCI retains alarm history for max 90 days. Clamping from {args.days} to 90.")

    # Time window
    time_end = datetime.now(timezone.utc)
    time_start = time_end - timedelta(days=days)
    print(f"Time window: {time_start.strftime('%Y-%m-%d %H:%M UTC')} → {time_end.strftime('%Y-%m-%d %H:%M UTC')} ({days} days)")

    # ── Authentication ────────────────────────────────────────────────────
    if args.use_config_file:
        print("Auth: Using config file authentication...")
        try:
            config = oci.config.from_file(profile_name=args.profile)
        except Exception as e:
            sys.exit(f"ERROR: Failed to load OCI config (profile={args.profile}): {e}")
        oci.config.validate_config(config)
        tenancy_id = config["tenancy"]
        identity_client = oci.identity.IdentityClient(config)
        monitoring_client = oci.monitoring.MonitoringClient(config)
        ons_cp_client = oci.ons.NotificationControlPlaneClient(config)
        ons_dp_client = oci.ons.NotificationDataPlaneClient(config)
    else:
        print("Auth: Using instance principals...")
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        except Exception as e:
            sys.exit(
                f"ERROR: Instance principals auth failed: {e}\n"
                "  Are you running this on an OCI compute instance with a matching dynamic group?\n"
                "  To use config file auth instead, add: --use-config-file"
            )
        tenancy_id = signer.tenancy_id
        identity_client = oci.identity.IdentityClient(config={}, signer=signer)
        monitoring_client = oci.monitoring.MonitoringClient(config={}, signer=signer)
        ons_cp_client = oci.ons.NotificationControlPlaneClient(config={}, signer=signer)
        ons_dp_client = oci.ons.NotificationDataPlaneClient(config={}, signer=signer)

    # ── Determine root compartment for scanning ──────────────────────────
    root_compartment_id = args.compartment_id or tenancy_id

    # ── Get compartment hierarchy ────────────────────────────────────────
    compartments, compartment_map = get_all_compartments(identity_client, tenancy_id)

    # If scoped to a specific compartment, filter the list
    if args.compartment_id:
        scoped_ids = {args.compartment_id}
        # Iterate until no new IDs are added (handles arbitrary nesting depth)
        changed = True
        while changed:
            changed = False
            for c in compartments:
                if c.id not in scoped_ids and getattr(c, 'compartment_id', None) in scoped_ids:
                    scoped_ids.add(c.id)
                    changed = True
        compartments = [c for c in compartments if c.id in scoped_ids]
        print(f"  Scoped to {len(compartments)} compartments under {args.compartment_id[:30]}...")

    # ── List all alarms across compartments ──────────────────────────────
    print(f"\nListing alarms across {len(compartments)} compartments...")
    all_alarms = []
    compartments_with_alarms = 0

    for comp in compartments:
        try:
            alarms = oci.pagination.list_call_get_all_results(
                monitoring_client.list_alarms,
                compartment_id=comp.id,
            ).data
            if alarms:
                compartments_with_alarms += 1
                all_alarms.extend([(alarm, comp.id) for alarm in alarms])
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                continue  # compartment may not have monitoring enabled
            elif e.status == 403:
                print(f"  SKIP (403 Forbidden): {comp.name}")
                continue
            elif e.status == 429:
                print("  Rate limited, waiting 5s...")
                time.sleep(5)
                # Retry once
                try:
                    alarms = oci.pagination.list_call_get_all_results(
                        monitoring_client.list_alarms,
                        compartment_id=comp.id,
                    ).data
                    if alarms:
                        compartments_with_alarms += 1
                        all_alarms.extend([(alarm, comp.id) for alarm in alarms])
                except Exception:
                    print(f"  SKIP (retry failed): {comp.name}")
            else:
                print(f"  SKIP ({e.status} {e.code}): {comp.name}")

    print(f"  Found {len(all_alarms)} alarms across {compartments_with_alarms} compartments.")

    if not all_alarms:
        print("\nNo alarms found. Nothing to export.")
        sys.exit(0)

    # ── Resolve ONS topic and subscription details ───────────────────────
    topic_cache = resolve_ons_subscriptions(ons_cp_client, ons_dp_client, all_alarms)

    # ── Retrieve history for each alarm ──────────────────────────────────
    print(f"\nRetrieving alarm history for {len(all_alarms)} alarms...")

    csv_rows = []
    alarms_with_history = 0
    total_entries = 0

    for idx, (alarm, alarm_compartment_id) in enumerate(all_alarms, 1):
        alarm_name = alarm.display_name
        print(f"  [{idx}/{len(all_alarms)}] {alarm_name}...", end=" ", flush=True)

        try:
            entries = get_full_alarm_history(
                monitoring_client, alarm.id, time_start, time_end
            )
        except oci.exceptions.ServiceError as e:
            print(f"ERROR ({e.status} {e.code})")
            continue
        except Exception as e:
            print(f"ERROR ({e})")
            continue

        if entries:
            alarms_with_history += 1
            total_entries += len(entries)
            print(f"{len(entries)} entries")
        else:
            print("no history")

        # Build the compartment path for this alarm
        comp_path = build_compartment_path(alarm_compartment_id, compartment_map)

        # Resolve the metric target compartment path (where the alarm monitors)
        metric_comp_id = getattr(alarm, 'metric_compartment_id', None) or alarm_compartment_id
        metric_comp_path = build_compartment_path(metric_comp_id, compartment_map)

        # Extract alarm metadata
        severity = getattr(alarm, 'severity', "N/A") or "N/A"
        namespace = getattr(alarm, 'namespace', "N/A") or "N/A"
        query = getattr(alarm, 'query', "N/A") or "N/A"
        is_enabled = getattr(alarm, 'is_enabled', None)
        lifecycle_state = getattr(alarm, 'lifecycle_state', "N/A") or "N/A"

        # Resolve notification destinations with subscription details
        destinations = getattr(alarm, 'destinations', []) or []
        topic_names_str, sub_details_str, topic_ids_str = format_subscription_details(
            destinations, topic_cache
        )

        if entries:
            for entry in entries:
                # AlarmHistoryEntry fields: summary (str), timestamp (datetime),
                # timestamp_triggered (datetime, optional)
                entry_summary = getattr(entry, 'summary', "N/A") or "N/A"
                entry_timestamp = getattr(entry, 'timestamp', None)
                entry_triggered = getattr(entry, 'timestamp_triggered', None)

                # Parse the status from the summary text
                # STATE_TRANSITION_HISTORY entries look like:
                #   "State transitioned from OK to Firing"
                #   "State transitioned from Firing to OK"
                # STATE_HISTORY entries look like:
                #   "The alarm state is FIRING"
                parsed_status = parse_status_from_summary(entry_summary)

                csv_rows.append({
                    "alarm_name":                alarm_name,
                    "alarm_id":                  alarm.id,
                    "severity":                  severity,
                    "parsed_status":             parsed_status,
                    "transition_summary":        entry_summary,
                    "timestamp":                 str(entry_timestamp) if entry_timestamp else "N/A",
                    "timestamp_triggered":       str(entry_triggered) if entry_triggered else "N/A",
                    "alarm_compartment_path":    comp_path,
                    "alarm_compartment_id":      alarm_compartment_id,
                    "metric_target_path":        metric_comp_path,
                    "metric_namespace":          namespace,
                    "metric_query":              query,
                    "is_enabled":                str(is_enabled) if is_enabled is not None else "N/A",
                    "lifecycle_state":           lifecycle_state,
                    "notification_topic_names":  topic_names_str,
                    "notification_topic_ids":    topic_ids_str,
                    "notification_subscriptions": sub_details_str,
                })
        else:
            # Still include alarms with no history (so auditors see the full alarm inventory)
            csv_rows.append({
                "alarm_name":                alarm_name,
                "alarm_id":                  alarm.id,
                "severity":                  severity,
                "parsed_status":             "NO_HISTORY_IN_WINDOW",
                "transition_summary":        "No state transitions recorded in the selected time window",
                "timestamp":                 "N/A",
                "timestamp_triggered":       "N/A",
                "alarm_compartment_path":    comp_path,
                "alarm_compartment_id":      alarm_compartment_id,
                "metric_target_path":        metric_comp_path,
                "metric_namespace":          namespace,
                "metric_query":              query,
                "is_enabled":                str(is_enabled) if is_enabled is not None else "N/A",
                "lifecycle_state":           lifecycle_state,
                "notification_topic_names":  topic_names_str,
                "notification_topic_ids":    topic_ids_str,
                "notification_subscriptions": sub_details_str,
            })

        # Small delay to stay under 10 TPS rate limit
        time.sleep(0.15)

    # ── Sort by timestamp (most recent first) ────────────────────────────
    csv_rows.sort(key=lambda r: r["timestamp"] if r["timestamp"] != "N/A" else "", reverse=True)

    # ── Write CSV ────────────────────────────────────────────────────────
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = args.output or f"oci_alarm_history_{timestamp_str}.csv"

    fieldnames = [
        "alarm_name",
        "alarm_id",
        "severity",
        "parsed_status",
        "transition_summary",
        "timestamp",
        "timestamp_triggered",
        "alarm_compartment_path",
        "alarm_compartment_id",
        "metric_target_path",
        "metric_namespace",
        "metric_query",
        "is_enabled",
        "lifecycle_state",
        "notification_topic_names",
        "notification_topic_ids",
        "notification_subscriptions",
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"  Compartments scanned:    {len(compartments)}")
    print(f"  Total alarms found:      {len(all_alarms)}")
    print(f"  Alarms with history:     {alarms_with_history}")
    print(f"  Total history entries:    {total_entries}")
    print(f"  ONS topics resolved:     {len(topic_cache)}")
    print(f"  Time window:             {days} days")
    print(f"  CSV rows written:        {len(csv_rows)}")
    print(f"  Output file:             {csv_file}")
    print("=" * 70)

    # ── Safety confirmation ──────────────────────────────────────────────
    print("\nREAD-ONLY CONFIRMATION: This script performed ZERO write/modify/delete")
    print("operations against any OCI resource. Only list/get API calls were made.")


if __name__ == "__main__":
    main()