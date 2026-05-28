from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieve_policies import (
    build_owners_from_emails,
    collect_backup_data,
    load_env_config,
    owner_key_for_resource,
    serialize_dynamic_group,
    serialize_policy,
    write_backup,
)


@dataclass
class _Resource:
    id: str
    name: str
    compartment_id: str = "dummy-tenancy-root"
    description: str = ""
    statements: list[str] = field(default_factory=list)
    matching_rule: str = ""
    lifecycle_state: str = "ACTIVE"
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, object]] = field(default_factory=dict)
    time_created: datetime = datetime(2026, 5, 28, 8, 30, tzinfo=timezone.utc)


@dataclass
class _Response:
    data: object


@dataclass
class _Compartment:
    id: str
    name: str


class _Identity:
    def __init__(self, dynamic_groups=None, dynamic_group_details=None):
        self.compartments = [
            _Compartment("dummy-compartment-owner-one", "OwnerOne"),
            _Compartment("dummy-compartment-owner-two", "OwnerTwo"),
        ]
        self.root_policies = []
        self.compartment_policies = {
            "dummy-compartment-owner-one": [_owner_one_policy()],
            "dummy-compartment-owner-two": [
                _Resource(
                    id="dummy-policy-owner-two",
                    name="OwnerTwoPolicy",
                    statements=["Allow group OwnerTwoAdmins to inspect instances in tenancy"],
                    defined_tags={
                        "Oracle_Tags": {
                            "CreatedBy": "oracleidentitycloudservice/owner.two@example.com"
                        }
                    },
                )
            ],
        }
        self.dynamic_groups = dynamic_groups or []
        self.dynamic_group_details = dynamic_group_details or {}

    def list_compartments(self, compartment_id, **kwargs):
        assert kwargs["compartment_id_in_subtree"] is True
        assert kwargs["lifecycle_state"] == "ACTIVE"
        return _Response(self.compartments)

    def list_policies(self, compartment_id):
        if compartment_id == "dummy-tenancy":
            return _Response(self.root_policies)
        return _Response(self.compartment_policies.get(compartment_id, []))

    def list_dynamic_groups(self, compartment_id):
        assert compartment_id == "dummy-tenancy"
        return _Response(self.dynamic_groups)

    def get_dynamic_group(self, dynamic_group_id):
        return _Response(self.dynamic_group_details[dynamic_group_id])


def _owner_one_policy() -> _Resource:
    return _Resource(
        id="dummy-policy-owner-one",
        name="OwnerOnePolicy",
        description="Owner one compartment policy",
        statements=[
            "Allow group OwnerOneAdmins to manage all-resources in compartment OwnerOne",
            "Allow dynamic-group OwnerOneWorkers to use instance-family in tenancy",
        ],
        defined_tags={
            "Oracle_Tags": {
                "CreatedBy": "oracleidentitycloudservice/owner.one@example.com"
            },
            "CCA_Basic_Tag": {
                "email": "oracleidentitycloudservice/owner.one@example.com"
            },
        },
    )


def test_owner_key_for_resource_uses_oracle_tags_created_by():
    owners = build_owners_from_emails(["owner.one@example.com"])

    assert owner_key_for_resource(_owner_one_policy(), owners) == "owner.one"


def test_owner_key_for_resource_uses_cca_basic_email_when_created_by_missing():
    owners = build_owners_from_emails(["owner.two@example.com"])
    resource = _Resource(
        id="dummy-policy-owner-two",
        name="OwnerTwoPolicy",
        defined_tags={
            "CCA_Basic_Tag": {
                "email": "oracleidentitycloudservice/owner.two@example.com"
            }
        },
    )

    assert owner_key_for_resource(resource, owners) == "owner.two"


