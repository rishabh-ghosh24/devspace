#!/usr/bin/env python3
"""OCI Compute Availability Report Generator.

Generates self-contained HTML availability reports for OCI Compute VM instances
using CpuUtilization and instance_status metrics.
"""

import argparse
import sys

VERSION = "1.0"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate OCI Compute availability reports"
    )

    # Required
    parser.add_argument("--compartment-id", required=True, help="Target compartment OCID")

    # Authentication
    parser.add_argument("--auth", choices=["instance_principal", "config"],
                        default="instance_principal", help="Auth method (default: instance_principal)")
    parser.add_argument("--profile", default="DEFAULT", help="OCI config profile (default: DEFAULT)")

    # Reporting
    parser.add_argument("--days", type=int, choices=[7, 14, 30, 60, 90],
                        default=7, help="Reporting period in days (default: 7)")
    parser.add_argument("--sla-target", type=float, default=99.95,
                        help="SLA target %% (default: 99.95)")
    parser.add_argument("--running-only", action="store_true",
                        help="Only include RUNNING instances (default: all non-TERMINATED)")
    parser.add_argument("--region", help="OCI region override")
    parser.add_argument("--compartment-name", help="Compartment display name override")

    # Branding
    parser.add_argument("--title", help="Custom report title (top-right header)")
    parser.add_argument("--logo", help="Path to logo image (embedded as base64)")

    # Output
    parser.add_argument("--output", help="Output HTML file path")
    parser.add_argument("--upload", action="store_true", help="Upload to Object Storage")
    parser.add_argument("--bucket", default="availability-reports", help="Bucket name")
    parser.add_argument("--os-namespace", help="Object Storage namespace")
    parser.add_argument("--par-expiry-days", type=int, default=30,
                        help="PAR link expiry in days (default: 30)")

    return parser.parse_args(argv)


def classify_hour(has_cpu, instance_status, query_failed=False):
    """Classify an hourly bucket as up, down, stopped, or nodata.

    Args:
        has_cpu: True if CpuUtilization data exists for this hour
        instance_status: 0 (healthy), 1 (unhealthy), or None (no data)
        query_failed: True if the Monitoring API call failed for this scope

    Returns:
        "up", "down", "stopped", or "nodata"
    """
    if query_failed:
        return "nodata"
    if has_cpu:
        if instance_status == 1:
            return "down"
        return "up"
    if instance_status == 0:
        return "up"
    if instance_status == 1:
        return "down"
    return "stopped"


def compute_instance_stats(hourly_statuses):
    """Compute availability stats from hourly classification dict.

    Args:
        hourly_statuses: dict of {hour_key: "up"|"down"|"stopped"|"nodata"}

    Returns:
        dict with up_hours, down_hours, stopped_hours, nodata_hours,
        monitored_hours, total_hours, availability_pct (float or None),
        downtime_minutes, data_complete
    """
    up = sum(1 for v in hourly_statuses.values() if v == "up")
    down = sum(1 for v in hourly_statuses.values() if v == "down")
    stopped = sum(1 for v in hourly_statuses.values() if v == "stopped")
    nodata = sum(1 for v in hourly_statuses.values() if v == "nodata")
    monitored = up + down
    total = len(hourly_statuses)
    data_complete = nodata == 0

    if nodata > 0:
        # Any nodata hours -> availability is unreliable, show N/A
        availability_pct = None
    elif monitored == 0:
        availability_pct = None
    else:
        availability_pct = round(up / monitored * 100, 2)

    return {
        "up_hours": up,
        "down_hours": down,
        "stopped_hours": stopped,
        "nodata_hours": nodata,
        "monitored_hours": monitored,
        "total_hours": total,
        "availability_pct": availability_pct,
        "downtime_minutes": down * 60,
        "data_complete": data_complete,
    }


def compute_compartment_stats(instances_in_compartment, sla_target):
    """Compute availability stats for a single compartment.

    If ANY instance in the compartment has data_complete=False (nodata hours),
    compartment_availability_pct and at_target_count both become None (fail closed).

    Args:
        instances_in_compartment: list of instance dicts with stats
        sla_target: SLA target percentage

    Returns:
        dict with instance_count, compartment_availability_pct, at_target_count, data_complete
    """
    total_up = sum(s["up_hours"] for s in instances_in_compartment)
    total_monitored = sum(s["monitored_hours"] for s in instances_in_compartment)
    all_complete = all(s.get("data_complete", True) for s in instances_in_compartment)

    if not all_complete or total_monitored == 0:
        return {
            "instance_count": len(instances_in_compartment),
            "compartment_availability_pct": None,
            "at_target_count": None,
            "data_complete": all_complete,
        }

    pct = round(total_up / total_monitored * 100, 2)
    at_target = sum(
        1 for s in instances_in_compartment
        if s["availability_pct"] is not None and s["availability_pct"] >= sla_target
    )

    return {
        "instance_count": len(instances_in_compartment),
        "compartment_availability_pct": pct,
        "at_target_count": at_target,
        "data_complete": all_complete,
    }


def compute_fleet_stats(instance_stats_list, sla_target, discovery_warnings=None):
    """Compute fleet-level availability from per-instance stats.

    Fail-closed rules:
    - Any instance with data_complete=False -> data_complete=False
    - Any discovery_warnings -> discovery_complete=False
    - report_complete = data_complete AND discovery_complete
    - If report_complete=False: fleet_availability_pct, at_target_count,
      total_up_hours, total_monitored_hours all become None
    - discovered_instance_count always stays numeric for diagnostics

    Args:
        instance_stats_list: list of dicts from compute_instance_stats
        sla_target: SLA target percentage (e.g. 99.95)
        discovery_warnings: list of warning strings from discovery phase

    Returns:
        dict with discovered_instance_count, fleet_availability_pct,
        at_target_count, total_up_hours, total_monitored_hours,
        data_complete, discovery_complete, report_complete
    """
    discovery_warnings = discovery_warnings or []
    total_up = sum(s["up_hours"] for s in instance_stats_list)
    total_monitored = sum(s["monitored_hours"] for s in instance_stats_list)
    data_complete = all(s.get("data_complete", True) for s in instance_stats_list)
    discovery_complete = len(discovery_warnings) == 0
    report_complete = data_complete and discovery_complete

    if not report_complete or total_monitored == 0:
        return {
            "discovered_instance_count": len(instance_stats_list),
            "fleet_availability_pct": None,
            "at_target_count": None,
            "total_up_hours": None if not report_complete else total_up,
            "total_monitored_hours": None if not report_complete else total_monitored,
            "data_complete": data_complete,
            "discovery_complete": discovery_complete,
            "report_complete": report_complete,
        }

    fleet_pct = round(total_up / total_monitored * 100, 2)
    at_target = sum(
        1 for s in instance_stats_list
        if s["availability_pct"] is not None and s["availability_pct"] >= sla_target
    )

    return {
        "discovered_instance_count": len(instance_stats_list),
        "fleet_availability_pct": fleet_pct,
        "at_target_count": at_target,
        "total_up_hours": total_up,
        "total_monitored_hours": total_monitored,
        "data_complete": data_complete,
        "discovery_complete": discovery_complete,
        "report_complete": report_complete,
    }


def get_heatmap_resolution(days):
    """Return (block_hours, label) for adaptive heatmap resolution."""
    if days <= 7:
        return 1, "1 hour"
    elif days <= 14:
        return 4, "4 hours"
    elif days <= 30:
        return 6, "6 hours"
    else:
        return 24, "1 day"


if __name__ == "__main__":
    args = parse_args()
