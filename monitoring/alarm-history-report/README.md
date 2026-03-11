# OCI Alarm History Report

Exports alarm state transition history across all compartments in an OCI tenancy to CSV.

Useful for compliance audits, incident reviews, and understanding where alarm notifications are being delivered.

## What it does

1. Scans all compartments in the tenancy (or a specific subtree)
2. Lists every alarm definition
3. Retrieves up to 90 days of state transition history per alarm (OCI platform limit)
4. Resolves ONS topic names and subscription details (protocol, endpoint, state)
5. Exports everything to a timestamped CSV

The script is **strictly read-only** — no write, modify, or delete operations are performed.

## Prerequisites

- Python 3.6+
- OCI Python SDK: `pip install oci`
- **Instance Principals** (default): Run from an OCI compute instance with a dynamic group and matching IAM policies
- **Config file** (optional): Use `--use-config-file` when running from a local machine

### Required IAM Policies

```
Allow dynamic-group <your-dg> to inspect alarms in tenancy
Allow dynamic-group <your-dg> to read alarm-history in tenancy
Allow dynamic-group <your-dg> to read ons-topics in tenancy
Allow dynamic-group <your-dg> to read ons-subscriptions in tenancy
Allow dynamic-group <your-dg> to inspect compartments in tenancy
```

## Usage

```bash
# Default: instance principals, 90 days, full tenancy
python3 oci_alarm_history.py

# Last 60 days only
python3 oci_alarm_history.py --days 60

# Custom output filename
python3 oci_alarm_history.py --output audit_q1_2026.csv

# Scope to a specific compartment + its children
python3 oci_alarm_history.py --compartment-id ocid1.compartment.oc1..xxxxx

# Use config file auth (local machine / non-OCI environment)
python3 oci_alarm_history.py --use-config-file

# Config file with a named profile
python3 oci_alarm_history.py --use-config-file --profile PROD
```

## Command Options

| Flag | Description | Default |
|------|-------------|---------|
| `--days` | Number of days of history (max 90) | `90` |
| `--output` | Output CSV filename | `oci_alarm_history_YYYYMMDD_HHMMSS.csv` |
| `--compartment-id` | Scope to a compartment + children | Entire tenancy |
| `--use-config-file` | Use `~/.oci/config` instead of instance principals | Off |
| `--profile` | Config profile name (with `--use-config-file`) | `DEFAULT` |

## CSV Output Columns

| Column | Description |
|--------|-------------|
| `alarm_name` | Alarm display name |
| `alarm_id` | Alarm OCID |
| `severity` | CRITICAL, ERROR, WARNING, or INFO |
| `parsed_status` | Extracted state: FIRING, OK, RESET, SUSPENDED |
| `transition_summary` | Raw API text (e.g. "State transitioned from OK to Firing") |
| `timestamp` | When the history entry was recorded (UTC) |
| `timestamp_triggered` | When the state actually changed (~3 min before timestamp) |
| `alarm_compartment_path` | Full compartment path where the alarm definition lives |
| `alarm_compartment_id` | Compartment OCID of the alarm definition |
| `metric_target_path` | Compartment path of the monitored resource (see note below) |
| `metric_namespace` | OCI metric namespace (e.g. `oci_computeagent`) |
| `metric_query` | MQL alarm query expression |
| `is_enabled` | Whether the alarm is currently enabled |
| `lifecycle_state` | ACTIVE, DELETING, or DELETED |
| `notification_topic_names` | ONS topic display names |
| `notification_topic_ids` | ONS topic OCIDs |
| `notification_subscriptions` | Where alerts go: `PROTOCOL:endpoint(STATE)` per subscription |

### Note on `metric_target_path`

This can differ from `alarm_compartment_path`. OCI allows cross-compartment monitoring — a team can create an alarm in their compartment that watches metrics in another team's compartment. This is the `metric_compartment_id` field from the Alarm API and is standard OCI behavior.

## Example Output

```
Compartments scanned:    666
Total alarms found:      70
Alarms with history:     14
Total history entries:    13215
ONS topics resolved:     26
Time window:             90 days
CSV rows written:        13271
```

## Notes

- OCI retains alarm history for a maximum of **90 days** ([docs](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Tasks/get-alarm-history.htm))
- Alarms with no history in the selected window still appear in the CSV as `NO_HISTORY_IN_WINDOW` so auditors see the complete alarm inventory
- ONS topics that return 404 (deleted topics still referenced by alarms) are logged as `ACCESS_DENIED(404)` and handled gracefully
- The script includes rate limiting (0.15s inter-call delay + 429 backoff) to stay within OCI's 10 TPS monitoring limit