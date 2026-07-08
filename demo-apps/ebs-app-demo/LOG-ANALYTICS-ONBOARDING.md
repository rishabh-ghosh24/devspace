# EBS -> OCI Logging Analytics Onboarding (`ebs-demo`)

Onboard all important logs from the single-node **Oracle E-Business Suite 12.2**
demo (`ebs-demo`) into **OCI Logging Analytics**, full stack (app tier + database +
host OS). The Management Agent already on the host (used by Stack Monitoring) is
reused - no second agent.

This doc is both the **runbook** and the **record of work done**, so we can later
verify what is already in place versus what remains.

- Date started: 2026-07-08
- Tenancy / region: `emdemo` / us-phoenix-1
- Author: Rishabh Ghosh
- Related design: [`docs/superpowers/specs/2026-06-04-ebs-stack-monitoring-demo-design.md`](../../docs/superpowers/specs/2026-06-04-ebs-stack-monitoring-demo-design.md) (the Stack Monitoring demo this layers on)

> Identifiers below are specific to the `emdemo` demo tenancy. Redact before
> publishing publicly. OCIDs are identifiers, not credentials.

---

## Status at a glance

| # | Step | Status | Verified |
|---|------|--------|----------|
| 0 | Log discovery (catalog every important EBS/OS log) | **DONE** | 2026-07-08 |
| A | App/DB/WLS/OHS log read access for `mgmt_agent` (ACLs) | **DONE** | 14/14 READ_OK |
| B | Host OS log read access for `mgmt_agent` (config) | **DONE** | 4/4, rotation + restart safe |
| C | Management Agent restart (pick up `adm` group) | **DONE** | live proc groups = adm,oinstall |
| 5 | Enable Logging Analytics plugin on the agent | DONE | LA plugin active (`mgmt_agent_logan.log` uploads) |
| 6 | IAM: agent dynamic group can submit discovery results | DONE (pre-existing) | `STACK_MONITORING_DISCOVERY_JOB_RESULT_SUBMIT` |
| 7 | Logging Analytics log group exists | DONE | `ocid1.loganalyticsloggroup.oc1.phx...z52u3r5a` |
| 8 | EBS entities + log-source associations created | **BLOCKED** | namespace at the 10,000 entity cap - see Blocker |
| 9 | Verify ingestion via MCP / Log Explorer | **BLOCKED** | only host OS logs flow today |

**Where we are:** host-side prerequisites (0, A, B, C) are complete and verified -
every EBS + OS log is readable by the agent. The EBS "Discover resources -> Log
Analytics only" wizard was run and **succeeded, but created zero Logging Analytics
entities** - the shared `emdemo` LA namespace is **at its 10,000 `entity-instances`
cap**, so the service silently cannot create the EBS entities. Only the pre-existing
host OS logs (syslog/secure/audit/cron) collect today.

## Blocker: `emdemo` namespace at the entity limit (diagnosed 2026-07-08)

The EBS discovery job reports `Succeeded`, but **no LA entities get created**, so
nothing collects beyond the host OS logs already onboarded on 2026-06-04.

