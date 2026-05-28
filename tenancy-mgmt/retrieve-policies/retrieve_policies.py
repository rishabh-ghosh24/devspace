#!/usr/bin/env python3
"""Read-only backup of selected OCI IAM policies and dynamic groups.

The script reads IAM resources from OCI and writes local JSON/Markdown files.
It does not create, update, or delete OCI resources.
"""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import oci
from oci.identity import IdentityClient

OWNER_TAGS = (
    ("Oracle_Tags", "CreatedBy"),
    ("CCA_Basic_Tag", "email"),
)


@dataclass(frozen=True)
class OwnerConfig:
    folder: str
    display_name: str
    email: str
    tag_values: tuple[str, ...]


@dataclass(frozen=True)
class EnvConfig:
    profile: str
    out_base: Path
    owners: dict[str, OwnerConfig]


@dataclass(frozen=True)
class BackupResult:
    path: Path
    counts: dict[str, dict[str, int]]
    warnings: tuple[str, ...] = ()


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "owners.env"


def _folder_from_email(email: str) -> str:
    local_part = email.strip().lower()
    if local_part.startswith("oracleidentitycloudservice/"):
        local_part = local_part.split("/", 1)[1]
    return local_part.split("@", 1)[0]


def _tag_values_for_email(email: str) -> tuple[str, ...]:
    normalized = email.strip().lower()
    if normalized.startswith("oracleidentitycloudservice/"):
        normalized = normalized.split("/", 1)[1]
    return (f"oracleidentitycloudservice/{normalized}", normalized)


def build_owners_from_emails(emails: Iterable[str]) -> dict[str, OwnerConfig]:
    owners: dict[str, OwnerConfig] = {}
    for raw_email in emails:
        email = raw_email.strip().lower()
        if not email:
            continue
        folder = _folder_from_email(email)
        if not folder:
            raise ValueError(f"invalid owner email: {raw_email}")
        owners[folder] = OwnerConfig(
            folder=folder,
            display_name=folder,
            email=email.removeprefix("oracleidentitycloudservice/"),
            tag_values=_tag_values_for_email(email),
        )
    if not owners:
        raise ValueError("OWNER_EMAILS must include at least one email address")
    return owners


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(f"{path}:{line_number}: expected KEY=VALUE")
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if not key:
            raise ValueError(f"{path}:{line_number}: empty key")
        values[key] = value
    return values


def load_env_config(path: Path) -> EnvConfig:
    values = _parse_env_file(path)
    profile = values.get("OCI_PROFILE", "DEFAULT")
    out_base = Path(values.get("OUTPUT_DIR", "backups"))
    if not out_base.is_absolute():
        out_base = path.parent / out_base
    emails = [email.strip() for email in values.get("OWNER_EMAILS", "").split(",")]
    return EnvConfig(
        profile=profile,
        out_base=out_base,
        owners=build_owners_from_emails(emails),
    )


def _as_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _defined_tag_value(resource: Any, namespace: str, key: str) -> str | None:
    defined_tags = getattr(resource, "defined_tags", None) or {}
    namespace_values = defined_tags.get(namespace) or {}
    value = namespace_values.get(key)
    if value is None:
        return None
    return str(value)


def owner_tag_values(resource: Any) -> tuple[str, ...]:
    values: list[str] = []
    for namespace, key in OWNER_TAGS:
        value = _defined_tag_value(resource, namespace, key)
        if value:
            values.append(value)
    return tuple(values)


def owner_key_for_resource(resource: Any, owners: Mapping[str, OwnerConfig]) -> str | None:
    values = {value.lower() for value in owner_tag_values(resource)}
    for key, owner in owners.items():
        if any(tag_value.lower() in values for tag_value in owner.tag_values):
            return key
    return None


def _created_by(resource: Any) -> str | None:
    values = owner_tag_values(resource)
    return values[0] if values else None