def test_load_env_config_builds_owners_from_comma_separated_emails(tmp_path):
    config_path = tmp_path / "owners.env"
    config_path.write_text(
        "\n".join(
            [
                "# Enter comma-separated email addresses when backing up more than one person.",
                "OCI_PROFILE=DEFAULT",
                "OWNER_EMAILS=owner.one@example.com, owner.two@example.com",
                "",
            ]
        )
    )

    config = load_env_config(config_path)

    assert config.profile == "DEFAULT"
    assert list(config.owners) == ["owner.one", "owner.two"]
    assert config.owners["owner.one"].folder == "owner.one"
    assert config.owners["owner.one"].tag_values == (
        "oracleidentitycloudservice/owner.one@example.com",
        "owner.one@example.com",
    )


def test_owners_env_example_explains_comma_separated_emails():
    example = Path(__file__).resolve().parents[1] / "owners.env.example"
    text = example.read_text()

    assert "comma-separated email addresses" in text
    assert "OWNER_EMAILS=" in text


def test_collect_backup_data_discovers_compartments_and_routes_by_owner(monkeypatch):
    owners = build_owners_from_emails(
        ["owner.one@example.com", "owner.two@example.com"]
    )
    progress_messages = []

    def _fake_list_all(client_method, compartment_id):
        return client_method(compartment_id).data

    monkeypatch.setattr("retrieve_policies._list_all", _fake_list_all)
    monkeypatch.setattr(
        "retrieve_policies.oci.pagination.list_call_get_all_results",
        lambda client_method, compartment_id, **kwargs: client_method(compartment_id, **kwargs),
    )

    root_policies, compartment_policies, dynamic_groups, warnings = collect_backup_data(
        identity=_Identity(),
        tenancy_id="dummy-tenancy",
        tenancy_name="example-tenancy",
        owners=owners,
        progress=progress_messages.append,
    )

    assert root_policies == []
    assert dynamic_groups == []
    assert warnings == ()
    by_owner = {policy["owner"]: policy for policy in compartment_policies}
    assert by_owner["owner.one"]["scope_name"] == "OwnerOne"
    assert by_owner["owner.two"]["scope_name"] == "OwnerTwo"
    assert progress_messages == [
        "Listing root tenancy policies",
        "Listing active compartments",
        "Scanning policies in 2 active compartment(s)",
        "Listing dynamic groups",
    ]


def test_collect_backup_data_fetches_dynamic_group_detail_for_matching_rule(monkeypatch):
    owners = build_owners_from_emails(["owner.one@example.com"])
    dynamic_group_id = "dummy-dynamic-group-workers"
    summary_group = _Resource(
        id=dynamic_group_id,
        name="OwnerOneWorkers",
        matching_rule=None,
        defined_tags={
            "Oracle_Tags": {
                "CreatedBy": "oracleidentitycloudservice/owner.one@example.com"
            }
        },
    )
    detail_group = _Resource(
        id=dynamic_group_id,
        name="OwnerOneWorkers",
        matching_rule="ALL {instance.compartment.id = 'dummy-compartment-owner-one'}",
        defined_tags=summary_group.defined_tags,
    )

    def _fake_list_all(client_method, compartment_id):
        return client_method(compartment_id).data

    monkeypatch.setattr("retrieve_policies._list_all", _fake_list_all)
    monkeypatch.setattr(
        "retrieve_policies.oci.pagination.list_call_get_all_results",
        lambda client_method, compartment_id, **kwargs: client_method(compartment_id, **kwargs),
    )

    _, _, dynamic_groups, warnings = collect_backup_data(
        identity=_Identity(
            dynamic_groups=[summary_group],
            dynamic_group_details={dynamic_group_id: detail_group},
        ),
        tenancy_id="dummy-tenancy",
        tenancy_name="example-tenancy",
        owners=owners,
    )

    assert warnings == ()
    assert dynamic_groups[0]["matching_rule"] == detail_group.matching_rule


