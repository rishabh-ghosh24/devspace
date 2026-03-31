# OCI Compute Availability Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file Python CLI that generates self-contained HTML availability reports for OCI Compute VM instances, using CpuUtilization + instance_status metrics.

**Architecture:** Single Python file with logical sections: CLI parsing → auth → discovery → metric collection → availability computation → HTML rendering → optional Object Storage upload. All OCI API interactions use the `oci` Python SDK. HTML output embeds Chart.js inline for offline use. Tests mock OCI API responses.

**Tech Stack:** Python 3.8+, `oci` SDK, `pytest` for tests, Chart.js 4.4.x (embedded)

**Spec:** `docs/superpowers/specs/2026-03-31-oci-compute-availability-report-design.md`

---

## File Structure

```
sla-report/
├── compute_availability_report.py      # Main script (single file, all logic)
├── tests/
│   ├── test_availability.py            # Unit tests: classification + computation
│   └── test_report.py                  # Unit tests: HTML generation
├── examples/
│   └── sample_report.html              # Pre-generated sample (mock data)
├── iam/
│   ├── dynamic_group.tf                # Terraform: dynamic group
│   └── policies.tf                     # Terraform: IAM policies
├── README.md                           # Setup, usage, examples
└── LICENSE
```

The main script is organized as logical sections within one file (not separate modules). The sections, top to bottom:

1. **Constants & config** — colors, typography, Chart.js blob, version string
2. **CLI parsing** — `argparse` setup, validation
3. **Authentication** — Instance Principals / config file setup
4. **Discovery** — compartment tree + instance enumeration
5. **Metric collection** — SummarizeMetricsData calls with batching
6. **Availability computation** — classification, per-instance/compartment/fleet stats
7. **HTML rendering** — report generation with all sections
8. **Object Storage upload** — bucket creation, upload, PAR generation
9. **Main** — orchestration, logging, error handling

---

## Task 1: Project Scaffolding + CLI Parsing

**Files:**
- Create: `sla-report/compute_availability_report.py`
- Create: `sla-report/tests/test_availability.py`

**Refs:** Spec sections 6.1 (AUTH-1 to AUTH-4), 6.2 (DISC-1), 6.3 (DATA-4), 6.4 (COMP-10), 6.6 (OUT-1, OUT-2), 7 (CLI interface)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p sla-report/tests sla-report/examples sla-report/iam
touch sla-report/tests/__init__.py
```

- [ ] **Step 2: Write CLI parsing test**

Create `sla-report/tests/test_availability.py` with tests for argument parsing:

```python
import pytest
import sys
from unittest.mock import patch

# Tests for parse_args function
class TestParseArgs:
    def test_required_compartment_id(self):
        """--compartment-id is required"""
        with pytest.raises(SystemExit):
            from compute_availability_report import parse_args
            parse_args([])

    def test_default_values(self):
        from compute_availability_report import parse_args
        args = parse_args(["--compartment-id", "ocid1.compartment.oc1..aaa"])
        assert args.auth == "instance_principal"
        assert args.profile == "DEFAULT"
        assert args.days == 7
        assert args.sla_target == 99.95
        assert args.running_only is False
        assert args.upload is False
        assert args.bucket == "availability-reports"
        assert args.par_expiry_days == 30

    def test_days_validation(self):
        """--days only accepts 7, 14, 30, 60, 90"""
        from compute_availability_report import parse_args
        with pytest.raises(SystemExit):
            parse_args(["--compartment-id", "ocid1.test", "--days", "15"])

    def test_all_flags(self):
        from compute_availability_report import parse_args
        args = parse_args([
            "--compartment-id", "ocid1.test",
            "--auth", "config",
            "--profile", "PROD",
            "--days", "30",
            "--sla-target", "99.99",
            "--running-only",
            "--region", "us-ashburn-1",
            "--title", "ACME Corp",
            "--logo", "/path/to/logo.png",
            "--output", "/tmp/report.html",
            "--upload",
            "--bucket", "my-bucket",
            "--os-namespace", "myns",
            "--par-expiry-days", "90",
        ])
        assert args.auth == "config"
        assert args.profile == "PROD"
        assert args.days == 30
        assert args.sla_target == 99.99
        assert args.running_only is True
        assert args.region == "us-ashburn-1"
        assert args.title == "ACME Corp"
        assert args.logo == "/path/to/logo.png"
        assert args.output == "/tmp/report.html"
        assert args.upload is True
        assert args.bucket == "my-bucket"
        assert args.os_namespace == "myns"
        assert args.par_expiry_days == 90
        assert args.compartment_name == "My Compartment"

    def test_compartment_name_override(self):
        from compute_availability_report import parse_args
        args = parse_args([
            "--compartment-id", "ocid1.test",
            "--compartment-name", "Custom Name",
        ])
        assert args.compartment_name == "Custom Name"
```

Note: Update `test_all_flags` parse_args call to include `"--compartment-name", "My Compartment"` in the args list.

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestParseArgs -v
```

Expected: FAIL — `compute_availability_report` module not found.

- [ ] **Step 4: Implement CLI parsing**

Create `sla-report/compute_availability_report.py` with:

```python
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


if __name__ == "__main__":
    args = parse_args()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestParseArgs -v
```

Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add sla-report/
git commit -m "feat: add project scaffold and CLI argument parsing"
```

---

## Task 2: Availability Classification + Computation Logic

**Files:**
- Modify: `sla-report/compute_availability_report.py`
- Modify: `sla-report/tests/test_availability.py`

**Refs:** Spec sections 5 (classification truth table), 6.4 (COMP-1 through COMP-11)

This is the core logic — pure functions, no OCI API calls, fully testable.

- [ ] **Step 1: Write classification tests**

Add to `sla-report/tests/test_availability.py`:

```python
from compute_availability_report import classify_hour, compute_instance_stats, compute_fleet_stats