def _resource_base(resource: Any, *, owner_key: str) -> dict[str, Any]:
    return {
        "owner": owner_key,
        "id": getattr(resource, "id", None),
        "name": getattr(resource, "name", None),
        "description": getattr(resource, "description", None),
        "compartment_id": getattr(resource, "compartment_id", None),
        "lifecycle_state": getattr(resource, "lifecycle_state", None),
        "created_by": _created_by(resource),
        "owner_tag_values": list(owner_tag_values(resource)),
        "defined_tags": getattr(resource, "defined_tags", None) or {},
        "freeform_tags": getattr(resource, "freeform_tags", None) or {},
        "time_created": _as_iso(getattr(resource, "time_created", None)),
    }


def serialize_policy(
    resource: Any,
    *,
    scope_type: str,
    scope_name: str,
    owner_key: str,
) -> dict[str, Any]:
    data = _resource_base(resource, owner_key=owner_key)
    data.update(
        {
            "scope_type": scope_type,
            "scope_name": scope_name,
            "statements": list(getattr(resource, "statements", None) or []),
            "version_date": _as_iso(getattr(resource, "version_date", None)),
        }
    )
    return data


def serialize_dynamic_group(resource: Any, *, owner_key: str) -> dict[str, Any]:
    data = _resource_base(resource, owner_key=owner_key)
    data["matching_rule"] = getattr(resource, "matching_rule", None)
    return data


def _sort_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda r: (r.get("scope_name") or "", r.get("name") or ""))


def _records_for_owner(records: Iterable[dict[str, Any]], owner_key: str) -> list[dict[str, Any]]:
    return _sort_records(record for record in records if record.get("owner") == owner_key)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _append_policy(lines: list[str], policy: dict[str, Any], *, title: str) -> None:
    lines.extend(
        [
            f"### {title}",
            "",
            f"- OCID: `{policy.get('id')}`",
            f"- Created by: `{policy.get('created_by') or 'unknown'}`",
            f"- Scope: `{policy.get('scope_name')}`",
            f"- Lifecycle: `{policy.get('lifecycle_state')}`",
        ]
    )
    description = policy.get("description")
    if description:
        lines.append(f"- Description: {description}")
    lines.extend(["", "Statements:"])
    statements = policy.get("statements") or []
    if statements:
        for index, statement in enumerate(statements, start=1):
            lines.append(f"{index}. {statement}")
    else:
        lines.append("No statements.")
    lines.append("")


def _owner_readme(
    *,
    owner: OwnerConfig,
    tenancy_name: str,
    root_policies: list[dict[str, Any]],
    compartment_policies: list[dict[str, Any]],
    dynamic_groups: list[dict[str, Any]],
) -> str:
    lines = [
        f"# IAM Backup - {owner.display_name}",
        "",
        f"- Tenancy: `{tenancy_name}`",
        f"- Owner email: `{owner.email}`",
        f"- Owner tag values: `{', '.join(owner.tag_values)}`",
        "",
        "## Root / Tenancy Policies",
        "",
    ]
    if root_policies:
        for policy in root_policies:
            _append_policy(lines, policy, title=policy.get("name") or "unnamed-policy")
    else:
        lines.extend(["No matching root policies.", ""])

    lines.extend(["## Compartment Policies", ""])
    if compartment_policies:
        for policy in compartment_policies:
            title = f"{policy.get('scope_name')} / {policy.get('name')}"
            _append_policy(lines, policy, title=title)
    else:
        lines.extend(["No matching compartment policies.", ""])

    lines.extend(["## Dynamic Groups", ""])
    if dynamic_groups:
        for group in dynamic_groups:
            lines.extend(
                [
                    f"### {group.get('name')}",
                    "",
                    f"- OCID: `{group.get('id')}`",
                    f"- Created by: `{group.get('created_by') or 'unknown'}`",
                    f"- Lifecycle: `{group.get('lifecycle_state')}`",
                ]
            )
            description = group.get("description")
            if description:
                lines.append(f"- Description: {description}")
            lines.extend(["", "Matching rule:", "", "```text", group.get("matching_rule") or "", "```", ""])
    else:
        lines.extend(["No matching dynamic groups.", ""])

    return "\n".join(lines).rstrip() + "\n"



def _h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _attr(value: Any) -> str:
    return _h(value).replace("\n", "&#10;")


def _copy_button(label: str, value: Any) -> str:
    return f'<button class="copy-button" type="button" data-copy="{_attr(value)}">{_h(label)}</button>'