def test_write_backup_separates_files_by_owner(tmp_path):
    owners = build_owners_from_emails(
        ["owner.one@example.com", "owner.two@example.com"]
    )
    generated_at = datetime(2026, 5, 28, 9, 30, 12, tzinfo=timezone.utc)
    root_policy = serialize_policy(
        _Resource(
            id="dummy-policy-root",
            name="RootPolicy",
            statements=["Allow group RootAdmins to inspect compartments in tenancy"],
            defined_tags={
                "Oracle_Tags": {
                    "CreatedBy": "oracleidentitycloudservice/owner.one@example.com"
                }
            },
        ),
        scope_type="root",
        scope_name="example-tenancy",
        owner_key="owner.one",
    )
    compartment_policy = serialize_policy(
        _owner_one_policy(),
        scope_type="compartment",
        scope_name="OwnerOne",
        owner_key="owner.one",
    )
    dynamic_group = serialize_dynamic_group(
        _Resource(
            id="dummy-dynamic-group-workers",
            name="OwnerOneWorkers",
            description="Workers owned by owner one",
            matching_rule="ALL {instance.compartment.id = 'dummy-compartment-x'}",
            defined_tags={
                "CCA_Basic_Tag": {
                    "email": "oracleidentitycloudservice/owner.one@example.com"
                }
            },
        ),
        owner_key="owner.one",
    )

    result = write_backup(
        out_base=tmp_path,
        tenancy_id="dummy-tenancy",
        tenancy_name="example-tenancy",
        profile="DEFAULT",
        owners=owners,
        root_policies=[root_policy],
        compartment_policies=[compartment_policy],
        dynamic_groups=[dynamic_group],
        generated_at=generated_at,
    )

    backup_dir = result.path
    assert backup_dir.name == "20260528T093012Z"
    assert (backup_dir / "metadata.json").exists()
    assert (backup_dir / "README.md").exists()
    assert (backup_dir / "owner.one" / "policies-root.json").exists()
    assert (backup_dir / "owner.one" / "policies-compartment.json").exists()
    assert (backup_dir / "owner.one" / "dynamic-groups.json").exists()
    assert (backup_dir / "owner.one" / "README.md").exists()
    assert (backup_dir / "owner.one" / "report.html").exists()
    assert (backup_dir / "owner.two" / "policies-root.json").exists()
    assert (backup_dir / "owner.two" / "report.html").exists()
    assert json.loads((backup_dir / "owner.one" / "policies-root.json").read_text())[0]["name"] == "RootPolicy"
    assert json.loads((backup_dir / "owner.two" / "policies-root.json").read_text()) == []

    owner_readme = (backup_dir / "owner.one" / "README.md").read_text()
    assert "# IAM Backup - owner.one" in owner_readme
    assert "## Root / Tenancy Policies" in owner_readme
    assert "### RootPolicy" in owner_readme
    assert "1. Allow group RootAdmins to inspect compartments in tenancy" in owner_readme
    assert "### OwnerOne / OwnerOnePolicy" in owner_readme
    assert "## Dynamic Groups" in owner_readme
    assert "### OwnerOneWorkers" in owner_readme

    owner_html = (backup_dir / "owner.one" / "report.html").read_text()
    assert "<title>IAM Backup - owner.one</title>" in owner_html
    assert "RootPolicy" in owner_html
    assert "OwnerOne / OwnerOnePolicy" in owner_html
    assert "Allow group RootAdmins to inspect compartments in tenancy" in owner_html
    assert "OwnerOneWorkers" in owner_html
    assert "Copy statement" in owner_html
    assert "Copy all statements" in owner_html
    assert "Allow group OwnerOneAdmins to manage all-resources in compartment OwnerOne&#10;Allow dynamic-group OwnerOneWorkers to use instance-family in tenancy" in owner_html
    assert "Copy rule" in owner_html

    metadata = json.loads((backup_dir / "metadata.json").read_text())
    assert metadata["run_folder"] == "20260528T093012Z"
    assert metadata["owners"]["owner.one"]["folder"] == "owner.one"
    assert metadata["owners"]["owner.two"]["folder"] == "owner.two"