**Root cause:** the shared `emdemo` LA namespace `axfo51x8x2ap` is **at its
`entity-instances` limit (10,000)**. A direct `oci log-analytics entity create`
returns `LimitExceeded {"limitName":"entity-instances","limit":10000}` - and that
error comes *after* authorization passes, so it is capacity, not permission. The
agent, host, log access, and the agent's discovery-result-submit grant are all
verified healthy; entity creation is a server-side step that silently hits the cap.
~74% of the namespace is uncleaned **ephemeral auto-created** entities (~3,470 VNICs,
mostly one live Functions app's per-invocation VNICs, plus ~3,900 Kubernetes pods)
with **no `AUTO_DELETE` preference set**, so it refills at ~300-400 entities/month.

**Fix (namespace admin, in order):** (1) enable
`AUTO_DELETE_SCH_ENTITIES_OF_TYPES=_ALL_` to stop the refill, (2) purge stale
ephemeral entities to get back under the cap, (3) request an `entity-instances`
limit increase for the immediate unblock. Then re-run the EBS discovery - every
other prerequisite is already in place. Tooling + full write-up:
[`tenancy-mgmt/logan-entity-cleanup/`](../../tenancy-mgmt/logan-entity-cleanup/).

---

## Environment

| Item | Value |
|------|-------|
| Host (SSH) | `ssh ebs-demo` -> `144.24.36.49`, user `opc`, key `~/.ssh/emdemo-common.key`, passwordless `sudo` |
| Host FQDN | `ebs-demo.sub05022315120.rishabhvcn.oraclevcn.com` |
| Topology | Single-node EBS 12.2 (Vision): DB + app tier co-located |
| DB | CDB `EBSCDB` (+ PDB), `ORACLE_HOME=/u01/install/APPS/19.0.0`, runs as OS user `oracle` |
| App tier | Run edition `fs1`; WebLogic (AdminServer, oacore/forms/oafm), OPMN + OHS web tier, Concurrent Managers; runs as `oracle` (apps user `applmgr`) |
| Management Agent | `ocid1.managementagent.oc1.phx.amaaaaaaqgp2kriaiacgevgxf5qj3dr5hgkpojgujywceuqcc7cwxzwodfwa`, runs as OS user `mgmt_agent` |
| Compartment | `LogAnalytics` = `ocid1.compartment.oc1..aaaaaaaa4yj2x6hjxntcf5vydrdvsm3trgblkmwgcmvxiar2miklv3ip4t7q` |
| LA namespace | `axfo51x8x2ap` |
| Stack Monitoring resource | `ebs-demo` (type `ebs_instance`), already discovered with full topology |

---

## The verified log catalog

Every path below was confirmed present and actively written on 2026-07-08 (host
clock). Path shorthand:

- `CONC` = `/u01/install/APPS/fs_ne/inst/EBSDB_apps/logs/appl/conc/log`
- `DOM`  = `/u01/install/APPS/fs1/FMW_Home/user_projects/domains/EBS_domain/servers`
- `OHS`  = `/u01/install/APPS/fs1/FMW_Home/webtier/instances/EBS_web_OHS1/diagnostics/logs`
- `DBTR` = `/u01/install/APPS/19.0.0/diag/rdbms/ebscdb/EBSCDB/trace`

| Tier / Stack Monitoring entity | Log file (glob) | OOB Logging Analytics source (display name) |
|---|---|---|
| **Concurrent Processing** `ebs-demo_ConcurrentProcessing*` | `CONC/EBSDB_*.mgr`, `CONC/i*.mgr` (internal) | `EBS Internal Concurrent Manager Logs` |
| | `CONC/w*.mgr` and other manager `*.mgr` | `EBS Concurrent Manager Logs` |
| | `CONC/l*.req` (per-request) | `EBS Concurrent Request Logs` |
| | conflict resolution manager `*.mgr` | `EBS Conflict Resolution Manager Logs` |
| | Output Post Processor (`FNDOPP*`) | `EBS Output Post Processor Logs` |
| | Transaction Manager | `EBS Transaction Manager Logs` |
| **Workflow** `ebs-demo_WorkflowSystem*` | `CONC/FNDCPGSC*.txt` (GSC: Mailer / Agent Listener) | `EBS Workflow Notification Mailer Logs` |
| **WebLogic** `ebs-demo_Domain_*` (AdminServer, oacore, forms, oafm) | `DOM/*/logs/*.log` (+ rotated `*.log0000N`) | `FMW WLS Server Logs` |
| | `DOM/oacore_server1/logs/access.log` | `FMW WLS Server Access Logs` |
| | `DOM/*/logs/*.out` | `FMW WLS Server STDOUT Logs` |
| | `DOM/*/logs/*-diagnostic.log` | `FMW WLS Server Diagnostic Logs` |
| **OHS / web tier** `ebs-demo-ohs` | `OHS/OHS/EBS_web/access_log` | `FMW OHS Access Logs (V11)` |
| | `OHS/OHS/EBS_web/EBS_web.log` (error) | `FMW OHS Error Logs` |
| | `OHS/OPMN/opmn/opmn.log` | `FMW OHS OPMN Logs (V11)` |
| **Database** `ebs-demo-db` / `-pdb` / `-dbsys` | `DBTR/alert_EBSCDB.log` | `Database Alert Logs` |
| | `/u01/install/APPS/19.0.0/rdbms/audit/*.aud` | `Database Audit Logs` |
| | DB listener (minimal in this env) | `Database Listener Alert Logs` / `Database Listener Trace Logs` |
| **Host OS** `ebs-demo-host` | `/var/log/messages` | `Linux Syslog Logs` |
| | `/var/log/secure` | `Linux Secure Logs` |
| | `/var/log/audit/audit.log` | `Linux Audit Logs` |
| | `/var/log/cron` | `Linux Cron Logs` |

**Exclusions (important):**

- **`/u01/install/APPS/fs_ne/inst/EBSDB_apps/logs/appl/conc/out` (51 GB)** - concurrent
  request *output*, not logs. Do NOT associate it; it would blow up ingestion cost.
- App-tier service-control logs (`.../fs1/inst/apps/EBSDB_apps/logs/appl/admin/log/ad*.txt`,
  `adstrtal.log`) - startup-only, low value. Skip unless troubleshooting startup.
- `adop` online-patching dir is empty (no patch cycles run). Add later if needed.

EBS 12.2 runs on FMW 11g (WLS 10.3.6, OHS 11g), which is why the web/WLS logs map to
the `FMW ... (V11)` sources rather than V12.

---

## Work completed

### Step 0 - Discovery (DONE)

SSH to the host and enumerated every important log across app/DB/host tiers,
resolving concurrent-log locations from the live EBS env
(`. /u01/install/APPS/EBSapps.env run`; `APPLCSF=/u01/install/APPS/fs_ne/inst/EBSDB_apps/logs/appl/conc`).
Result is the catalog table above.

### Step A - EBS/DB/WLS/OHS read access for `mgmt_agent` (DONE)

**Problem found (by testing, not guessing):** `mgmt_agent` is already in the
`oinstall` group and most EBS log *files* are `0644 oracle:oinstall`, but the
**parent directories were `0700 oracle`** (and `fs_ne` had no ACL at all), so the
agent could not traverse into them. Only the DB logs (under `19.0.0/...`) were
readable. A read test as `mgmt_agent` returned **2/18 READ_OK** before the fix.

**Fix:** POSIX ACLs scoped to `mgmt_agent` only - traverse (`--x`) down each
directory chain, read (`rX`) on the leaf log dirs, and a **default ACL** so rotated
files inherit read access. Nothing is loosened for other users.

Run as `root` on the EBS host (idempotent - safe to re-run, e.g. if EBS patching or
cloning resets permissions):

```bash
#!/usr/bin/env bash
# grant-mgmt-agent-log-access.sh - Part A: let mgmt_agent read EBS app/WLS/OHS logs.
set -euo pipefail
BASE=/u01/install/APPS
AGENT_USER=mgmt_agent

grant() {  # $1 = leaf log dir: traverse ancestors + read leaf + default ACL for new files
  local leaf="$1" rel d part
  [ -e "$leaf" ] || { echo "SKIP(missing) $leaf"; return; }
  rel="${leaf#$BASE/}"; d="$BASE"; setfacl -m u:${AGENT_USER}:--x "$d"
  IFS=/ read -ra P <<< "$(dirname "$rel")"
  for part in "${P[@]}"; do d="$d/$part"; setfacl -m u:${AGENT_USER}:--x "$d"; done
  setfacl -R -m u:${AGENT_USER}:rX "$leaf"
  setfacl -d -m u:${AGENT_USER}:rX "$leaf"
  echo "granted $leaf"
}

DOM=$BASE/fs1/FMW_Home/user_projects/domains/EBS_domain/servers
OHS=$BASE/fs1/FMW_Home/webtier/instances/EBS_web_OHS1/diagnostics/logs

grant $BASE/fs_ne/inst/EBSDB_apps/logs/appl/conc/log            # concurrent + workflow
for s in AdminServer oacore_server1 forms_server1 oafm_server1; do grant $DOM/$s/logs; done
grant $OHS/OHS/EBS_web                                          # OHS access + error
grant $OHS/OPMN/opmn                                            # OPMN
grant $BASE/fs1/inst/apps/EBSDB_apps/logs/ora/10.1.2/network    # apps/forms listener
# DB logs (alert/audit) already readable via oinstall - no action.
```

**Verification (re-run any time):**

```bash
# as root, read one byte of each live log AS the agent user
runuser -u mgmt_agent -- head -c1 /u01/install/APPS/fs_ne/inst/EBSDB_apps/logs/appl/conc/log/*.mgr >/dev/null && echo OK
```

Recorded result on 2026-07-08: **14/14 READ_OK, 0 blocked** (concurrent/workflow,
4x WebLogic, OHS access/error/OPMN, apps listener, DB alert + audit). Default ACL
confirmed on the leaf dirs (`default:user:mgmt_agent:r-x`) so rotated files inherit.

### Step B - Host OS log read access for `mgmt_agent` (DONE)

**Problem:** `/var/log/{messages,secure,cron,audit.log}` are `0600 root:root` - no
group access. A one-shot `chmod` would be undone by logrotate/auditd. Needs a
config-level, rotation- and restart-safe fix.

**Fix:** make the OS logs group-readable by `adm` and add `mgmt_agent` to `adm`.
Run as `root` (idempotent):

```bash
#!/usr/bin/env bash
# setup-os-log-perms.sh - Part B: let mgmt_agent read /var/log OS logs (survives rotation, restart, reboot).
set -euo pipefail
usermod -aG adm mgmt_agent

# rsyslog: create syslog files 0640 root:adm (dropin loads before RULES on OL8)
cat >/etc/rsyslog.d/00-loganalytics-perms.conf <<'CONF'
# OCI Logging Analytics: allow mgmt_agent (adm group) to read syslog files
$FileCreateMode 0640
$FileGroup adm
CONF

# logrotate: recreate rotated syslog files deterministically as 0640 root:adm
grep -q 'create 0640 root adm' /etc/logrotate.d/syslog \
  || sed -i '/^{$/a\    create 0640 root adm' /etc/logrotate.d/syslog

# auditd: group-readable audit.log across restarts and auditd self-rotation
sed -i 's/^log_group.*/log_group = adm/' /etc/audit/auditd.conf

# fix current files, then apply
chgrp adm /var/log/messages /var/log/secure /var/log/cron /var/log/audit/audit.log
chmod 0640 /var/log/messages /var/log/secure /var/log/cron /var/log/audit/audit.log
systemctl restart rsyslog
service auditd restart 2>/dev/null || systemctl kill -s HUP auditd.service
```

**Verification (proven on 2026-07-08):** all four files `0640 root:adm` and READ_OK
as `mgmt_agent` - immediately, after a forced `logrotate -f /etc/logrotate.d/syslog`
+ `service auditd rotate`, and after a `systemctl restart rsyslog` + `service auditd
restart`. All changes are on-disk config, so they also survive reboot.

### Step C - Management Agent restart (DONE)

Adding `mgmt_agent` to `adm` only affects new processes, so the running agent daemon
was restarted to pick up the group:

```bash
systemctl restart mgmt_agent
```

**Verification (2026-07-08):** the live agent Java process supplementary groups went
from `983(mgmt_agent) 54321(oinstall)` to `4(adm) 983(mgmt_agent) 54321(oinstall)`;
`mgmt_agent.service` is `active (running)` and the agent log shows "Bootstrapping was
completed successfully". The daemon now has OS-level read access to all 18/18 sources.

---

## Remaining onboarding steps

### Step 5 - Enable the Logging Analytics plugin on the agent

The agent currently runs the Stack Monitoring plugin; it also needs the **Logging
Analytics** plugin. Console: Observability & Management -> Management Agents ->
`ebs-demo` agent -> **Deploy plugins** -> check **Logging Analytics** -> Update. The
agent redeploys the plugin (no separate install). Confirm the plugin shows
`Deployed`.

### Step 6 - IAM policy (agent -> Logging Analytics)

The Management Agent's dynamic group needs permission to upload to Logging Analytics
in the compartment. Add (adjust the dynamic-group name to the existing one used for
this agent):

```
Allow dynamic-group <mgmt-agent-dg> to use loganalytics-log-group in compartment LogAnalytics
Allow dynamic-group <mgmt-agent-dg> to {LOG_ANALYTICS_LOG_GROUP_UPLOAD_LOGS} in compartment LogAnalytics
```

The Stack Monitoring policies do not cover Logging Analytics, so this is additive.

### Step 7 - Create the Logging Analytics log group

Console: Logging Analytics -> Administration -> Log Groups -> Create. Name
`EBS-Logs`, compartment `LogAnalytics`. This is the container the associations write
to.

### Step 8 - Associate log sources to the EBS entities (guided console)

Logging Analytics -> Administration -> **Sources** / or the **Add Data** wizard.
Because Stack Monitoring already discovered the EBS topology, the same entities are
reused for association. Associate, on the `ebs-demo` agent, the sources from the
[catalog table](#the-verified-log-catalog) to their entities:

- **EBS instance / Concurrent Processing / Workflow entities:** the seven `EBS ...`
  sources (Internal/standard Concurrent Manager, Concurrent Request, Conflict
  Resolution Manager, Output Post Processor, Transaction Manager, Workflow
  Notification Mailer).
- **WebLogic entities** (`ebs-demo_Domain_*`): `FMW WLS Server Logs`, `FMW WLS Server
  Access Logs`, `FMW WLS Server STDOUT Logs`, `FMW WLS Server Diagnostic Logs`.
- **OHS entity** (`ebs-demo-ohs`): `FMW OHS Access Logs (V11)`, `FMW OHS Error Logs`,
  `FMW OHS OPMN Logs (V11)`.
- **Database entity** (`ebs-demo-db` / `-pdb`): `Database Alert Logs`, `Database Audit
  Logs`, (optionally the Listener sources).
- **Host entity** (`ebs-demo-host`): `Linux Syslog Logs`, `Linux Secure Logs`, `Linux
  Audit Logs`, `Linux Cron Logs`.

Check each source's file path matches this deployment (the shorthand paths above); the
OOB defaults assume standard EBS/FMW layout and generally match. **Do not** point any
source at the 51 GB `conc/out` directory.

### Step 9 - Verify ingestion

Allow ~10-15 minutes after association, then confirm each tier is flowing. Via the
`emdemo-logan` MCP (compartment is already `LogAnalytics`) or Log Explorer:

```
# which sources are ingesting, last hour
* | stats count as logrecords by 'Log Source' | sort -logrecords

# scope to this host/entity
'Host Name (Server)' = 'ebs-demo.sub05022315120.rishabhvcn.oraclevcn.com'
  | stats count by 'Log Source'
```

Success = each expected source returns non-zero rows. Any expected source with **zero
rows** = an association or file-path/permission issue to fix (re-check Step A/B for
that path, and the source's configured file pattern).

---

## Rollback / teardown

- **Part A (ACLs):** remove the agent's ACL entries -
  `setfacl -R -x u:mgmt_agent <leaf dirs>` and `setfacl -k <leaf dirs>` to drop the
  default ACLs; remove the `--x` traverse entries on the ancestor dirs if desired.
- **Part B (OS logs):** delete `/etc/rsyslog.d/00-loganalytics-perms.conf`, revert the
  `create 0640 root adm` line in `/etc/logrotate.d/syslog`, set `log_group = root` in
  `/etc/audit/auditd.conf`, `gpasswd -d mgmt_agent adm`, restart rsyslog + auditd.
- **LA config:** delete the source associations, the `EBS-Logs` log group, and the IAM
  policy; disable the Logging Analytics plugin on the agent.

Stopping ingestion does not remove already-ingested data (subject to the log group's
retention).
