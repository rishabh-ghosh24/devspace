# OCI Logging Analytics - Entity Limit Cleanup

Diagnose and clean up a Logging Analytics namespace that has hit its **entity
limit**, and stop it from recurring.

## The problem

OCI Logging Analytics has a per-tenancy **`entity-instances` limit (default 10,000)**.
Logging Analytics **auto-creates entities** from Service Connector Hub / flow-log
ingestion - a VNIC entity per Functions/Load-Balancer/OKE VNIC, a Kubernetes pod
entity per pod, etc. These are **ephemeral** (the underlying resource is created and
destroyed constantly) but the entities are **never cleaned up on their own**, so they
pile up until the namespace is full.

Once the cap is reached:

- New entity creation **silently fails** with `LimitExceeded {"limitName":"entity-instances","limit":10000}`.
- Stack Monitoring / EBS / host **auto-discovery "succeeds"** (the agent submits its
  result) but **no entities are actually created**, so nothing collects.
- Dashboards and Log Explorer show no data for the new resources.

Real example (the tenancy this tool was built against): **~74% of a maxed 10,000-entity
namespace was ephemeral auto-created entities** - ~3,470 VNICs (mostly one active
Functions app's per-invocation VNICs) + ~3,900 Kubernetes pods - while a legitimate EBS
demo could not create the ~15 entities it needed.

## Diagnose

```bash
NS=<namespace>            # e.g. from: oci log-analytics namespace list ...
CMPT=<compartment-ocid>   # the compartment that holds the entities
P=<profile>

# 1. Confirm the limit is hit - a create returns LimitExceeded:
#    (or check Console -> Governance & Administration -> Limits, Quotas and Usage
#     -> Service: Logging Analytics -> entity-count/entity-instances)

# 2. Count entities by type (find what is filling the namespace).
#    Per type (namespace-wide): the MCP list_entities returns all of a type but no
#    timestamps; the CLI below is compartment-scoped but returns timestamps + OCIDs.
oci log-analytics entity list --namespace-name $NS --compartment-id $CMPT \
  --entity-type-name oci_vcn_vnic --limit 5000 --profile $P \
  --query 'length(data.items)'

# 3. Age + candidate generation for one type (this tool):
python3 find_stale_entities.py --namespace $NS --compartment-id $CMPT \
  --entity-type oci_vcn_vnic --profile $P --oldest 300
```

Common ephemeral type internal-names: `oci_vcn_vnic`, `omc_kubernetes_pod`,
`oci_kubernetes_service`, `oci_load_balancer`, `oci_functions_function`,
`omc_kubernetes_node`.

## The durable fix (stop the churn)

Manual deletion is a treadmill - the source keeps creating new entities (measured at
~300-400/month in the example tenancy, so deleting a few hundred buys only ~weeks). The
real fix is the **`entityLifecycle` auto-delete preference**, which makes the service
delete an auto-created entity when its underlying OCI resource is deleted:

```bash
oci log-analytics preference update --namespace-name $NS --profile $P \
  --items '[{"name":"AUTO_DELETE_SCH_ENTITIES_OF_TYPES","value":"_ALL_"},
            {"name":"AUTO_DELETE_AGENT_ENTITY","value":"TRUE"},
            {"name":"AUTO_DELETE_HOST_ENTITY","value":"TRUE"}]'
```

Notes:
- `AUTO_DELETE_SCH_ENTITIES_OF_TYPES=_ALL_` is the churn-stopper (SCH-created entities).
- These are **namespace-wide / tenant-wide** preferences - in a shared tenancy, make the
  change deliberately, and it needs IAM to manage entity preferences (`entityLifecycle`).
- It is **forward-only**: it prevents future buildup but does **not** drain the existing
  backlog, so pair it with a one-time cleanup (below) and, if still needed, an
  `entity-instances` limit-increase request.
- It never touches live resources or agent-based entities (hosts/agents/EBS/DB).
- Docs: https://docs.oracle.com/en-us/iaas/log-analytics/doc/manage-entities.html
  ("Manage Entity Preferences").

## Interim cleanup with `find_stale_entities.py`

```bash
# Report age distribution and write a delete script for the 300 oldest VNIC entities:
python3 find_stale_entities.py \
  --namespace $NS --compartment-id $CMPT \
  --entity-type oci_vcn_vnic --profile $P \
  --oldest 300 --out delete_candidates.sh

# Or select by age instead of count (3 years = 1095 days):
python3 find_stale_entities.py ... --older-than-days 1095

# Review, then run it AS YOURSELF (never sudo - root has no OCI config):
bash delete_candidates.sh 2>&1 | tee delete.log
```

`delete_candidates.sh` in this directory is a point-in-time sample output (300 oldest
VNIC entities, all last active in 2022). Regenerate a fresh one anytime with the script
above - OCIDs go stale once deleted.

## Safety notes

- **Do NOT bulk-delete by type for live infrastructure**: `omc_mgmt_agent`
  (Management Agent - these are live agents), `omc_host_linux`/`omc_host_windows`,
  `oci_load_balancer`, `oci_compute_instance`, cluster/DB entities. Target only the
  ephemeral churn types (VNIC, Kubernetes pod/endpoint/etc.).
- **Age is high-confidence, not proof.** For 100% certainty an entity is dead, verify
  the underlying resource is gone: the VNIC entity name carries the parent OCID
  (`ocid1.loadbalancer...`, `ocid1.cluster...`, `ocid1.fnapp...`); `oci <service> get`
  returning `NotAuthorizedOrNotFound` means deleted (assuming you have read access).
- **Reappearance is a safety net.** Deleting a still-live ephemeral entity is harmless -
  LA recreates it on the next log push. So dead ones stay gone; live ones come back.
- **Run as your user, not `sudo`** - the deletes use your `~/.oci/config` profile.
- Deletion is done by you; this tool only reads and generates the script.