def _policy_title(policy: dict[str, Any]) -> str:
    if policy.get("scope_type") == "compartment":
        return f"{policy.get('scope_name')} / {policy.get('name')}"
    return str(policy.get("name") or "unnamed-policy")


def _policy_cards(policies: list[dict[str, Any]], *, empty_text: str) -> str:
    if not policies:
        return f'<p class="empty">{_h(empty_text)}</p>'

    cards: list[str] = []
    for policy in policies:
        statements = policy.get("statements") or []
        if statements:
            all_statements = "\n".join(str(statement) for statement in statements)
            statements_header = (
                '<div class="statement-toolbar">'
                '<div class="subhead">Statements</div>'
                f'{_copy_button("Copy all statements", all_statements)}'
                "</div>"
            )
            statement_items = []
            for index, statement in enumerate(statements, start=1):
                statement_items.append(
                    "".join(
                        [
                            '<li class="statement-row">',
                            f'<div class="statement-index">{index}</div>',
                            f'<pre class="statement-text">{_h(statement)}</pre>',
                            _copy_button("Copy statement", statement),
                            "</li>",
                        ]
                    )
                )
            statements_html = '<ol class="statement-list">' + "".join(statement_items) + "</ol>"
        else:
            statements_header = '<div class="subhead">Statements</div>'
            statements_html = '<p class="empty small">No statements.</p>'

        description = policy.get("description")
        description_html = f'<p class="description">{_h(description)}</p>' if description else ""
        cards.append(
            "".join(
                [
                    '<article class="card policy-card">',
                    '<div class="card-head">',
                    f'<h3>{_h(_policy_title(policy))}</h3>',
                    f'<span class="state">{_h(policy.get("lifecycle_state") or "unknown")}</span>',
                    "</div>",
                    description_html,
                    '<dl class="meta-grid">',
                    f'<div><dt>OCID</dt><dd><code>{_h(policy.get("id"))}</code></dd></div>',
                    f'<div><dt>Created by</dt><dd><code>{_h(policy.get("created_by") or "unknown")}</code></dd></div>',
                    f'<div><dt>Scope</dt><dd>{_h(policy.get("scope_name") or "unknown")}</dd></div>',
                    f'<div><dt>Created</dt><dd>{_h(policy.get("time_created") or "unknown")}</dd></div>',
                    "</dl>",
                    statements_header,
                    statements_html,
                    "</article>",
                ]
            )
        )
    return "".join(cards)


def _dynamic_group_cards(dynamic_groups: list[dict[str, Any]]) -> str:
    if not dynamic_groups:
        return '<p class="empty">No matching dynamic groups.</p>'

    cards: list[str] = []
    for group in dynamic_groups:
        matching_rule = group.get("matching_rule") or ""
        description = group.get("description")
        description_html = f'<p class="description">{_h(description)}</p>' if description else ""
        cards.append(
            "".join(
                [
                    '<article class="card group-card">',
                    '<div class="card-head">',
                    f'<h3>{_h(group.get("name") or "unnamed-dynamic-group")}</h3>',
                    f'<span class="state">{_h(group.get("lifecycle_state") or "unknown")}</span>',
                    "</div>",
                    description_html,
                    '<dl class="meta-grid">',
                    f'<div><dt>OCID</dt><dd><code>{_h(group.get("id"))}</code></dd></div>',
                    f'<div><dt>Created by</dt><dd><code>{_h(group.get("created_by") or "unknown")}</code></dd></div>',
                    f'<div><dt>Created</dt><dd>{_h(group.get("time_created") or "unknown")}</dd></div>',
                    "</dl>",
                    '<div class="subhead">Matching rule</div>',
                    '<div class="rule-box">',
                    f'<pre>{_h(matching_rule)}</pre>',
                    _copy_button("Copy rule", matching_rule),
                    "</div>",
                    "</article>",
                ]
            )
        )
    return "".join(cards)


