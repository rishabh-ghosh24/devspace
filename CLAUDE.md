# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains two OCI (Oracle Cloud Infrastructure) production tools:

1. **FinOps** (`/FinOps/`) — Ingests OCI FOCUS cost reports into Log Analytics for dashboards and alerting.
2. **Audit Log Masking** (`/logging/audit-log-masking/`) — OCI Function that redacts auth credentials from audit logs before forwarding to external SIEMs.

## Deployment Commands

### FinOps — Infrastructure (Terraform)
```bash
cd FinOps/terraform
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```
Copy `terraform.tfvars.example` to `terraform.tfvars` and fill in tenancy/compartment OCIDs before deploying.

### FinOps — Function
```bash
cd FinOps/function
fn use context <your-context>
fn deploy --app finops-prod-app
```

### Audit Log Masking — Function
```bash
cd logging/audit-log-masking
fn deploy
```

### Audit Log Masking — Verify masking
```bash
python3 logging/audit-log-masking/verify_masking.py --stream-id <stream-ocid>
python3 logging/audit-log-masking/verify_masking.py --stream-id <stream-ocid> --limit 10 --raw
```

## Architecture

### FinOps Data Flow
```
OCI FOCUS Reports (billing bucket)
  → OCI Function (focus-report-copier, runs daily at 6 AM UTC)
  → Object Storage (FOCUS reports bucket, 365-day lifecycle)
  → OCI Streaming (Kafka-compatible stream)
  → Log Analytics (collection rule)
  → Pre-built Dashboards & Alerts
```

The OCI Function (`FinOps/function/func.py`) uses a lookback window (default 5 days) to copy FOCUS CSV/Parquet reports. Infrastructure is fully modular Terraform under `FinOps/terraform/modules/`: `function`, `storage`, `streaming`, `iam`, `log-analytics`.

### Audit Log Masking Data Flow
```
OCI Audit Logs
  → Service Connector Hub (Function Task)
  → OCI Function (masking, logging/audit-log-masking/func.py)
  → OCI Streaming
  → External SIEM (Splunk, Sentinel, etc.)
```

The masking function (`logging/audit-log-masking/func.py`) redacts values for keys in `REDACT_KEYS` and values matching `SECRET_VALUE_PATTERNS` (OCI session tokens `ST$`, API signatures, Bearer/Basic auth headers). It preserves event structure and metadata, only nulling credential fields.

## Key Files

| File | Purpose |
|------|---------|
| `FinOps/function/func.py` | FOCUS report copy logic (277 lines) |
| `FinOps/terraform/variables.tf` | All configurable Terraform variables |
| `FinOps/terraform/terraform.tfvars.example` | Required configuration template |
| `logging/audit-log-masking/func.py` | Credential masking logic (194 lines) |
| `logging/audit-log-masking/verify_masking.py` | Stream verification utility (273 lines) |

## Tech Stack

- **Python 3.11** for OCI Functions; runtime via `fdk>=0.1.50`, OCI SDK `oci>=2.100.0`
- **Terraform >= 1.0.0** with OCI Provider >= 5.0.0 for infrastructure
- **Fn Project CLI** for function deployment
- Both functions use **resource principal authentication** — no API keys in code

## Important Patterns

- IAM uses least-privilege dynamic groups and policies (defined in `FinOps/terraform/modules/iam/main.tf`)
- Dashboards are JSON files importable via OCI Console (`FinOps/dashboards/`)
- Log Analytics parsers are pre-built ZIPs in `FinOps/parsers/`
- The masking function receives gzip-compressed JSON batches from Service Connector Hub and returns the same structure with credentials nulled