class TestClassifyHour:
    def test_cpu_data_and_status_healthy(self):
        assert classify_hour(has_cpu=True, instance_status=0) == "up"

    def test_cpu_data_and_status_unhealthy(self):
        assert classify_hour(has_cpu=True, instance_status=1) == "down"

    def test_cpu_data_and_no_status(self):
        assert classify_hour(has_cpu=True, instance_status=None) == "up"

    def test_no_cpu_and_status_healthy(self):
        assert classify_hour(has_cpu=False, instance_status=0) == "up"

    def test_no_cpu_and_status_unhealthy(self):
        assert classify_hour(has_cpu=False, instance_status=1) == "down"

    def test_no_cpu_and_no_status(self):
        assert classify_hour(has_cpu=False, instance_status=None) == "stopped"

    def test_query_failure(self):
        assert classify_hour(has_cpu=False, instance_status=None, query_failed=True) == "nodata"

    def test_query_failure_overrides_data(self):
        assert classify_hour(has_cpu=True, instance_status=0, query_failed=True) == "nodata"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestClassifyHour -v
```

Expected: FAIL — `classify_hour` not found.

- [ ] **Step 3: Implement classify_hour**

Add to `compute_availability_report.py`:

```python
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
```

- [ ] **Step 4: Run classification tests**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestClassifyHour -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Write computation tests**

Add to `sla-report/tests/test_availability.py`:

```python
class TestComputeInstanceStats:
    def test_all_up(self):
        hourly = {"2026-03-24T00:00:00Z": "up", "2026-03-24T01:00:00Z": "up"}
        stats = compute_instance_stats(hourly)
        assert stats["up_hours"] == 2
        assert stats["down_hours"] == 0
        assert stats["stopped_hours"] == 0
        assert stats["availability_pct"] == 100.0

    def test_with_downtime(self):
        hourly = {f"h{i}": "up" for i in range(167)}
        hourly["h167"] = "down"
        stats = compute_instance_stats(hourly)
        assert stats["up_hours"] == 167
        assert stats["down_hours"] == 1
        assert stats["availability_pct"] == 99.40  # 167/168 rounded to 2dp

    def test_stopped_excluded_from_denominator(self):
        hourly = {"h0": "up", "h1": "up", "h2": "stopped", "h3": "stopped"}
        stats = compute_instance_stats(hourly)
        assert stats["up_hours"] == 2
        assert stats["stopped_hours"] == 2
        assert stats["monitored_hours"] == 2  # up + down only
        assert stats["availability_pct"] == 100.0

    def test_all_stopped(self):
        hourly = {"h0": "stopped", "h1": "stopped"}
        stats = compute_instance_stats(hourly)
        assert stats["availability_pct"] is None  # N/A

    def test_downtime_minutes(self):
        hourly = {"h0": "up", "h1": "down", "h2": "down"}
        stats = compute_instance_stats(hourly)
        assert stats["downtime_minutes"] == 120

    def test_nodata_causes_na(self):
        hourly = {"h0": "up", "h1": "nodata", "h2": "up"}
        stats = compute_instance_stats(hourly)
        assert stats["nodata_hours"] == 1
        assert stats["availability_pct"] is None
        assert stats["data_complete"] is False

    def test_mixed_up_down_stopped(self):
        hourly = {f"h{i}": "up" for i in range(5)}
        hourly.update({f"h{i+5}": "down" for i in range(2)})
        hourly.update({f"h{i+7}": "stopped" for i in range(3)})
        stats = compute_instance_stats(hourly)
        assert stats["up_hours"] == 5
        assert stats["down_hours"] == 2
        assert stats["stopped_hours"] == 3
        assert stats["monitored_hours"] == 7  # 5 + 2
        assert stats["availability_pct"] == 71.43  # 5/7 * 100


class TestComputeCompartmentStats:
    def test_compartment_stats(self):
        from compute_availability_report import compute_compartment_stats
        instances = [
            {"compartment_name": "prod", "up_hours": 168, "down_hours": 0,
             "monitored_hours": 168, "availability_pct": 100.0},
            {"compartment_name": "prod", "up_hours": 167, "down_hours": 1,
             "monitored_hours": 168, "availability_pct": 99.40},
        ]
        stats = compute_compartment_stats(instances, sla_target=99.95)
        assert stats["instance_count"] == 2
        assert stats["compartment_availability_pct"] == 99.70  # 335/336
        assert stats["at_target_count"] == 1


class TestGetHeatmapResolution:
    def test_7_days(self):
        from compute_availability_report import get_heatmap_resolution
        assert get_heatmap_resolution(7) == (1, "1 hour")

    def test_14_days(self):
        from compute_availability_report import get_heatmap_resolution
        assert get_heatmap_resolution(14) == (4, "4 hours")

    def test_30_days(self):
        from compute_availability_report import get_heatmap_resolution
        assert get_heatmap_resolution(30) == (6, "6 hours")

    def test_60_days(self):
        from compute_availability_report import get_heatmap_resolution
        assert get_heatmap_resolution(60) == (24, "1 day")

    def test_90_days(self):
        from compute_availability_report import get_heatmap_resolution
        assert get_heatmap_resolution(90) == (24, "1 day")


class TestComputeFleetStats:
    def test_fleet_aggregation(self):
        instances = [
            {"up_hours": 168, "down_hours": 0, "monitored_hours": 168, "availability_pct": 100.0},
            {"up_hours": 167, "down_hours": 1, "monitored_hours": 168, "availability_pct": 99.40},
        ]
        fleet = compute_fleet_stats(instances, sla_target=99.95)
        assert fleet["total_instances"] == 2
        assert fleet["total_up_hours"] == 335
        assert fleet["total_monitored_hours"] == 336
        # 335/336 = 99.70
        assert fleet["fleet_availability_pct"] == 99.70
        assert fleet["at_target_count"] == 1  # only first meets 99.95

    def test_fleet_all_na(self):
        instances = [
            {"up_hours": 0, "down_hours": 0, "monitored_hours": 0, "availability_pct": None},
        ]
        fleet = compute_fleet_stats(instances, sla_target=99.95)
        assert fleet["fleet_availability_pct"] is None
```

- [ ] **Step 6: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestComputeInstanceStats tests/test_availability.py::TestComputeFleetStats -v
```

Expected: FAIL — functions not found.

- [ ] **Step 7: Implement compute_instance_stats and compute_fleet_stats**

Add to `compute_availability_report.py`:

```python
def compute_instance_stats(hourly_statuses):
    """Compute availability stats from hourly classification dict.

    Args:
        hourly_statuses: dict of {hour_key: "up"|"down"|"stopped"}

    Returns:
        dict with up_hours, down_hours, stopped_hours, monitored_hours,
        total_hours, availability_pct (float or None), downtime_minutes
    """
    up = sum(1 for v in hourly_statuses.values() if v == "up")
    down = sum(1 for v in hourly_statuses.values() if v == "down")
    stopped = sum(1 for v in hourly_statuses.values() if v == "stopped")
    nodata = sum(1 for v in hourly_statuses.values() if v == "nodata")
    monitored = up + down
    total = len(hourly_statuses)
    data_complete = nodata == 0

    if nodata > 0:
        # Any nodata hours → availability is unreliable, show N/A
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


def compute_fleet_stats(instance_stats_list, sla_target):
    """Compute fleet-level availability from per-instance stats.

    Args:
        instance_stats_list: list of dicts from compute_instance_stats
        sla_target: SLA target percentage (e.g. 99.95)

    Returns:
        dict with total_instances, fleet_availability_pct, at_target_count,
        total_up_hours, total_monitored_hours
    """
    total_up = sum(s["up_hours"] for s in instance_stats_list)
    total_monitored = sum(s["monitored_hours"] for s in instance_stats_list)

    if total_monitored == 0:
        fleet_pct = None
    else:
        fleet_pct = round(total_up / total_monitored * 100, 2)

    at_target = sum(
        1 for s in instance_stats_list
        if s["availability_pct"] is not None and s["availability_pct"] >= sla_target
    )

    return {
        "total_instances": len(instance_stats_list),
        "fleet_availability_pct": fleet_pct,
        "at_target_count": at_target,
        "total_up_hours": total_up,
        "total_monitored_hours": total_monitored,
    }
```

- [ ] **Step 7b: Implement compute_compartment_stats and get_heatmap_resolution**

Add to `compute_availability_report.py`:

```python
def compute_compartment_stats(instances_in_compartment, sla_target):
    """Compute availability stats for a single compartment.

    Args:
        instances_in_compartment: list of instance dicts with stats
        sla_target: SLA target percentage

    Returns:
        dict with instance_count, compartment_availability_pct, at_target_count
    """
    total_up = sum(s["up_hours"] for s in instances_in_compartment)
    total_monitored = sum(s["monitored_hours"] for s in instances_in_compartment)

    if total_monitored == 0:
        pct = None
    else:
        pct = round(total_up / total_monitored * 100, 2)

    at_target = sum(
        1 for s in instances_in_compartment
        if s["availability_pct"] is not None and s["availability_pct"] >= sla_target
    )

    return {
        "instance_count": len(instances_in_compartment),
        "compartment_availability_pct": pct,
        "at_target_count": at_target,
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
```

- [ ] **Step 8: Run all tests**

```bash
cd sla-report && python -m pytest tests/test_availability.py -v
```

Expected: All tests PASS (classification + computation + CLI).

- [ ] **Step 9: Commit**

```bash
git add sla-report/
git commit -m "feat: add availability classification and computation logic with tests"
```

---

## Task 3: Authentication + OCI Client Setup

**Files:**
- Modify: `sla-report/compute_availability_report.py`

**Refs:** Spec sections 6.1 (AUTH-1 through AUTH-4)

No unit tests for this task — auth depends on OCI SDK and real credentials. Will be verified during integration testing.

- [ ] **Step 1: Implement auth setup**

Add to `compute_availability_report.py`:

```python
import oci
import logging

log = logging.getLogger("availability-report")


def setup_auth(args):
    """Create OCI config and signer based on auth method.

    Returns:
        (config, signer) tuple. For config auth, signer is None.
        For instance_principal, config is minimal and signer is set.
    """
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
```

- [ ] **Step 2: Commit**

```bash
git add sla-report/compute_availability_report.py
git commit -m "feat: add OCI authentication setup (instance principal + config file)"
```

---

## Task 4: Instance Discovery

**Files:**
- Modify: `sla-report/compute_availability_report.py`
- Modify: `sla-report/tests/test_availability.py`

**Refs:** Spec sections 6.2 (DISC-1 through DISC-8)

- [ ] **Step 1: Write discovery helper tests**

Add to `sla-report/tests/test_availability.py`:

```python
from compute_availability_report import group_instances_by_compartment


class TestGroupInstances:
    def test_groups_by_compartment(self):
        instances = [
            {"name": "vm1", "compartment_name": "prod", "availability_pct": 100.0},
            {"name": "vm2", "compartment_name": "staging", "availability_pct": 99.5},
            {"name": "vm3", "compartment_name": "prod", "availability_pct": 98.0},
        ]
        groups = group_instances_by_compartment(instances)
        assert list(groups.keys()) == ["prod", "staging"]
        assert len(groups["prod"]) == 2
        assert len(groups["staging"]) == 1

    def test_sorted_worst_first(self):
        instances = [
            {"name": "vm1", "compartment_name": "prod", "availability_pct": 100.0},
            {"name": "vm2", "compartment_name": "prod", "availability_pct": 98.0},
            {"name": "vm3", "compartment_name": "prod", "availability_pct": 99.5},
        ]
        groups = group_instances_by_compartment(instances)
        names = [i["name"] for i in groups["prod"]]
        assert names == ["vm2", "vm3", "vm1"]  # worst first
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestGroupInstances -v
```

- [ ] **Step 3: Implement discovery functions**

Add to `compute_availability_report.py`:

```python
from collections import OrderedDict


def discover_compartments(identity_client, compartment_id):
    """Get compartment name and list all sub-compartments.

    Returns:
        (root_compartment_name, compartment_map) where compartment_map is
        {compartment_ocid: compartment_display_name}
    """
    # Get root compartment name
    root = identity_client.get_compartment(compartment_id).data
    root_name = root.name

    compartment_map = {compartment_id: root_name}

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
            compartment_map[c.id] = c.name
    except oci.exceptions.ServiceError as e:
        log.warning(f"Could not list sub-compartments: {e.message}")

    return root_name, compartment_map


def discover_instances(compute_client, compartment_map, running_only=False):
    """Discover VM instances across compartment tree.

    Note: Compute.ListInstances does NOT support compartment_id_in_subtree.
    We must iterate each compartment individually. This is correct behavior
    for the Compute API (unlike Monitoring/Log Analytics which do support subtree).

    Args:
        compute_client: OCI ComputeClient
        compartment_map: {compartment_ocid: display_name} from discover_compartments
        running_only: if True, only include RUNNING instances

    Returns:
        list of instance dicts with metadata
    """
    instances = []

    for comp_id, comp_name in compartment_map.items():
        try:
            comp_instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                comp_id,
            ).data
        except oci.exceptions.ServiceError as e:
            log.warning(f"Could not list instances in {comp_name}: {e.message}")
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
            })

    log.info(f"Discovered {len(instances)} instances across {len(compartment_map)} compartments")
    return instances


def group_instances_by_compartment(instances):
    """Group instances by compartment, sorted worst-availability-first within each group.

    Returns:
        OrderedDict of {compartment_name: [instances sorted by availability asc]}
    """
    groups = {}
    for inst in instances:
        comp = inst["compartment_name"]
        if comp not in groups:
            groups[comp] = []
        groups[comp].append(inst)

    # Sort instances within each group: worst availability first
    # None (N/A) sorts before numbers (worst)
    for comp in groups:
        groups[comp].sort(key=lambda i: (
            i.get("availability_pct") is not None,
            i.get("availability_pct", 0),
        ))

    return OrderedDict(sorted(groups.items()))
```

- [ ] **Step 4: Run tests**

```bash
cd sla-report && python -m pytest tests/test_availability.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add sla-report/
git commit -m "feat: add compartment and instance discovery with grouping logic"
```

---

## Task 5: Metric Collection + Batching

**Files:**
- Modify: `sla-report/compute_availability_report.py`
- Modify: `sla-report/tests/test_availability.py`

**Refs:** Spec sections 6.3 (DATA-1 through DATA-9), 10 (API batching)

- [ ] **Step 1: Write batching calculation test**

Add to `sla-report/tests/test_availability.py`:

```python
from compute_availability_report import calculate_batch_groups, build_hourly_buckets
from datetime import datetime, timezone, timedelta


class TestBatching:
    def test_small_fleet_single_batch(self):
        instance_ids = [f"ocid{i}" for i in range(50)]
        batches = calculate_batch_groups(instance_ids, hours=168)
        assert len(batches) == 1
        assert len(batches[0]) == 50

    def test_large_fleet_90_days_multiple_batches(self):
        instance_ids = [f"ocid{i}" for i in range(100)]
        batches = calculate_batch_groups(instance_ids, hours=2160)
        # 100 * 2160 = 216,000 > 80,000. 80000/2160 = ~37 per batch
        assert len(batches) >= 3
        # All instances covered
        all_ids = [id for batch in batches for id in batch]
        assert len(all_ids) == 100


class TestHourlyBuckets:
    def test_7_day_buckets(self):
        end = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
        start = end - timedelta(days=7)
        buckets = build_hourly_buckets(start, end)
        assert len(buckets) == 168

    def test_bucket_format(self):
        end = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
        start = end - timedelta(days=1)
        buckets = build_hourly_buckets(start, end)
        assert buckets[0] == "2026-03-30T00:00:00Z"
        assert buckets[-1] == "2026-03-30T23:00:00Z"
        assert len(buckets) == 24
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestBatching tests/test_availability.py::TestHourlyBuckets -v
```

- [ ] **Step 3: Implement metric collection functions**

Add to `compute_availability_report.py`:

```python
from datetime import datetime, timezone, timedelta
import math


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
    except oci.exceptions.ServiceError as e:
        log.warning(f"Metric query failed for {namespace}/{metric_name} "
                    f"in {compartment_id}: {e.message}")
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
        (cpu_metrics, status_metrics, failed_compartments) where:
        - cpu_metrics: {instance_ocid: {hour_key: value}}
        - status_metrics: {instance_ocid: {hour_key: value}}
        - failed_compartments: set of compartment OCIDs where queries failed
    """
    hours = int((end_time - start_time).total_seconds() / 3600)
    cpu_metrics = {}
    status_metrics = {}
    failed_compartments = set()

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
                failed_compartments.add(comp_id)

    return cpu_metrics, status_metrics, failed_compartments
```

- [ ] **Step 4: Run all tests**

```bash
cd sla-report && python -m pytest tests/test_availability.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add sla-report/
git commit -m "feat: add metric collection with hourly bucketing and API batching"
```

---

## Task 6: Availability Matrix Builder

**Files:**
- Modify: `sla-report/compute_availability_report.py`
- Modify: `sla-report/tests/test_availability.py`

**Refs:** Spec section 5 (classification truth table), 6.4 (COMP-1, COMP-2)

This ties together metric data + classification + computation.

- [ ] **Step 1: Write matrix builder test**

Add to `sla-report/tests/test_availability.py`:

```python
from compute_availability_report import build_availability_matrix


class TestBuildAvailabilityMatrix:
    def test_builds_matrix_from_metrics(self):
        hourly_buckets = ["h0", "h1", "h2", "h3"]
        cpu_metrics = {
            "inst1": {"h0": 5.0, "h1": 10.0, "h2": 2.0},  # h3 missing
        }
        status_metrics = {
            "inst1": {"h0": 0, "h1": 0, "h2": 1, "h3": 1},
        }
        matrix = build_availability_matrix(
            ["inst1"], hourly_buckets, cpu_metrics, status_metrics
        )
        assert matrix["inst1"]["h0"] == "up"      # cpu + status 0
        assert matrix["inst1"]["h1"] == "up"      # cpu + status 0
        assert matrix["inst1"]["h2"] == "down"    # cpu + status 1
        assert matrix["inst1"]["h3"] == "down"    # no cpu + status 1

    def test_no_data_is_stopped(self):
        hourly_buckets = ["h0", "h1"]
        cpu_metrics = {}
        status_metrics = {}
        matrix = build_availability_matrix(
            ["inst1"], hourly_buckets, cpu_metrics, status_metrics
        )
        assert matrix["inst1"]["h0"] == "stopped"
        assert matrix["inst1"]["h1"] == "stopped"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_availability.py::TestBuildAvailabilityMatrix -v
```

- [ ] **Step 3: Implement build_availability_matrix**

Add to `compute_availability_report.py`:

```python
def build_availability_matrix(instances, hourly_buckets, cpu_metrics, status_metrics,
                               failed_compartments=None):
    """Build availability matrix from metric data.

    Args:
        instances: list of instance dicts (need id and compartment_id)
        hourly_buckets: list of hour keys (ISO format strings)
        cpu_metrics: {instance_id: {hour_key: value}} from CpuUtilization
        status_metrics: {instance_id: {hour_key: value}} from instance_status
        failed_compartments: set of compartment OCIDs where queries failed

    Returns:
        {instance_id: {hour_key: "up"|"down"|"stopped"|"nodata"}}
    """
    failed_compartments = failed_compartments or set()
    matrix = {}
    for inst in instances:
        inst_id = inst["id"] if isinstance(inst, dict) else inst
        comp_id = inst.get("compartment_id") if isinstance(inst, dict) else None
        query_failed = comp_id in failed_compartments if comp_id else False

        inst_cpu = cpu_metrics.get(inst_id, {})
        inst_status = status_metrics.get(inst_id, {})
        hourly = {}
        for hour in hourly_buckets:
            has_cpu = hour in inst_cpu
            status_val = inst_status.get(hour)
            if status_val is not None:
                status_val = int(status_val)
            hourly[hour] = classify_hour(has_cpu, status_val, query_failed=query_failed)
        matrix[inst_id] = hourly
    return matrix
```

- [ ] **Step 4: Run all tests**

```bash
cd sla-report && python -m pytest tests/test_availability.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add sla-report/
git commit -m "feat: add availability matrix builder connecting metrics to classification"
```

---

## Task 7: HTML Report Generation

**Files:**
- Modify: `sla-report/compute_availability_report.py`
- Create: `sla-report/tests/test_report.py`

**Refs:** Spec sections 6.5 (all), 9 (HTML design spec)

This is the largest task. It generates the self-contained HTML report.

- [ ] **Step 1: Write HTML generation tests**

Create `sla-report/tests/test_report.py`:

```python
import pytest
from compute_availability_report import generate_html_report


@pytest.fixture
def sample_report_data():
    instances = [
        {
            "id": "ocid1.instance.oc1.aaa1",
            "name": "web-server-1",
            "state": "RUNNING",
            "shape": "VM.Standard.E4.Flex",
            "compartment_name": "production",
            "availability_pct": 100.0,
            "up_hours": 168,
            "down_hours": 0,
            "stopped_hours": 0,
            "monitored_hours": 168,
            "downtime_minutes": 0,
        },
        {
            "id": "ocid1.instance.oc1.aaa2",
            "name": "api-server-1",
            "state": "RUNNING",
            "shape": "VM.Standard.E4.Flex",
            "compartment_name": "production",
            "availability_pct": 99.40,
            "up_hours": 167,
            "down_hours": 1,
            "stopped_hours": 0,
            "monitored_hours": 168,
            "downtime_minutes": 60,
        },
    ]
    fleet = {
        "total_instances": 2,
        "fleet_availability_pct": 99.70,
        "at_target_count": 1,
        "total_up_hours": 335,
        "total_monitored_hours": 336,
    }
    heatmap_data = {
        "ocid1.instance.oc1.aaa1": ["up"] * 168,
        "ocid1.instance.oc1.aaa2": ["up"] * 75 + ["down"] + ["up"] * 92,
    }
    all_hours = [f"2026-03-24T{h:02d}:00:00Z" for h in range(24)] * 7  # simplified
    return {
        "instances": instances,
        "fleet": fleet,
        "heatmap_data": heatmap_data,
        "all_hours": all_hours[:168],
        "compartment_name": "acme-corp",
        "region": "us-ashburn-1",
        "days": 7,
        "sla_target": 99.95,
        "start_date": "Mar 24, 2026",
        "end_date": "Mar 30, 2026",
    }


class TestHTMLReport:
    def test_generates_valid_html(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_contains_report_title(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "Compute availability report" in html

    def test_contains_fleet_availability(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "99.70%" in html or "99.7%" in html

    def test_contains_instance_names(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "web-server-1" in html
        assert "api-server-1" in html

    def test_contains_compartment_grouping(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "production" in html

    def test_contains_chart_js(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        # Chart.js should be embedded inline, not loaded from CDN
        assert "cdn.jsdelivr.net" not in html
        assert "Chart" in html  # Chart.js constructor reference

    def test_contains_heatmap_blocks(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "hblk-up" in html or "hblk" in html

    def test_contains_print_styles(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "@media print" in html

    def test_self_contained(self, sample_report_data):
        """Report should have no external resource references"""
        html = generate_html_report(**sample_report_data)
        assert '<link rel="stylesheet"' not in html
        assert "src=\"http" not in html

    def test_branding_title(self, sample_report_data):
        html = generate_html_report(**sample_report_data, title="ACME Corp")
        assert "ACME Corp" in html

    def test_branding_logo(self, sample_report_data):
        logo_data = "data:image/png;base64,iVBORw0KGgo="
        html = generate_html_report(**sample_report_data, logo_data=logo_data)
        assert logo_data in html

    def test_footer_version(self, sample_report_data):
        html = generate_html_report(**sample_report_data)
        assert "OCI Compute Availability Report v1.0" in html

    def test_heatmap_toggle_hidden_under_50(self, sample_report_data):
        """No toggle button when under 50 instances"""
        html = generate_html_report(**sample_report_data)
        assert "show-all-toggle" not in html

    def test_heatmap_toggle_shown_over_50(self, sample_report_data):
        """Toggle button appears when >50 instances"""
        # Create 55 instances
        instances = []
        heatmap_data = {}
        for i in range(55):
            inst = {
                "id": f"ocid{i}", "name": f"vm-{i}", "state": "RUNNING",
                "shape": "VM.Standard.E4.Flex", "compartment_name": "prod",
                "availability_pct": 100.0, "up_hours": 168, "down_hours": 0,
                "stopped_hours": 0, "monitored_hours": 168, "downtime_minutes": 0,
            }
            instances.append(inst)
            heatmap_data[f"ocid{i}"] = ["up"] * 168
        data = {**sample_report_data, "instances": instances, "heatmap_data": heatmap_data}
        html = generate_html_report(**data)
        assert "show-all-toggle" in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd sla-report && python -m pytest tests/test_report.py -v
```

- [ ] **Step 3: Download Chart.js and embed**

