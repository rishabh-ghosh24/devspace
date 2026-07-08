#!/usr/bin/env python3
"""
Find stale OCI Logging Analytics entities of one type and generate a delete script.

Why this exists
---------------
OCI Logging Analytics has a per-tenancy entity limit (default 10,000). Ephemeral
entities that LA auto-creates from Service Connector Hub / flow-log ingestion -
VNICs behind Functions, Load Balancers and OKE clusters, Kubernetes pods, etc. -
accumulate against that limit and are never cleaned up on their own. Once the cap
is hit, NEW entity creation silently fails (`LimitExceeded`), which breaks Stack
Monitoring auto-discovery and leaves dashboards empty.

The durable fix is the AUTO_DELETE_SCH_ENTITIES_OF_TYPES preference (see README).
This tool is the interim manual cleanup: it lists entities of one type, ranks them
by last-updated (staleness), reports the age distribution, and writes a reviewable
`oci log-analytics entity delete` script for the oldest / stalest ones.

Staleness signal
----------------
`time-updated` is when the entity last had activity. For an inherently ephemeral
type, "not updated in >3 years" is high-confidence dead. Deleting a still-live
ephemeral entity is self-correcting: LA re-creates it on the next log push.

Usage
-----
  python3 find_stale_entities.py \
      --namespace <ns> --compartment-id <ocid> \
      [--entity-type oci_vcn_vnic] [--profile DEFAULT] \
      [--oldest 300 | --older-than-days 1095] \
      [--out delete_candidates.sh]

Then review and run the generated script yourself:  bash delete_candidates.sh
"""
import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import date, timedelta


def oci_json(args, profile):
    cmd = ["oci"] + args + ["--profile", profile, "--output", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"oci CLI error:\n{r.stderr.strip()[:600]}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def main():
    ap = argparse.ArgumentParser(
        description="Find stale Logging Analytics entities and generate a delete script."
    )
    ap.add_argument("--namespace", required=True, help="Logging Analytics namespace.")
    ap.add_argument("--compartment-id", required=True,
                    help="Compartment holding the entities (often the LogAnalytics compartment).")
    ap.add_argument("--entity-type", default="oci_vcn_vnic",
                    help="Internal entity type name, e.g. oci_vcn_vnic, omc_kubernetes_pod, oci_load_balancer.")
    ap.add_argument("--profile", default="DEFAULT", help="OCI CLI config profile.")
    ap.add_argument("--limit", type=int, default=5000, help="Max entities to fetch.")
    sel = ap.add_mutually_exclusive_group()
    sel.add_argument("--oldest", type=int, help="Select the N oldest entities by last-updated.")
    sel.add_argument("--older-than-days", type=int,
                     help="Select entities not updated in the last D days (e.g. 1095 = 3 years).")
    ap.add_argument("--out", default="delete_candidates.sh", help="Path for the generated delete script.")
    args = ap.parse_args()

    data = oci_json([
        "log-analytics", "entity", "list",
        "--namespace-name", args.namespace,
        "--compartment-id", args.compartment_id,
        "--entity-type-name", args.entity_type,
        "--limit", str(args.limit),
    ], args.profile)
    items = data.get("data", {}).get("items", [])
    print(f"{len(items)} '{args.entity_type}' entities in the compartment.")
    if not items:
        return

    items.sort(key=lambda e: e.get("time-updated", "") or "9999")  # oldest first
    by_year = Counter((e.get("time-updated", "") or "?")[:4] for e in items)
    print("By year (last-updated):", dict(sorted(by_year.items())))
    today = date.today()
    for yrs in (3, 4, 5):
        cut = (today - timedelta(days=365 * yrs)).isoformat()
        n = sum(1 for e in items if (e.get("time-updated", "") or "9999") < cut)
        print(f"  >{yrs}yr untouched (updated < {cut}): {n}")

    if args.older_than_days is not None:
        cut = (today - timedelta(days=args.older_than_days)).isoformat()
        cand = [e for e in items if (e.get("time-updated", "") or "9999") < cut]
        desc = f"not updated in >{args.older_than_days} days (before {cut})"
    else:
        n = args.oldest or 300
        cand = items[:n]
        desc = f"oldest {len(cand)} by last-updated"
    if not cand:
        print("No candidates matched the selection.")
        return

    with open(args.out, "w") as f:
        f.write("#!/usr/bin/env bash\n")
        f.write(f"# {len(cand)} '{args.entity_type}' Logging Analytics entities: {desc}.\n")
        f.write(f"# last-activity range: {cand[0].get('time-updated','')[:10]} .. {cand[-1].get('time-updated','')[:10]}\n")
        f.write("# Review before running. Ephemeral entities auto-recreate if their resource is still live (safety net).\n")
        f.write(f"OCI=oci; NS={args.namespace}; PROFILE={args.profile}\n\n")
        for e in cand:
            f.write(f"# {(e.get('name', '') or '')[:70]}  (updated {e.get('time-updated', '')[:10]})\n")
            f.write(f"$OCI log-analytics entity delete --namespace-name $NS "
                    f"--entity-id {e['id']} --force --profile $PROFILE\n")
    print(f"\nWrote {len(cand)} delete commands -> {args.out}")
    print(f"Candidate age range: {cand[0].get('time-updated', '')[:10]} .. {cand[-1].get('time-updated', '')[:10]}")
    print(f"Review it, then run:  bash {args.out}")


if __name__ == "__main__":
    main()
