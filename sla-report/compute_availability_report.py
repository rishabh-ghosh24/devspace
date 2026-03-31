#!/usr/bin/env python3
"""OCI Compute Availability Report Generator.

Generates self-contained HTML availability reports for OCI Compute VM instances
using CpuUtilization and instance_status metrics.
"""

import argparse
import logging
import math
import sys
from collections import OrderedDict
from datetime import datetime, timezone, timedelta

try:
    import oci
except ImportError:
    oci = None

VERSION = "1.0"

log = logging.getLogger("availability-report")


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


def setup_auth(args):
    """Create OCI config and signer based on auth method.

    Returns:
        (config, signer) tuple. For config auth, signer is None.
        For instance_principal, config is minimal and signer is set.
    """
    if oci is None:
        raise RuntimeError("The 'oci' package is required. Install it with: pip install oci")
    if args.auth == "config":
        config = oci.config.from_file(profile_name=args.profile)
        if args.region:
            config["region"] = args.region
        oci.config.validate_config(config)
        return config, None
    else:
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        config = {"region": args.region} if args.region else {"region": signer.region}
        return config, signer


def make_client(client_class, config, signer):
    """Create an OCI SDK client with appropriate auth.

    For signer-based auth, pass the config dict (which contains region)
    so --region override is respected.
    """
    if signer:
        return client_class(config=config, signer=signer)
    return client_class(config)


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


def _build_ancestor_path(compartment_map, comp_id, max_depth=10):
    """Build full ancestor path for a compartment: grandparent/parent/name."""
    parts = []
    current = comp_id
    for _ in range(max_depth):
        info = compartment_map.get(current)
        if not info:
            break
        parts.append(info["name"])
        if not info.get("parent_id") or info["parent_id"] not in compartment_map:
            break
        current = info["parent_id"]
    parts.reverse()
    return "/".join(parts)


def build_compartment_labels(compartment_map):
    """Add a 'label' key to each compartment entry.

    Algorithm:
    1. Start with label = name for all compartments
    2. Find groups of compartments that share the same label
    3. For each collision group, prepend one more ancestor to each label
    4. Repeat until all labels are unique, or fall back to full path

    This handles arbitrarily deep duplicates:
    - orgA/team/prod vs orgB/team/prod (not just parent/prod)
    """
    # Initialize labels with just the name
    for comp_id, info in compartment_map.items():
        info["_path_parts"] = [info["name"]]
        info["_current_id"] = comp_id
        info["label"] = info["name"]

    # Iteratively disambiguate until all labels are unique (max 10 levels)
    for _ in range(10):
        # Find label collisions
        label_groups = {}
        for comp_id, info in compartment_map.items():
            label_groups.setdefault(info["label"], []).append(comp_id)

        collisions = {label: ids for label, ids in label_groups.items() if len(ids) > 1}
        if not collisions:
            break

        # For each collision group, prepend one more ancestor
        for label, comp_ids in collisions.items():
            for comp_id in comp_ids:
                info = compartment_map[comp_id]
                # Walk up to next ancestor not yet in the path
                current = comp_id
                for _ in range(len(info["_path_parts"])):
                    parent_id = compartment_map.get(current, {}).get("parent_id")
                    if not parent_id or parent_id not in compartment_map:
                        break
                    current = parent_id
                parent_info = compartment_map.get(current)
                if parent_info and parent_info["name"] not in info["_path_parts"]:
                    info["_path_parts"].insert(0, parent_info["name"])
                else:
                    # Fall back to full path if we can't disambiguate further
                    info["_path_parts"] = _build_ancestor_path(
                        compartment_map, comp_id
                    ).split("/")
                info["label"] = "/".join(info["_path_parts"])

    # Clean up temporary keys
    for info in compartment_map.values():
        info.pop("_path_parts", None)
        info.pop("_current_id", None)


def discover_compartments(identity_client, compartment_id):
    """Get compartment name and list all sub-compartments.

    Returns:
        (root_compartment_name, compartment_map, discovery_warnings) where:
        - compartment_map: {compartment_ocid: {"name": str, "parent_id": str|None, "label": str}}
        - discovery_warnings: list of warning strings (empty = fully successful)
    """
    discovery_warnings = []

    # Get root compartment name
    root = identity_client.get_compartment(compartment_id).data
    root_name = root.name

    # compartment_map stores {ocid: {"name": str, "parent_id": str}}
    compartment_map = {compartment_id: {"name": root_name, "parent_id": None}}

    # List all sub-compartments recursively
    try:
        sub_compartments = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            compartment_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
            lifecycle_state="ACTIVE",
        ).data
        for c in sub_compartments:
            compartment_map[c.id] = {"name": c.name, "parent_id": c.compartment_id}
    except oci.exceptions.ServiceError as e:
        msg = f"Could not list sub-compartments: {e.message}"
        log.warning(msg)
        discovery_warnings.append(msg)

    # Build display labels, disambiguating duplicate names
    build_compartment_labels(compartment_map)

    return root_name, compartment_map, discovery_warnings