def _owner_html(
    *,
    owner: OwnerConfig,
    tenancy_name: str,
    profile: str,
    generated_at: datetime,
    root_policies: list[dict[str, Any]],
    compartment_policies: list[dict[str, Any]],
    dynamic_groups: list[dict[str, Any]],
) -> str:
    total_policies = len(root_policies) + len(compartment_policies)
    css = """
    :root { color-scheme: light; --ink: #17202a; --muted: #5f6b7a; --line: #d9e2ec; --panel: #ffffff; --wash: #f6f8fb; --accent: #1f6feb; --accent-ink: #0b3d91; --good: #137333; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--wash); line-height: 1.5; }
    header { background: #ffffff; border-bottom: 1px solid var(--line); padding: 28px 32px 22px; }
    main { max-width: 1180px; margin: 0 auto; padding: 26px 24px 44px; }
    h1 { margin: 0 0 10px; font-size: 30px; font-weight: 720; }
    h2 { margin: 34px 0 14px; font-size: 20px; }
    h3 { margin: 0; font-size: 17px; line-height: 1.3; }
    code { font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }
    .subtitle { margin: 0; color: var(--muted); max-width: 920px; }
    .summary { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; margin-top: 20px; }
    .summary-card, .card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); }
    .summary-card { padding: 14px 16px; }
    .summary-card span { display: block; color: var(--muted); font-size: 12px; }
    .summary-card strong { display: block; margin-top: 4px; font-size: 22px; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
    .toolbar a { color: var(--accent-ink); background: #eaf2ff; border: 1px solid #c7dcff; border-radius: 6px; padding: 7px 10px; text-decoration: none; font-size: 13px; font-weight: 650; }
    .section-grid { display: grid; grid-template-columns: 1fr; gap: 14px; }
    .card { padding: 18px; }
    .card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 14px; }
    .state { flex: 0 0 auto; border-radius: 999px; background: #e9f6ec; color: var(--good); border: 1px solid #bde5c8; padding: 3px 9px; font-size: 12px; font-weight: 700; }
    .description { margin: 0 0 14px; color: var(--muted); }
    .meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 18px; margin: 0 0 16px; }
    .meta-grid div { min-width: 0; }
    .meta-grid dt { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .meta-grid dd { margin: 3px 0 0; overflow-wrap: anywhere; }
    .subhead { margin: 0; color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; }
    .statement-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 16px 0 8px; }
    .statement-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
    .statement-row { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 10px; align-items: start; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: #fbfdff; }
    .statement-index { width: 26px; height: 26px; display: grid; place-items: center; border-radius: 50%; background: #eaf2ff; color: var(--accent-ink); font-size: 12px; font-weight: 800; }
    pre { margin: 0; white-space: pre-wrap; word-break: break-word; font-family: "SFMono-Regular", Consolas, monospace; font-size: 12px; }
    .rule-box { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: start; padding: 12px; border: 1px solid var(--line); border-radius: 8px; background: #fbfdff; }
    .copy-button { border: 1px solid #c7dcff; background: #f2f7ff; color: var(--accent-ink); border-radius: 6px; padding: 6px 9px; font-size: 12px; font-weight: 750; cursor: pointer; white-space: nowrap; }
    .copy-button:hover { background: #e3efff; }
    .empty { margin: 0; padding: 14px; border: 1px dashed var(--line); border-radius: 8px; background: #ffffff; color: var(--muted); }
    .small { padding: 0; border: 0; }
    footer { color: var(--muted); font-size: 12px; margin-top: 32px; }
    @media (max-width: 760px) { header { padding: 22px 18px; } main { padding: 18px; } .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } .meta-grid { grid-template-columns: 1fr; } .statement-row, .rule-box { grid-template-columns: 1fr; } .statement-index { display: none; } }
    """
    script = """
    document.addEventListener('click', async (event) => {
      const button = event.target.closest('[data-copy]');
      if (!button) return;
      const original = button.textContent;
      try {
        await navigator.clipboard.writeText(button.dataset.copy || '');
        button.textContent = 'Copied';
        setTimeout(() => { button.textContent = original; }, 1200);
      } catch (error) {
        button.textContent = 'Select text';
        setTimeout(() => { button.textContent = original; }, 1600);
      }
    });
    """
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IAM Backup - {_h(owner.display_name)}</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>IAM Backup - {_h(owner.display_name)}</h1>
    <p class="subtitle">Read-only OCI IAM snapshot for {_h(tenancy_name)} using profile <code>{_h(profile)}</code>. Resources are included only when owner tags match this email: <code>{_h(owner.email)}</code>.</p>
    <div class="summary">
      <div class="summary-card"><span>Root policies</span><strong>{len(root_policies)}</strong></div>
      <div class="summary-card"><span>Compartment policies</span><strong>{len(compartment_policies)}</strong></div>
      <div class="summary-card"><span>Dynamic groups</span><strong>{len(dynamic_groups)}</strong></div>
      <div class="summary-card"><span>Total policies</span><strong>{total_policies}</strong></div>
    </div>
    <div class="toolbar">
      <a href="policies-root.json">Root policies JSON</a>
      <a href="policies-compartment.json">Compartment policies JSON</a>
      <a href="dynamic-groups.json">Dynamic groups JSON</a>
      <a href="README.md">Markdown report</a>
    </div>
  </header>
  <main>
    <section>
      <h2>Owner Context</h2>
      <article class="card">
        <dl class="meta-grid">
          <div><dt>Owner email</dt><dd><code>{_h(owner.email)}</code></dd></div>
          <div><dt>Tag values</dt><dd><code>{_h(", ".join(owner.tag_values))}</code></dd></div>
          <div><dt>Generated</dt><dd>{_h(generated_at.isoformat())}</dd></div>
          <div><dt>Folder</dt><dd>{_h(owner.folder)}</dd></div>
        </dl>
      </article>
    </section>
    <section>
      <h2>Root / Tenancy Policies</h2>
      <div class="section-grid">{_policy_cards(root_policies, empty_text="No matching root policies.")}</div>
    </section>
    <section>
      <h2>Compartment Policies</h2>
      <div class="section-grid">{_policy_cards(compartment_policies, empty_text="No matching compartment policies.")}</div>
    </section>
    <section>
      <h2>Dynamic Groups</h2>
      <div class="section-grid">{_dynamic_group_cards(dynamic_groups)}</div>
    </section>
    <footer>Generated by tenancy-mgmt/retrieve-policies. This report is local-only and was built from read-only OCI API responses.</footer>
  </main>
  <script>{script}</script>
