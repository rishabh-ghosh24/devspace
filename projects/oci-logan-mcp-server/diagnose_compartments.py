#!/usr/bin/env python3
"""
Diagnostic script to debug compartment traversal and log queries.
Run this on your VM to see what's happening.

Usage: python3 diagnose_compartments.py
"""

import oci
from datetime import datetime, timedelta
from pathlib import Path
import yaml

def main():
    print("=" * 60)
    print("  OCI Log Analytics - Compartment Diagnostic")
    print("=" * 60)
    print()

    # Load configs
    print("[1] Loading configurations...")
    oci_config = oci.config.from_file()

    config_path = Path.home() / ".oci-la-mcp" / "config.yaml"
    with open(config_path) as f:
        mcp_config = yaml.safe_load(f)

    namespace = mcp_config["log_analytics"]["namespace"]
    tenancy_id = oci_config["tenancy"]

    print(f"    Tenancy: {tenancy_id[:50]}...")
    print(f"    Namespace: {namespace}")
    print()

    # Initialize clients
    identity_client = oci.identity.IdentityClient(oci_config)
    la_client = oci.log_analytics.LogAnalyticsClient(oci_config)

    # List ALL compartments
    print("[2] Listing ALL compartments in tenancy tree...")
    all_compartments = []

    response = identity_client.list_compartments(
        compartment_id=tenancy_id,
        compartment_id_in_subtree=True,
        lifecycle_state="ACTIVE",
        access_level="ACCESSIBLE",
    )
    all_compartments.extend(response.data)

    while response.has_next_page:
        response = identity_client.list_compartments(
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            lifecycle_state="ACTIVE",
            access_level="ACCESSIBLE",
            page=response.next_page,
        )
        all_compartments.extend(response.data)

    print(f"    Found {len(all_compartments)} compartments")
    print()

    # Show compartment hierarchy
    print("[3] Compartment list:")
    for i, comp in enumerate(all_compartments[:20]):  # Show first 20
        print(f"    {i+1}. {comp.name} ({comp.id[:30]}...)")
    if len(all_compartments) > 20:
        print(f"    ... and {len(all_compartments) - 20} more")
    print()

    # Test query on each compartment
    print("[4] Testing query on each compartment...")
    print("    Query: * | stats count as LogCount by 'Log Source'")
    print("    Time range: Last 7 days")
    print()

    time_end = datetime.utcnow()
    time_start = time_end - timedelta(days=7)

    time_range = oci.log_analytics.models.TimeRange(
        time_start=time_start,
        time_end=time_end,
        time_zone="UTC",
    )

    results_by_compartment = {}
    total_log_count = 0
    all_log_sources = {}

    for i, comp in enumerate(all_compartments):
        try:
            query_details = oci.log_analytics.models.QueryDetails(
                compartment_id=comp.id,
                compartment_id_in_subtree=False,  # Just this compartment
                query_string="* | stats count as LogCount by 'Log Source'",
                sub_system=oci.log_analytics.models.QueryDetails.SUB_SYSTEM_LOG,
                time_filter=time_range,
                max_total_count=1000,
            )

            response = la_client.query(
                namespace_name=namespace,
                query_details=query_details,
            )

            if response.data.items:
                comp_total = 0
                for item in response.data.items:
                    if hasattr(item, 'values'):
                        values = item.values
                        if callable(values):
                            values = list(values())
                        log_source = values[0] if len(values) > 0 else "Unknown"
                        count = values[1] if len(values) > 1 else 0
                        comp_total += count
                        all_log_sources[log_source] = all_log_sources.get(log_source, 0) + count

                if comp_total > 0:
                    results_by_compartment[comp.name] = comp_total
                    total_log_count += comp_total
                    print(f"    ✓ {comp.name}: {comp_total:,} logs")

        except Exception as e:
            if "NotAuthorized" not in str(e) and "404" not in str(e):
                print(f"    ✗ {comp.name}: Error - {str(e)[:50]}")

    print()
    print("=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print()

    print(f"Total compartments found: {len(all_compartments)}")
    print(f"Compartments with logs: {len(results_by_compartment)}")
    print(f"Total log count: {total_log_count:,}")
    print()

    print("Log sources found:")
    for source, count in sorted(all_log_sources.items(), key=lambda x: -x[1]):
        print(f"  • {source}: {count:,}")
    print()

    print("Compartments with logs:")
    for comp_name, count in sorted(results_by_compartment.items(), key=lambda x: -x[1]):
        print(f"  • {comp_name}: {count:,}")
    print()

    # Compare with include_subcompartments at root
    print("=" * 60)
    print("  COMPARISON TEST")
    print("=" * 60)
    print()

    print("[5] Testing query at TENANCY level with include_subcompartments=True...")
    try:
        query_details = oci.log_analytics.models.QueryDetails(
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            query_string="* | stats count as LogCount by 'Log Source'",
            sub_system=oci.log_analytics.models.QueryDetails.SUB_SYSTEM_LOG,
            time_filter=time_range,
            max_total_count=1000,
        )

        response = la_client.query(
            namespace_name=namespace,
            query_details=query_details,
        )

        tenancy_total = 0
        print("    Results at tenancy level:")
        if response.data.items:
            for item in response.data.items:
                if hasattr(item, 'values'):
                    values = item.values
                    if callable(values):
                        values = list(values())
                    log_source = values[0] if len(values) > 0 else "Unknown"
                    count = values[1] if len(values) > 1 else 0
                    tenancy_total += count
                    print(f"      • {log_source}: {count:,}")
        print(f"    Total at tenancy level: {tenancy_total:,}")
    except Exception as e:
        print(f"    Error: {e}")

    print()
    print("=" * 60)
    print("  ANALYSIS")
    print("=" * 60)
    print()
    print(f"Sum of individual compartment queries: {total_log_count:,}")
    print(f"Query at tenancy with subtree=True:    {tenancy_total:,}")
    print(f"Expected (from OCI Console):           ~38,000,000")
    print()

    if total_log_count > tenancy_total:
        print("✓ Individual compartment queries return MORE data than tenancy query")
        print("  This confirms the OCI API bug with tenancy-level subtree queries")
    else:
        print("⚠ Individual compartment queries return SAME or LESS data")
        print("  This suggests a different issue")

    if total_log_count < 30000000:
        print()
        print("⚠ Still missing logs. Possible causes:")
        print("  1. Some compartments may not be accessible to this API user")
        print("  2. Logs may be in a different region")
        print("  3. Log group permissions may restrict access")

if __name__ == "__main__":
    main()