def discover_instances(compute_client, compartment_map, running_only=False):
    """Discover VM instances across compartment tree.

    Note: Compute.ListInstances does NOT support compartment_id_in_subtree.
    We must iterate each compartment individually.

    Args:
        compute_client: OCI ComputeClient
        compartment_map: {compartment_ocid: {"name": str, "parent_id": str, "label": str}}
        running_only: if True, only include RUNNING instances

    Returns:
        (instances, discovery_warnings) tuple:
        - instances: list of instance dicts with metadata
        - discovery_warnings: list of warning strings for failed compartments
    """
    instances = []
    discovery_warnings = []

    for comp_id, comp_info in compartment_map.items():
        comp_name = comp_info["name"]
        comp_label = comp_info.get("label", comp_name)
        try:
            comp_instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                comp_id,
            ).data
        except oci.exceptions.ServiceError as e:
            msg = f"Could not list instances in {comp_label} ({comp_id}): {e.message}"
            log.warning(msg)
            discovery_warnings.append(msg)
            continue

        for inst in comp_instances:
            # Skip terminated always
            if inst.lifecycle_state == "TERMINATED":
                continue
            # Skip non-running if --running-only
            if running_only and inst.lifecycle_state != "RUNNING":
                continue

            instances.append({
                "id": inst.id,
                "name": inst.display_name,
                "state": inst.lifecycle_state,
                "shape": inst.shape,
                "ad": inst.availability_domain,
                "fd": inst.fault_domain,
                "region": inst.region,
                "compartment_id": inst.compartment_id,
                "compartment_name": comp_name,
                "compartment_label": comp_label,
            })

    log.info(f"Discovered {len(instances)} instances across {len(compartment_map)} compartments")
    return instances, discovery_warnings


def group_instances_by_compartment(instances):
    """Group instances by compartment OCID, sorted worst-availability-first within each group.

    Groups by compartment_id (OCID) to avoid merging distinct compartments
    that share the same display name. Uses compartment_label for display.

    Returns:
        OrderedDict of {compartment_id: {
            "name": compartment_display_name,
            "instances": [instances sorted by availability asc]
        }}
    """
    groups = {}
    for inst in instances:
        comp_id = inst.get("compartment_id", inst.get("compartment_name"))
        comp_label = inst.get("compartment_label", inst.get("compartment_name", comp_id))
        if comp_id not in groups:
            groups[comp_id] = {"name": comp_label, "instances": []}
        groups[comp_id]["instances"].append(inst)

    # Sort instances within each group: worst availability first
    # None (N/A) sorts before numbers (worst)
    for comp_id in groups:
        groups[comp_id]["instances"].sort(key=lambda i: (
            i.get("availability_pct") is not None,
            i.get("availability_pct", 0),
        ))

    return OrderedDict(sorted(groups.items(), key=lambda x: x[1]["name"]))


DATAPOINT_LIMIT = 80_000  # safety margin below 100K API limit


def build_hourly_buckets(start_time, end_time):
    """Build list of hourly bucket keys (ISO format, UTC) for the reporting period."""
    buckets = []
    current = start_time
    while current < end_time:
        buckets.append(current.strftime("%Y-%m-%dT%H:%M:%SZ"))
        current += timedelta(hours=1)
    return buckets