</body>
</html>
"""


def _top_readme(
    *,
    tenancy_name: str,
    tenancy_id: str,
    profile: str,
    run_folder: str,
    owners: Mapping[str, OwnerConfig],
    counts: dict[str, dict[str, int]],
    warnings: Sequence[str],
) -> str:
    lines = [
        f"# OCI IAM Backup - {tenancy_name}",
        "",
        f"- Run folder: `{run_folder}`",
        f"- Tenancy OCID: `{tenancy_id}`",
        f"- OCI profile: `{profile}`",
        "",
        "Each owner folder contains root policies, that owner's compartment policies, dynamic groups, and a readable README.",
        "",
        "## Owners",
        "",
    ]
    for key, owner in owners.items():
        owner_counts = counts[key]
        lines.extend(
            [
                f"### {owner.display_name}",
                "",
                f"- Folder: `{owner.folder}/`",
                f"- Root policies: {owner_counts['root_policies']}",
                f"- Compartment policies: {owner_counts['compartment_policies']}",
                f"- Dynamic groups: {owner_counts['dynamic_groups']}",
                "",
            ]
        )
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _unique_backup_dir(out_base: Path, generated_at: datetime) -> Path:
    stamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = out_base / stamp
    if not candidate.exists():
        return candidate
    for index in range(2, 100):
        numbered = out_base / f"{stamp}-{index}"
        if not numbered.exists():
            return numbered
    raise RuntimeError(f"could not find unused backup directory under {out_base}")


def _owner_metadata(owner: OwnerConfig) -> dict[str, Any]:
    return {
        "folder": owner.folder,
        "display_name": owner.display_name,
        "email": owner.email,
        "tag_values": list(owner.tag_values),
    }


def write_backup(
    *,
    out_base: Path,
    tenancy_id: str,
    tenancy_name: str,
    profile: str,
    owners: Mapping[str, OwnerConfig],
    root_policies: list[dict[str, Any]],
    compartment_policies: list[dict[str, Any]],
    dynamic_groups: list[dict[str, Any]],
    generated_at: datetime | None = None,
    warnings: Iterable[str] = (),
) -> BackupResult:
    generated_at = generated_at or datetime.now(timezone.utc)
    warning_tuple = tuple(warnings)
    backup_dir = _unique_backup_dir(out_base, generated_at)
    backup_dir.mkdir(parents=True)
    run_folder = backup_dir.name

    counts: dict[str, dict[str, int]] = {}
    for owner_key, owner in owners.items():
        owner_dir = backup_dir / owner.folder
        owner_dir.mkdir()
        owner_root = _records_for_owner(root_policies, owner_key)
        owner_compartment = _records_for_owner(compartment_policies, owner_key)
        owner_groups = _records_for_owner(dynamic_groups, owner_key)
        counts[owner_key] = {
            "root_policies": len(owner_root),
            "compartment_policies": len(owner_compartment),
            "dynamic_groups": len(owner_groups),
        }
        _write_json(owner_dir / "policies-root.json", owner_root)
        _write_json(owner_dir / "policies-compartment.json", owner_compartment)
        _write_json(owner_dir / "dynamic-groups.json", owner_groups)
        (owner_dir / "README.md").write_text(
            _owner_readme(
                owner=owner,
                tenancy_name=tenancy_name,
                root_policies=owner_root,
                compartment_policies=owner_compartment,
                dynamic_groups=owner_groups,
            )
        )
        (owner_dir / "report.html").write_text(
            _owner_html(
                owner=owner,
                tenancy_name=tenancy_name,
                profile=profile,
                generated_at=generated_at,
                root_policies=owner_root,
                compartment_policies=owner_compartment,
                dynamic_groups=owner_groups,
            )
        )

    metadata = {
        "generated_at": generated_at.isoformat(),
        "run_folder": run_folder,
        "tenancy_id": tenancy_id,
        "tenancy_name": tenancy_name,
        "profile": profile,
        "read_only_oci_apis": [
            "get_tenancy",
            "get_dynamic_group",
            "list_compartments",
            "list_policies",
            "list_dynamic_groups",
        ],
        "owner_tag_keys": [f"{namespace}.{key}" for namespace, key in OWNER_TAGS],
        "owners": {key: _owner_metadata(owner) for key, owner in owners.items()},
        "counts": counts,
        "warnings": list(warning_tuple),
    }
    _write_json(backup_dir / "metadata.json", metadata)
    (backup_dir / "README.md").write_text(
        _top_readme(
            tenancy_name=tenancy_name,
            tenancy_id=tenancy_id,
            profile=profile,
            run_folder=run_folder,
            owners=owners,
            counts=counts,
            warnings=warning_tuple,
        )
    )
    return BackupResult(path=backup_dir, counts=counts, warnings=warning_tuple)


def _list_all(client_method: Any, compartment_id: str) -> list[Any]:
    return oci.pagination.list_call_get_all_results(client_method, compartment_id).data


def _active_compartment_names(identity: IdentityClient, tenancy_id: str) -> dict[str, str]:
    compartments = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,
        lifecycle_state="ACTIVE",
    ).data
    return {
        compartment.id: compartment.name or compartment.id
        for compartment in compartments
        if getattr(compartment, "id", None)
    }


def _append_owned_policy(
    records: list[dict[str, Any]],
    resource: Any,
    *,
    owners: Mapping[str, OwnerConfig],
    scope_type: str,
    scope_name: str,
) -> None:
    owner_key = owner_key_for_resource(resource, owners)
    if owner_key:
        records.append(
            serialize_policy(
                resource,
                scope_type=scope_type,
                scope_name=scope_name,
                owner_key=owner_key,
            )
        )


def collect_backup_data(
    *,
    identity: IdentityClient,
    tenancy_id: str,
    tenancy_name: str,
    owners: Mapping[str, OwnerConfig],
    progress: Callable[[str], None] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], tuple[str, ...]]:
    progress = progress or (lambda message: None)
    warnings: list[str] = []
    root_policies: list[dict[str, Any]] = []
    compartment_policies: list[dict[str, Any]] = []
    dynamic_groups: list[dict[str, Any]] = []

    progress("Listing root tenancy policies")
    for policy in _list_all(identity.list_policies, tenancy_id):
        _append_owned_policy(
            root_policies,
            policy,
            owners=owners,
            scope_type="root",
            scope_name=tenancy_name,
        )

    progress("Listing active compartments")
    try:
        compartment_names = _active_compartment_names(identity, tenancy_id)
    except oci.exceptions.ServiceError as exc:
        compartment_names = {}
        warnings.append(f"list_compartments failed with {exc.status} {exc.code}")

    progress(f"Scanning policies in {len(compartment_names)} active compartment(s)")
    for compartment_id, compartment_name in sorted(compartment_names.items(), key=lambda item: item[1]):
        try:
            policies = _list_all(identity.list_policies, compartment_id)
        except oci.exceptions.ServiceError as exc:
            warnings.append(f"{compartment_name}: list_policies failed with {exc.status} {exc.code}")
            continue
        for policy in policies:
            matched_owner = owner_key_for_resource(policy, owners)
            if matched_owner:
                compartment_policies.append(
                    serialize_policy(
                        policy,
                        scope_type="compartment",
                        scope_name=compartment_name,
                        owner_key=matched_owner,
                    )
                )

    progress("Listing dynamic groups")
    for group in _list_all(identity.list_dynamic_groups, tenancy_id):
        owner_key = owner_key_for_resource(group, owners)
        if owner_key:
            group_id = getattr(group, "id", None)
            group_name = getattr(group, "name", None) or group_id or "unknown dynamic group"
            detailed_group = group
            if group_id:
                try:
                    detailed_group = identity.get_dynamic_group(group_id).data
                except oci.exceptions.ServiceError as exc:
                    warnings.append(
                        f"{group_name}: get_dynamic_group failed with {exc.status} {exc.code}"
                    )
            else:
                warnings.append(f"{group_name}: get_dynamic_group skipped because id is missing")
            dynamic_groups.append(serialize_dynamic_group(detailed_group, owner_key=owner_key))

    return root_policies, compartment_policies, dynamic_groups, tuple(warnings)


def run_backup(
    *,
    profile: str,
    out_base: Path,
    owners: Mapping[str, OwnerConfig],
    progress: Callable[[str], None] | None = None,
) -> BackupResult:
    progress = progress or (lambda message: None)
    progress(f"Loading OCI config profile {profile}")
    config = oci.config.from_file(profile_name=profile)
    tenancy_id = config["tenancy"]
    identity = IdentityClient(config)
    progress("Loading tenancy details")
    tenancy = identity.get_tenancy(tenancy_id).data
    tenancy_name = getattr(tenancy, "name", None) or tenancy_id
    root_policies, compartment_policies, dynamic_groups, warnings = collect_backup_data(
        identity=identity,
        tenancy_id=tenancy_id,
        tenancy_name=tenancy_name,
        owners=owners,
        progress=progress,
    )
    progress("Writing backup files")
    return write_backup(
        out_base=out_base,
        tenancy_id=tenancy_id,
        tenancy_name=tenancy_name,
        profile=profile,
        owners=owners,
        root_policies=root_policies,
        compartment_policies=compartment_policies,
        dynamic_groups=dynamic_groups,
        warnings=warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Back up selected OCI IAM policies and dynamic groups using read-only APIs."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=script_dir / "owners.env",
        help="Path to owners env file. Default: ./owners.env next to this script.",
    )
    parser.add_argument("--profile", help="OCI config profile override.")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output directory override. Default comes from OUTPUT_DIR or ./backups.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_env_config(args.config)
        profile = args.profile or config.profile
        out_base = args.out or config.out_base
        print(f"Loaded {len(config.owners)} owner(s) from {args.config}", flush=True)
        result = run_backup(
            profile=profile,
            out_base=out_base,
            owners=config.owners,
            progress=lambda message: print(f"[retrieve-policies] {message}", flush=True),
        )
    except Exception as exc:
        print(f"FATAL: {exc}")
        return 2

    print(f"Wrote IAM backup to {result.path}")
    for owner_key, counts in result.counts.items():
        owner = config.owners[owner_key]
        print(f"  {owner.display_name} ({owner.folder}/)")
        print(f"    root policies:        {counts['root_policies']}")
        print(f"    compartment policies: {counts['compartment_policies']}")
        print(f"    dynamic groups:       {counts['dynamic_groups']}")
    if result.warnings:
        print(f"  warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"    - {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
