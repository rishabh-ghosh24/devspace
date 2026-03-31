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