def calculate_batch_groups(instance_ids, hours):
    """Split instance IDs into batches to stay under API data point limit.

    Args:
        instance_ids: list of instance OCIDs
        hours: number of hourly buckets in the reporting period

    Returns:
        list of lists, each sub-list is a batch of instance IDs
    """
    if not instance_ids:
        return []

    max_per_batch = max(1, DATAPOINT_LIMIT // hours)
    batches = []
    for i in range(0, len(instance_ids), max_per_batch):
        batches.append(instance_ids[i:i + max_per_batch])
    return batches


def is_tenancy_ocid(ocid):
    """Check if an OCID is a tenancy root OCID."""
    return ocid.startswith("ocid1.tenancy.")


def collect_metrics(monitoring_client, compartment_id, namespace, metric_name,
                    start_time, end_time, use_subtree=False, instance_ids=None):
    """Query SummarizeMetricsData for a metric across instances.

    Args:
        monitoring_client: OCI MonitoringClient
        compartment_id: compartment OCID for the query
        namespace: metric namespace (e.g. "oci_computeagent")
        metric_name: metric name (e.g. "CpuUtilization")
        start_time: datetime, start of reporting window
        end_time: datetime, end of reporting window
        use_subtree: only set True when compartment_id is tenancy root OCID
        instance_ids: optional list of instance OCIDs to filter by

    Returns:
        (metrics_dict, failed) tuple:
        - metrics_dict: {instance_ocid: {hour_key: value}}
        - failed: bool, True if the API call failed
    """
    if instance_ids:
        resource_filter = " || ".join(
            f'resourceId = "{rid}"' for rid in instance_ids
        )
        query = f"{metric_name}[1h]{{{resource_filter}}}.max()"
    else:
        query = f"{metric_name}[1h].max()"

    try:
        result = monitoring_client.summarize_metrics_data(
            compartment_id,
            oci.monitoring.models.SummarizeMetricsDataDetails(
                namespace=namespace,
                query=query,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                resolution="1h",
            ),
            compartment_id_in_subtree=use_subtree,
        ).data
    except Exception as e:
        log.warning(f"Metric query failed for {namespace}/{metric_name} "
                    f"in {compartment_id}: {e}")
        return {}, True  # Return failure flag

    # Parse results: group data points by resourceId
    metrics_by_instance = {}
    for metric_data in result:
        resource_id = metric_data.dimensions.get("resourceId") if metric_data.dimensions else None
        if not resource_id:
            continue

        if resource_id not in metrics_by_instance:
            metrics_by_instance[resource_id] = {}

        for dp in metric_data.aggregated_datapoints:
            hour_key = dp.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            metrics_by_instance[resource_id][hour_key] = dp.value

    return metrics_by_instance, False


def collect_all_metrics(monitoring_client, root_compartment_id, compartment_map,
                        instances, start_time, end_time):
    """Collect CpuUtilization and instance_status for all instances.

    Query strategy:
    - If root_compartment_id is tenancy OCID: single query with subtree=True
    - Otherwise: per-compartment queries with subtree=False

    Returns:
        (cpu_metrics, status_metrics, failed_instance_ids) where:
        - cpu_metrics: {instance_ocid: {hour_key: value}}
        - status_metrics: {instance_ocid: {hour_key: value}}
        - failed_instance_ids: set of instance OCIDs where metric queries failed
    """
    hours = int((end_time - start_time).total_seconds() / 3600)
    cpu_metrics = {}
    status_metrics = {}
    failed_instance_ids = set()

    use_subtree = is_tenancy_ocid(root_compartment_id)

    if use_subtree:
        # Tenancy-wide: single query with subtree
        scopes = [(root_compartment_id, True)]
    else:
        # Non-root: per-compartment queries
        scopes = [(comp_id, False) for comp_id in compartment_map.keys()]

    for comp_id, subtree in scopes:
        # Determine instances in this scope for batching
        if subtree:
            scope_instance_ids = [inst["id"] for inst in instances]
        else:
            scope_instance_ids = [inst["id"] for inst in instances
                                  if inst["compartment_id"] == comp_id]
        if not scope_instance_ids:
            continue

        batches = calculate_batch_groups(scope_instance_ids, hours)

        for batch in batches:
            log.info(f"Querying metrics for batch of {len(batch)} instances "
                     f"in {comp_id[:30]}...")

            # CpuUtilization
            batch_cpu, cpu_failed = collect_metrics(
                monitoring_client, comp_id,
                "oci_computeagent", "CpuUtilization",
                start_time, end_time,
                use_subtree=subtree,
                instance_ids=batch if len(batches) > 1 else None,
            )
            cpu_metrics.update(batch_cpu)

            # instance_status
            batch_status, status_failed = collect_metrics(
                monitoring_client, comp_id,
                "oci_compute_infrastructure_health", "instance_status",
                start_time, end_time,
                use_subtree=subtree,
                instance_ids=batch if len(batches) > 1 else None,
            )
            status_metrics.update(batch_status)

            if cpu_failed or status_failed:
                # Mark specific instances in this batch as failed,
                # not the whole compartment -- preserves successful batches
                failed_instance_ids.update(batch)

    return cpu_metrics, status_metrics, failed_instance_ids


if __name__ == "__main__":
    args = parse_args()
