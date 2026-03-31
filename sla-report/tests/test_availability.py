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
            "--compartment-name", "My Compartment",
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