```bash
cd sla-report
curl -sL "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" -o /tmp/chart.min.js
echo "Downloaded Chart.js: $(wc -c < /tmp/chart.min.js) bytes"
```

The Chart.js content will be stored as a constant string in the Python file.

- [ ] **Step 4: Implement generate_html_report**

Add the full `generate_html_report()` function to `compute_availability_report.py`. The function signature:

```python
# Chart.js must be stored as a constant at module level:
# CHART_JS = """<contents of chart.umd.min.js>"""

def generate_html_report(instances, fleet, heatmap_data, all_hours,
                         compartment_name, region, days, sla_target,
                         start_date, end_date, title=None, logo_data=None):
    """Generate self-contained HTML availability report.

    Args:
        instances: list of instance dicts (with stats merged in)
        fleet: fleet stats dict from compute_fleet_stats
        heatmap_data: {instance_id: [status_per_bucket]} for heatmap blocks
        all_hours: list of hourly bucket keys (ISO format)
        compartment_name: root compartment display name
        region: OCI region string
        days: reporting period in days
        sla_target: SLA target percentage
        start_date: formatted start date string
        end_date: formatted end date string
        title: optional custom branding title (top-right)
        logo_data: optional base64-encoded logo data URI

    Returns:
        Complete HTML string
    """
```

The function builds the HTML string section by section. Each section below must be implemented as part of the f-string or string concatenation:

