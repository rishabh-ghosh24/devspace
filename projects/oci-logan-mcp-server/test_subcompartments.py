#!/usr/bin/env python3
"""
Test script to diagnose include_subcompartments behavior
at tenancy vs sub-compartment level.
"""

import oci
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone

def main():
    # Load configs
    config = oci.config.from_file()
    mcp_config_path = Path.home() / ".oci-la-mcp" / "config.yaml"

    if mcp_config_path.exists():
        with open(mcp_config_path) as f:
            mcp_config = yaml.safe_load(f)
        namespace = mcp_config["log_analytics"]["namespace"]
        compartment = mcp_config["log_analytics"]["default_compartment_id"]
    else:
        print("ERROR: ~/.oci-la-mcp/config.yaml not found")
        return

    # Get tenancy OCID
    tenancy_ocid = config.get("tenancy")

    print("=" * 70)
    print("OCI Log Analytics - Subcompartment Test")
    print("=" * 70)
    print(f"Namespace: {namespace}")
    print(f"Tenancy OCID: {tenancy_ocid}")
    print(f"Config Compartment: {compartment}")
    print(f"Is Tenancy: {compartment.startswith('ocid1.tenancy')}")
    print("=" * 70)

    client = oci.log_analytics.LogAnalyticsClient(config)

    # Time range - last 7 days
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)

    query = "* | stats count as LogCount by 'Log Source' | sort -LogCount"

    # Test 1: Tenancy OCID without subcompartments
    print("\n--- TEST 1: Tenancy OCID, include_subcompartments=FALSE ---")
    try:
        details = oci.log_analytics.models.QueryDetails(
            compartment_id=tenancy_ocid,
            compartment_id_in_subtree=False,
            query_string=query,
            sub_system="LOG",
            time_filter=oci.log_analytics.models.TimeRange(
                time_start=start, time_end=end, time_zone="UTC"
            ),
        )
        result = client.query(namespace_name=namespace, query_details=details)
        print(f"Rows returned: {len(result.data.items)}")
        total = 0
        for item in result.data.items[:5]:
            vals = list(item.values()) if hasattr(item, 'values') and callable(item.values) else item.values
            print(f"  {vals}")
            if len(vals) > 1:
                total += vals[1] if isinstance(vals[1], int) else 0
        print(f"Total logs (top 5): {total:,}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Tenancy OCID with subcompartments
    print("\n--- TEST 2: Tenancy OCID, include_subcompartments=TRUE ---")
    try:
        details = oci.log_analytics.models.QueryDetails(
            compartment_id=tenancy_ocid,
            compartment_id_in_subtree=True,
            query_string=query,
            sub_system="LOG",
            time_filter=oci.log_analytics.models.TimeRange(
                time_start=start, time_end=end, time_zone="UTC"
            ),
        )
        result = client.query(namespace_name=namespace, query_details=details)
        print(f"Rows returned: {len(result.data.items)}")
        total = 0
        for item in result.data.items[:10]:
            vals = list(item.values()) if hasattr(item, 'values') and callable(item.values) else item.values
            print(f"  {vals}")
            if len(vals) > 1:
                total += vals[1] if isinstance(vals[1], int) else 0
        print(f"Total logs (shown): {total:,}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 3: Sub-compartment OCID without subcompartments
    if not compartment.startswith("ocid1.tenancy"):
        print(f"\n--- TEST 3: Sub-Compartment OCID, include_subcompartments=FALSE ---")
        print(f"Compartment: {compartment}")
        try:
            details = oci.log_analytics.models.QueryDetails(
                compartment_id=compartment,
                compartment_id_in_subtree=False,
                query_string=query,
                sub_system="LOG",
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=start, time_end=end, time_zone="UTC"
                ),
            )
            result = client.query(namespace_name=namespace, query_details=details)
            print(f"Rows returned: {len(result.data.items)}")
            total = 0
            for item in result.data.items[:5]:
                vals = list(item.values()) if hasattr(item, 'values') and callable(item.values) else item.values
                print(f"  {vals}")
                if len(vals) > 1:
                    total += vals[1] if isinstance(vals[1], int) else 0
            print(f"Total logs (top 5): {total:,}")
        except Exception as e:
            print(f"ERROR: {e}")

        print(f"\n--- TEST 4: Sub-Compartment OCID, include_subcompartments=TRUE ---")
        try:
            details = oci.log_analytics.models.QueryDetails(
                compartment_id=compartment,
                compartment_id_in_subtree=True,
                query_string=query,
                sub_system="LOG",
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=start, time_end=end, time_zone="UTC"
                ),
            )
            result = client.query(namespace_name=namespace, query_details=details)
            print(f"Rows returned: {len(result.data.items)}")
            total = 0
            for item in result.data.items[:10]:
                vals = list(item.values()) if hasattr(item, 'values') and callable(item.values) else item.values
                print(f"  {vals}")
                if len(vals) > 1:
                    total += vals[1] if isinstance(vals[1], int) else 0
            print(f"Total logs (shown): {total:,}")
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        # Get first-level compartments and try one
        print("\n--- Listing first-level compartments ---")
        identity = oci.identity.IdentityClient(config)
        compartments = identity.list_compartments(
            compartment_id=tenancy_ocid,
            lifecycle_state="ACTIVE"
        ).data

        print(f"Found {len(compartments)} first-level compartments:")
        for c in compartments[:5]:
            print(f"  - {c.name}: {c.id}")

        if compartments:
            test_compartment = compartments[0].id
            print(f"\n--- TEST 3: First Sub-Compartment ({compartments[0].name}), include_subcompartments=TRUE ---")
            try:
                details = oci.log_analytics.models.QueryDetails(
                    compartment_id=test_compartment,
                    compartment_id_in_subtree=True,
                    query_string=query,
                    sub_system="LOG",
                    time_filter=oci.log_analytics.models.TimeRange(
                        time_start=start, time_end=end, time_zone="UTC"
                    ),
                )
                result = client.query(namespace_name=namespace, query_details=details)
                print(f"Rows returned: {len(result.data.items)}")
                total = 0
                for item in result.data.items[:10]:
                    vals = list(item.values()) if hasattr(item, 'values') and callable(item.values) else item.values
                    print(f"  {vals}")
                    if len(vals) > 1:
                        total += vals[1] if isinstance(vals[1], int) else 0
                print(f"Total logs (shown): {total:,}")
            except Exception as e:
                print(f"ERROR: {e}")

    print("\n" + "=" * 70)
    print("CONCLUSION:")
    print("If Test 1 & Test 2 return the same results, OCI SDK ignores")
    print("include_subcompartments at tenancy level. This is API behavior.")
    print("=" * 70)

if __name__ == "__main__":
    main()