**Section A: DOCTYPE + HEAD**
- `<!DOCTYPE html>`, charset utf-8, viewport meta
- `<title>Compute Availability Report — {compartment_name}</title>`
- `<style>` block with ALL CSS inline (no external stylesheets):
  - Colors: #1D9E75 (green), #E24B4A (red), #E8E6DF (gray), #EF9F27 (amber), #F8F7F4 (bg), #1A1A1A (text), #888780 (secondary), #B4B2A9 (muted)
  - `.container` max-width 960px, centered, padding 32px 24px
  - `.metrics` grid 4-col, 12px gap
  - `.metric-card` white bg, 10px radius, 1px solid #E8E6DF
  - `.summary-row` grid 180px + 1fr, 24px gap
  - `.donut-center .big` font-size 24px, weight 600
  - Table: th 11px uppercase, td 13px, border-bottom #f0efe9
  - Badge classes: `.badge-ok` (#E1F5EE/#085041), `.badge-warn` (#FAEEDA/#633806), `.badge-bad` (#FCEBEB/#791F1F)
  - `.avail-bar` flex, height 6px, border-radius 3px
  - Heatmap: `.heatmap-row` flex, `.heatmap-label` width 200px, `.heatmap-pct` width 52px, `.hblk` height 24px flex:1 border-radius 1.5px
  - `.hblk-up` #1D9E75, `.hblk-down` #E24B4A, `.hblk-nodata` #E8E6DF
  - `.tooltip` fixed position, bg #2C2C2A, white text, 11px, 4px radius, display none
  - `@media print` — white bg, hidden tooltips, visible borders

**Section B: HEADER**
- `<div class="header">` with h1 "Compute availability report"
- Meta bar: Compartment, Region, Period (start — end, N days), SLA target
- If `title` or `logo_data`: right-aligned branding area

**Section C: METRIC CARDS**
- 4 cards in `.metrics` grid:
  1. Fleet availability — value colored green/amber/red based on sla_target
  2. Instances monitored — neutral
  3. Meeting SLA target — `at_target / total` green
  4. Total uptime hours — `up / monitored` neutral
- Handle fleet_availability_pct = None → display "N/A"

**Section D: EXECUTIVE SUMMARY (donut + table)**
- Donut: `<canvas id="donut">` + center text overlay
- Table grouped by compartment using `group_instances_by_compartment`:
  - For each compartment: header row with name, count, compartment availability %
    (use `compute_compartment_stats` for each group)
  - Column headers: Instance, Status (centered), Availability, Uptime (centered), Downtime
  - Column widths: 28%, 14%, 14%, 30%, 14%
  - Each instance row:
    - Instance: colored dot (green=RUNNING, red=STOPPED, amber=other) + display name
    - Status: centered badge with lifecycle state
    - Availability: bold, colored (green >= sla_target, amber >= 99, red otherwise)
    - Uptime: hours centered above stacked bar (green up / red down / gray stopped)
    - Downtime: minutes, colored red if > 0
  - Instances sorted worst-availability-first within each compartment

**Section E: HEATMAP**
- Section title "Hourly availability heatmap"
- Date markers row (evenly spaced dates)
- For each compartment group:
  - Uppercase compartment label
  - For each instance row:
    - Name (200px), availability % (52px, colored), colored blocks
    - Use `get_heatmap_resolution(days)` to determine block grouping
    - Aggregate hourly statuses into blocks:
      - if ANY hour is "nodata" → block is nodata
      - if ANY hour is "down" → block is down
      - if ALL hours are "stopped" → block is stopped
      - if mix of up + stopped → block is up (instance was available when running; stopped hours don't indicate unavailability)
      - else → up
  - **HEAT-9 toggle**: If total instances > 50, only render rows where availability < sla_target. Add a button with id="show-all-toggle" that toggles visibility of hidden rows via JS.
- Legend: Available (green), Unavailable (red), No data/stopped (gray), resolution note

**Section F: TOOLTIP + FOOTER**
- `<div class="tooltip" id="tooltip"></div>` element
- Footer: generation timestamp (UTC) + version "OCI Compute Availability Report v1.0"

**Section G: JAVASCRIPT**
- Embed Chart.js inline: `<script>{CHART_JS}</script>`
- Donut chart initialization:
  ```js
  new Chart(document.getElementById('donut'), {
    type: 'doughnut',
    data: { datasets: [{ data: [fleet_pct, 100-fleet_pct],
            backgroundColor: ['#1d9e75', unavail > 0 ? '#e24b4a' : '#e8e6df'],
            borderWidth: 0, cutout: '74%' }] },
    options: { responsive: false, plugins: { legend: { display: false } },
               animation: { animateRotate: true, duration: 600 } }
  });
  ```
- Heatmap tooltip JS: mouseenter/mousemove/mouseleave handlers on `.hblk` elements
  - Tooltip format: `{instance_name} — {date} {hour}:00 UTC — {status_label}`
- HEAT-9 toggle button JS (if >50 instances):
  ```js
  document.getElementById('show-all-toggle').addEventListener('click', function() {
    document.querySelectorAll('.heatmap-hidden').forEach(el => el.classList.toggle('hidden'));
    this.textContent = this.textContent === 'Show all' ? 'Show below SLA only' : 'Show all';
  });
  ```

- [ ] **Step 5: Run tests**

```bash
cd sla-report && python -m pytest tests/test_report.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add sla-report/
git commit -m "feat: add HTML report generation with embedded Chart.js, heatmap, and print styles"
```

---

## Task 8: Object Storage Upload + PAR

**Files:**
- Modify: `sla-report/compute_availability_report.py`

**Refs:** Spec sections 6.6 (OUT-3 through OUT-8)

No unit tests — depends on live Object Storage. Verified during integration testing.

- [ ] **Step 1: Implement upload functions**

Add to `compute_availability_report.py`:

```python
def upload_report(config, signer, compartment_id, html_content, object_name,
                  bucket_name, namespace=None, par_expiry_days=30):
    """Upload HTML report to Object Storage and create a PAR link.

    Args:
        config: OCI config dict
        signer: OCI signer (or None for config auth)
        compartment_id: compartment OCID for the bucket
        html_content: HTML string to upload
        object_name: object name in the bucket
        bucket_name: bucket name
        namespace: Object Storage namespace (auto-detected if None)
        par_expiry_days: PAR expiry in days

    Returns:
        PAR URL string, or None on failure
    """
    os_client = make_client(oci.object_storage.ObjectStorageClient, config, signer)

    # Auto-detect namespace
    if not namespace:
        namespace = os_client.get_namespace().data

    # Create bucket if it doesn't exist
    try:
        os_client.get_bucket(namespace, bucket_name)
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            log.info(f"Creating bucket '{bucket_name}'...")
            os_client.create_bucket(
                namespace,
                oci.object_storage.models.CreateBucketDetails(
                    name=bucket_name,
                    compartment_id=compartment_id,
                    public_access_type="NoPublicAccess",
                ),
            )
        else:
            log.error(f"Bucket check failed: {e.message}")
            return None

    # Upload
    os_client.put_object(
        namespace, bucket_name, object_name,
        html_content.encode("utf-8"),
        content_type="text/html",
    )
    log.info(f"Uploaded to {namespace}/{bucket_name}/{object_name}")

    # Create PAR
    expiry = datetime.now(timezone.utc) + timedelta(days=par_expiry_days)
    par = os_client.create_preauthenticated_request(
        namespace, bucket_name,
        oci.object_storage.models.CreatePreauthenticatedRequestDetails(
            name=f"availability-report-{object_name}",
            access_type="ObjectRead",
            time_expires=expiry,
            object_name=object_name,
            bucket_listing_action="Deny",
        ),
    ).data

    par_url = f"https://objectstorage.{config.get('region', 'unknown')}.oraclecloud.com{par.access_uri}"
    return par_url
```

- [ ] **Step 2: Commit**

```bash
git add sla-report/compute_availability_report.py
git commit -m "feat: add Object Storage upload with bucket creation and PAR link"
```

---

## Task 9: Main Orchestration + Logo Embedding

**Files:**
- Modify: `sla-report/compute_availability_report.py`

**Refs:** Spec sections 4 (architecture phases), 6.5.1 (RPT-3 branding)

- [ ] **Step 1: Implement main function**

Add to `compute_availability_report.py`:

```python
import base64
import os
import re


def sanitize_filename(name):
    """Convert compartment name to safe filename component."""
    return re.sub(r'[^\w\-]', '_', name).lower()


def embed_logo(logo_path):
    """Read logo file and return base64-encoded data URI."""
    if not logo_path or not os.path.isfile(logo_path):
        return None
    ext = os.path.splitext(logo_path)[1].lower()
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                  ".svg": "image/svg+xml", ".gif": "image/gif"}
    mime = mime_types.get(ext, "image/png")
    with open(logo_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def main():
    args = parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("OCI Compute Availability Report v%s", VERSION)

    # Phase 1: Auth
    log.info("Authenticating (%s)...", args.auth)
    config, signer = setup_auth(args)

    # Phase 2: Discover
    log.info("Discovering instances...")
    identity_client = make_client(oci.identity.IdentityClient, config, signer)
    compute_client = make_client(oci.core.ComputeClient, config, signer)

    compartment_name = args.compartment_name
    if not compartment_name:
        compartment_name, compartment_map = discover_compartments(identity_client, args.compartment_id)
    else:
        _, compartment_map = discover_compartments(identity_client, args.compartment_id)

    instances = discover_instances(compute_client, compartment_map, args.running_only)
    if not instances:
        log.error("No instances found. Exiting.")
        sys.exit(1)

    # Phase 3: Collect metrics
    end_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(days=args.days)
    hourly_buckets = build_hourly_buckets(start_time, end_time)

    log.info("Collecting metrics for %d instances over %d days (%d hours)...",
             len(instances), args.days, len(hourly_buckets))
    monitoring_client = make_client(oci.monitoring.MonitoringClient, config, signer)
    cpu_metrics, status_metrics, failed_compartments = collect_all_metrics(
        monitoring_client, args.compartment_id, compartment_map,
        instances, start_time, end_time,
    )

    if failed_compartments:
        log.warning(f"Metric queries failed for {len(failed_compartments)} compartment(s). "
                    "Affected instances will show N/A availability.")

    # Phase 4: Compute availability
    log.info("Computing availability...")
    matrix = build_availability_matrix(
        instances, hourly_buckets, cpu_metrics, status_metrics, failed_compartments
    )

    # Merge stats into instance dicts
    for inst in instances:
        stats = compute_instance_stats(matrix[inst["id"]])
        inst.update(stats)

    fleet = compute_fleet_stats(instances, args.sla_target)

    # Build heatmap data (list of statuses per instance)
    heatmap_data = {}
    for inst in instances:
        heatmap_data[inst["id"]] = [matrix[inst["id"]][h] for h in hourly_buckets]

    # Phase 5: Render
    log.info("Generating report...")
    region = args.region or config.get("region", "unknown")
    logo_data = embed_logo(args.logo) if args.logo else None

    html = generate_html_report(
        instances=instances,
        fleet=fleet,
        heatmap_data=heatmap_data,
        all_hours=hourly_buckets,
        compartment_name=compartment_name,
        region=region,
        days=args.days,
        sla_target=args.sla_target,
        start_date=start_time.strftime("%b %d, %Y"),
        end_date=(end_time - timedelta(hours=1)).strftime("%b %d, %Y"),
        title=args.title,
        logo_data=logo_data,
    )

    # Write to file
    if args.output:
        output_path = args.output
    else:
        safe_name = sanitize_filename(compartment_name)
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = f"availability_report_{safe_name}_{date_str}.html"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    log.info("Report written to %s", output_path)

    # Phase 6: Upload (optional)
    if args.upload:
        log.info("Uploading to Object Storage...")
        object_name = os.path.basename(output_path)
        par_url = upload_report(
            config, signer, args.compartment_id, html, object_name,
            args.bucket, args.os_namespace, args.par_expiry_days,
        )
        if par_url:
            log.info("PAR URL (expires in %d days):", args.par_expiry_days)
            print(par_url)

    log.info("Done. Fleet availability: %s",
             f"{fleet['fleet_availability_pct']}%" if fleet['fleet_availability_pct'] is not None else "N/A")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests to confirm nothing broke**

```bash
cd sla-report && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add sla-report/
git commit -m "feat: add main orchestration, logo embedding, and CLI entry point"
```

---

## Task 10: IAM Terraform + README + Sample Report

**Files:**
- Create: `sla-report/iam/dynamic_group.tf`
- Create: `sla-report/iam/policies.tf`
- Create: `sla-report/README.md`
- Create: `sla-report/examples/sample_report.html`
- Create: `sla-report/LICENSE`

**Refs:** Spec sections 8 (IAM), 11 (repo structure)

- [ ] **Step 1: Create IAM Terraform files**

`sla-report/iam/dynamic_group.tf`:
```hcl
variable "tenancy_ocid" {}
variable "monitoring_vm_ocid" {}

resource "oci_identity_dynamic_group" "availability_reporter" {
  name           = "availability-reporter"
  description    = "VM that generates availability reports"
  compartment_id = var.tenancy_ocid
  matching_rule  = "instance.id = '${var.monitoring_vm_ocid}'"
}
```

`sla-report/iam/policies.tf`:
```hcl
variable "tenancy_ocid" {}
variable "compartment_name" {}
variable "bucket_name" { default = "availability-reports" }

resource "oci_identity_policy" "availability_reporter_policy" {
  name           = "availability-reporter-policy"
  description    = "Allow availability report generation"
  compartment_id = var.tenancy_ocid

  statements = [
    "Allow dynamic-group availability-reporter to read instances in compartment ${var.compartment_name}",
    "Allow dynamic-group availability-reporter to read metrics in compartment ${var.compartment_name}",
    "Allow dynamic-group availability-reporter to read compartments in tenancy",
    "Allow dynamic-group availability-reporter to manage objects in compartment ${var.compartment_name} where target.bucket.name='${var.bucket_name}'",
    "Allow dynamic-group availability-reporter to manage buckets in compartment ${var.compartment_name} where target.bucket.name='${var.bucket_name}'",
    "Allow dynamic-group availability-reporter to manage preauthenticated-requests in compartment ${var.compartment_name} where target.bucket.name='${var.bucket_name}'",
  ]
}
```

- [ ] **Step 2: Create README.md**

Write README based on spec sections 7, 8, 13. Include: what it produces, prerequisites, usage examples, CLI reference, cron setup, limitations. Reference the existing README at `/Users/rishabh/Documents/ProductMgmt/sla-report/README.md` for structure and tone.

- [ ] **Step 3: Generate sample report with mock data**

Run the `generate_html_report()` function with mock data (similar to `test_report.py` fixture) and save to `sla-report/examples/sample_report.html`. This serves as a demo for users who haven't set up OCI auth yet.

- [ ] **Step 4: Add LICENSE file**

Copy or create an appropriate license file.

- [ ] **Step 5: Run full test suite**

```bash
cd sla-report && python -m pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add sla-report/
git commit -m "docs: add IAM terraform, README, sample report, and LICENSE"
```

---

## Task 11: Integration Test (Live OCI)

**Files:**
- Test against live OCI environment

**Refs:** Spec section 12 (integration tests)

This task is manual — run on a VM with OCI access (or locally with `--auth config`).

- [ ] **Step 1: Test basic 7-day report**

```bash
cd sla-report
python3 compute_availability_report.py \
  --auth config --profile DEFAULT \
  --compartment-id <YOUR_COMPARTMENT_OCID>
```

Verify: report generated, opens in browser, donut/table/heatmap render correctly.

- [ ] **Step 2: Test 30-day report**

```bash
python3 compute_availability_report.py \
  --auth config --profile DEFAULT \
  --compartment-id <YOUR_COMPARTMENT_OCID> \
  --days 30
```

Verify: heatmap uses 6-hour blocks, report loads quickly.

- [ ] **Step 3: Test with upload**

```bash
python3 compute_availability_report.py \
  --auth config --profile DEFAULT \
  --compartment-id <YOUR_COMPARTMENT_OCID> \
  --upload --bucket availability-reports-test
```

Verify: PAR URL printed, accessible in browser.

- [ ] **Step 4: Test branding**

```bash
python3 compute_availability_report.py \
  --auth config --profile DEFAULT \
  --compartment-id <YOUR_COMPARTMENT_OCID> \
  --title "Test Corp" --logo /path/to/logo.png
```

Verify: branding appears in top-right of report.

- [ ] **Step 5: Compare with OCI Console (both metrics)**

Open OCI Console → Monitoring → Metrics Explorer. For a specific instance, query BOTH:
1. `CpuUtilization[1h].max()` from `oci_computeagent`
2. `instance_status[1h].max()` from `oci_compute_infrastructure_health`

Verify the report's hourly classification matches the combined signal from both metrics. Do NOT validate against CpuUtilization alone — the whole design depends on the two-metric approach.

- [ ] **Step 6: Print to PDF**

Open report in browser → Print → Save as PDF. Verify clean output without tooltips, white background, visible borders.

- [ ] **Step 7: Final commit if any fixes needed**

```bash
git add sla-report/
git commit -m "fix: integration test fixes"
```
