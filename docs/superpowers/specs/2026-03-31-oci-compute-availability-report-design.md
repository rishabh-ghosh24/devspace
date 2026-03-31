# OCI Compute Availability Report — Design Spec

**Author:** Rishabh Ghosh, Technical Program Manager — OCI O&M
**Status:** Draft
**Version:** 1.0
**Date:** 2026-03-31

---

## 1. Problem

MSP and partner organizations on OCI need to prove compute instance uptime to their customers for SLA-based contractual payments. No OCI-native solution exists today. Competitors offer this out of the box.

Existing OCI capabilities fall short:
- **`instance_status` metric** — inverted values (0=up, 1=down), VM-only, no direct availability percentage
- **OCI Monitoring Metrics Explorer** — can chart metrics but cannot compute availability percentages or generate exportable reports
- **OCI Log Analytics dashboards** — limited visualization types, no heatmap, no conditional formatting
- **OCI Stack Monitoring** — tracks resource status but lacks formal SLA reporting and export

---

## 2. Target users

**Primary:** MSP/partner operations teams generating availability reports for end customers to prove SLA compliance and trigger contractual payments.

**Secondary:** Enterprise IT operations teams running internal SLA tracking, and OCI presales engineers demonstrating OCI-native availability reporting.

---

## 3. Solution overview

A single-file Python CLI tool distributed as a standalone GitHub repository. It:

1. Discovers VM instances across a compartment tree (recursive sub-compartment scanning)
2. Queries two OCI Monitoring metrics as availability signals
3. Computes per-instance, per-compartment, and fleet-level availability percentages
4. Generates a self-contained HTML report (Chart.js embedded inline, no CDN dependency)
5. Optionally uploads the report to OCI Object Storage with a shareable PAR link

### v1 scope

- **VM compute instances only** (BM instances, databases, load balancers, and other resource types are v2)
- **Single region per run** (multi-region is v2)
- **HTML output only** (automated PDF generation is v2)

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Monitoring VM / Local Machine                   │
│         (Instance Principals / OCI Config File)              │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         compute_availability_report.py                 │ │
│  │                                                        │ │
│  │  Phase 1: DISCOVER                                     │ │
│  │    ├─ Identity API → resolve compartment name          │ │
│  │    ├─ Identity API → list sub-compartments (recursive) │ │
│  │    └─ Compute API  → list VM instances per compartment │ │
│  │         (exclude TERMINATED, optionally STOPPED)       │ │
│  │                                                        │ │
│  │  Phase 2: COLLECT (2 API calls, batched if needed)     │ │
│  │    ├─ Monitoring API → CpuUtilization (all instances)  │ │
│  │    │   namespace: oci_computeagent                     │ │
│  │    └─ Monitoring API → instance_status (all instances) │ │
│  │        namespace: oci_compute_infrastructure_health    │ │
│  │                                                        │ │
│  │  Phase 3: COMPUTE                                      │ │
│  │    ├─ Match metrics to instances by resourceId         │ │
│  │    ├─ Classify each hour: UP / DOWN / STOPPED          │ │
│  │    ├─ Per-instance availability %                      │ │
│  │    ├─ Per-compartment summary                          │ │
│  │    └─ Fleet-level summary                              │ │
│  │                                                        │ │
│  │  Phase 4: RENDER                                       │ │
│  │    ├─ Generate self-contained HTML                     │ │
│  │    │   (Chart.js embedded inline, no CDN)              │ │
│  │    └─ Optional: upload to Object Storage + PAR link    │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│           availability_report_<name>_<date>.html             │
└──────────────────────────────────────────────────────────────┘
```

### Why two metrics

| Metric | Namespace | What it tells us | Emission behavior |
|--------|-----------|------------------|-------------------|
| `CpuUtilization` | `oci_computeagent` | Instance is running (agent emitting data) | Every minute while running; no data when stopped |
| `instance_status` | `oci_compute_infrastructure_health` | Infrastructure is healthy (0) or degraded (1) | Every ~5-8 min while running; no data when stopped |

`CpuUtilization` alone cannot distinguish "stopped by customer" from "down due to infra issue" — both produce no data. Adding `instance_status` resolves this: if `instance_status` reports 1 (unhealthy), it's a confirmed infrastructure issue. If neither metric has data, the instance was stopped.

### Metrics NOT used (and why)

| Metric | Namespace | Why excluded |
|--------|-----------|--------------|
| `instance_accessibility_status` | `oci_compute_instance_health` | Measures network reachability (ARP ping). Catches OS-level issues (crashed network stack, firewall misconfiguration) which are customer responsibility, not OCI infrastructure problems. Including it would create false negatives. |
| `instance_file_system_status` | `oci_compute_instance_health` | Detects filesystem anomalies. Same rationale — customer-side issue, not infrastructure availability. |
| `health_status` | `oci_compute_infrastructure_health` | BM-only. v1 is VM-only. Will be used in v2 for bare metal instances. |

---

## 5. Availability classification

For each hourly bucket, classify the instance's status using both metrics:

```
if CpuUtilization data exists:
    if instance_status == 1:        → DOWN   (running but infra degraded)
    else:                           → UP     (healthy)
elif instance_status == 0:          → UP     (infra healthy, agent issue)
elif instance_status == 1:          → DOWN   (infra issue, no CPU data)
else (no data from either metric):  → STOPPED (exclude from denominator)
```

### Classification truth table

| CpuUtilization | instance_status | Classification | Rationale |
|----------------|-----------------|----------------|-----------|
| Has data | 0 (healthy) | **UP** | Running and healthy — best signal |
| Has data | 1 (unhealthy) | **DOWN** | Running but infra degraded |
| Has data | no data | **UP** | Agent running, status not reported (rare) |
| No data | 0 (healthy) | **UP** | Infra healthy, agent disabled/issue |
| No data | 1 (unhealthy) | **DOWN** | Infra issue confirmed |
| No data | no data | **STOPPED** | Excluded from denominator |

### Availability formula

```
per-instance:  availability % = up_hours / (up_hours + down_hours) × 100
per-compartment: sum(up_hours in compartment) / sum(monitored_hours in compartment) × 100
fleet-level:   availability % = sum(all_up_hours) / sum(all_up_hours + all_down_hours) × 100
```

- STOPPED hours are excluded from both numerator and denominator
- Division by zero (all hours STOPPED) → display as "N/A"
- Availability rounded to 2 decimal places

---

## 6. Functional requirements

### 6.1 Authentication

| ID | Requirement |
|----|-------------|
| AUTH-1 | Support Instance Principals (default, for VMs with dynamic group policies) |
| AUTH-2 | Support OCI config file (`~/.oci/config`) with configurable profile |
| AUTH-3 | CLI flag: `--auth {instance_principal, config}`, default `instance_principal` |
| AUTH-4 | CLI flag: `--profile <name>`, default `DEFAULT` (only with `--auth config`) |

### 6.2 Instance discovery

| ID | Requirement |
|----|-------------|
| DISC-1 | Accept compartment OCID via `--compartment-id` (required). Can be tenancy root OCID. |
| DISC-2 | Always scan sub-compartments recursively (`compartment_id_in_subtree=True`) |
| DISC-3 | Auto-detect compartment display name via Identity API; allow override with `--compartment-name` |
| DISC-4 | List all VM compute instances using Compute `ListInstances` API |
| DISC-5 | Exclude TERMINATED instances always |
| DISC-6 | By default, include only RUNNING instances (checked at query time). `--include-stopped` flag includes STOPPED and other lifecycle states. Note: an instance that was RUNNING during the reporting period but is now STOPPED will be excluded unless `--include-stopped` is set. |
| DISC-7 | Collect per-instance metadata: display name, OCID, lifecycle state, shape, availability domain, fault domain, region, compartment name |
| DISC-8 | Group instances by compartment for report output |

### 6.3 Availability data collection

| ID | Requirement |
|----|-------------|
| DATA-1 | Query `CpuUtilization` from `oci_computeagent` namespace via `SummarizeMetricsData` API |
| DATA-2 | Query `instance_status` from `oci_compute_infrastructure_health` namespace via `SummarizeMetricsData` API |
| DATA-3 | Use 1-hour resolution with `max()` statistic for both metrics |
| DATA-4 | Query window: current time minus `--days` (default 7, allowed: 7, 14, 30, 60, 90) |
| DATA-5 | Maximum lookback: 90 days (OCI Monitoring hourly retention limit) |
| DATA-6 | Query all instances in a single API call per metric (no resourceId filter), using compartment subtree scanning |
| DATA-7 | Match returned metric streams to instances by `resourceId` dimension client-side |
| DATA-8 | **API batching**: if expected data points (instances × hours) exceeds 80,000, split into batched queries by instance groups to stay under the 100,000 data point per-call API limit |
| DATA-9 | Handle API errors gracefully — log warning, mark affected hours as "nodata" |

### 6.4 Availability computation

| ID | Requirement |
|----|-------------|
| COMP-1 | Divide the reporting period into 1-hour buckets |
| COMP-2 | For each instance, for each hourly bucket: classify as UP, DOWN, or STOPPED per the classification truth table |
| COMP-3 | Per-instance availability % = `up_hours / (up_hours + down_hours) × 100`, rounded to 2 decimal places |
| COMP-4 | STOPPED hours excluded from both numerator and denominator |
| COMP-5 | Per-compartment availability % = weighted average across instances in compartment |
| COMP-6 | Fleet availability % = `sum(all_up_hours) / sum(all_up_hours + all_down_hours) × 100` |
| COMP-7 | Track per-instance: total hours, up hours, down hours, stopped hours, monitored hours (up+down), availability %, downtime minutes |
| COMP-8 | Track per-compartment: instance count, compartment availability %, instances meeting SLA target |
| COMP-9 | Track fleet-level: total instances, fleet availability %, count meeting SLA target, total up hours, total monitored hours |
| COMP-10 | SLA target configurable via `--sla-target` (default: 99.95) |
| COMP-11 | Division by zero (all hours STOPPED/nodata) → availability = "N/A" |

### 6.5 Report generation — HTML output

Self-contained HTML file. All CSS inline. Chart.js embedded inline (no CDN). Heatmap is pure HTML/CSS/JS.

#### 6.5.1 Report header

| ID | Requirement |
|----|-------------|
| RPT-1 | Title: "Compute availability report" |
| RPT-2 | Metadata bar: tenancy/compartment name, region, reporting period (start — end, N days), SLA target |
| RPT-3 | Optional branding area (top-right): custom title via `--title`, logo via `--logo` (embedded as base64) |

#### 6.5.2 Metric cards (top row, 4 cards)

| Card | Value | Color logic |
|------|-------|-------------|
| Fleet availability | `fleet_availability_pct%` | Green if >= SLA target, amber if >= 99%, red otherwise |
| Instances monitored | count | Neutral |
| Meeting SLA target | `at_target / total` | Green |
| Total uptime hours | `up_hours / monitored_hours` | Neutral |

#### 6.5.3 Executive summary section

| ID | Requirement |
|----|-------------|
| EXEC-1 | Donut chart (Chart.js doughnut, embedded) showing fleet availability vs unavailability, with percentage centered (24px font) |
| EXEC-2 | Per-instance table grouped by compartment |
| EXEC-3 | Each compartment group has a header row: compartment name, instance count, compartment availability % |
| EXEC-4 | Table columns: Instance, Status, Availability %, Uptime (hours centered above stacked bar), Downtime |
| EXEC-5 | Instances sorted worst-availability-first within each compartment |
| EXEC-6 | Status column shows lifecycle state as a centered colored badge (green = RUNNING, red = STOPPED, amber = other) |
| EXEC-7 | Availability column color-coded: green if >= SLA target, amber if >= 99%, red otherwise |
| EXEC-8 | Uptime column shows hours text centered above a mini horizontal stacked bar (green = up, red = down, gray = stopped) |

#### 6.5.4 Availability heatmap section

| ID | Requirement |
|----|-------------|
| HEAT-1 | Grouped by compartment (uppercase label above each group) |
| HEAT-2 | One row per instance within each compartment group |
| HEAT-3 | Each row shows: instance name (200px), availability % (52px), colored blocks |
| HEAT-4 | Adaptive block resolution based on `--days` value: |
|         | - 7 days: 1-hour blocks (168 blocks) |
|         | - 14 days: 4-hour blocks (84 blocks) |
|         | - 30 days: 6-hour blocks (120 blocks) |
|         | - 60 days: daily blocks (60 blocks) |
|         | - 90 days: daily blocks (90 blocks) |
| HEAT-5 | Block colors: green (#1D9E75) = available, red (#E24B4A) = unavailable, light gray (#E8E6DF) = no data/stopped |
| HEAT-6 | Hover tooltip: `{instance_name} — {date} {hour}:00 UTC — {status_label}` |
| HEAT-7 | Date markers above the heatmap |
| HEAT-8 | Legend below: Available, Unavailable, No data/stopped, block resolution note |
| HEAT-9 | At scale (>50 instances): show only instances below SLA target in heatmap by default. HTML toggle to show all. Full instance list always in summary table. |

#### 6.5.5 Footer

| ID | Requirement |
|----|-------------|
| FTR-1 | Generation timestamp (UTC) |
| FTR-2 | Version string: "OCI Compute Availability Report v1.0" |

#### 6.5.6 Print / PDF support

| ID | Requirement |
|----|-------------|
| PRNT-1 | `@media print` CSS rules for clean printing |
| PRNT-2 | White background, visible borders, hidden tooltips when printed |

### 6.6 Output and distribution

| ID | Requirement |
|----|-------------|
| OUT-1 | Default output: `availability_report_<compartment_name>_<YYYYMMDD>.html` in current directory |
| OUT-2 | Custom output path via `--output` flag |
| OUT-3 | Optional Object Storage upload via `--upload` flag |
| OUT-4 | Bucket name configurable via `--bucket` (default: `availability-reports`) |
| OUT-5 | Object Storage namespace auto-detected or overridden via `--os-namespace` |
| OUT-6 | On upload: create bucket if it doesn't exist, upload HTML with `content-type: text/html`, create PAR |
| OUT-7 | PAR expiry configurable via `--par-expiry-days` (default: 30) |
| OUT-8 | Print shareable PAR URL to stdout after upload |

---

## 7. CLI interface

```
compute_availability_report.py [OPTIONS]

Required:
  --compartment-id OCID         Target compartment (can be tenancy root OCID)

Authentication:
  --auth {instance_principal,config}  Auth method (default: instance_principal)
  --profile NAME                OCI config profile (default: DEFAULT)

Reporting:
  --days {7,14,30,60,90}        Reporting period (default: 7)
  --sla-target FLOAT            SLA target % (default: 99.95)
  --include-stopped             Include non-RUNNING instances
  --region REGION               OCI region override (default: from auth provider)

Branding:
  --title TEXT                  Custom report title (top-right header)
  --logo PATH                  Path to logo image (embedded as base64)

Output:
  --output PATH                 Output HTML file path
  --upload                      Upload to Object Storage
  --bucket NAME                 Bucket name (default: availability-reports)
  --os-namespace NS             Object Storage namespace
  --par-expiry-days INT         PAR link expiry in days (default: 30)
```

### Example commands

```bash
# Weekly report for a compartment subtree (Instance Principals auth)
python3 compute_availability_report.py \
  --compartment-id ocid1.compartment.oc1..aaaa...

# Tenancy-wide 30-day report with upload
python3 compute_availability_report.py \
  --compartment-id ocid1.tenancy.oc1..aaaa... \
  --days 30 \
  --upload --bucket sla-reports

# Config file auth, custom SLA, MSP branding
python3 compute_availability_report.py \
  --auth config --profile PROD \
  --compartment-id ocid1.compartment.oc1..aaaa... \
  --days 90 --sla-target 99.99 \
  --title "ACME Corp MSP" --logo /path/to/logo.png

# Custom output path, 90-day PAR
python3 compute_availability_report.py \
  --compartment-id ocid1.compartment.oc1..aaaa... \
  --days 30 --upload \
  --par-expiry-days 90
```

---

## 8. IAM prerequisites

### Dynamic group (for Instance Principals)

```
instance.id = '<MONITORING_VM_OCID>'
```

### IAM policies

```
Allow dynamic-group <DG_NAME> to read instances in compartment <COMPARTMENT>
Allow dynamic-group <DG_NAME> to read metrics in compartment <COMPARTMENT>
Allow dynamic-group <DG_NAME> to read compartments in tenancy

# Only required if using --upload:
Allow dynamic-group <DG_NAME> to manage objects in compartment <COMPARTMENT> where target.bucket.name='<BUCKET>'
Allow dynamic-group <DG_NAME> to manage buckets in compartment <COMPARTMENT> where target.bucket.name='<BUCKET>'
Allow dynamic-group <DG_NAME> to manage preauthenticated-requests in compartment <COMPARTMENT> where target.bucket.name='<BUCKET>'
```

---

## 9. HTML report design spec

### Color palette

| Purpose | Hex | Usage |
|---------|-----|-------|
| Available / green | #1D9E75 | Heatmap up blocks, status dots, badges |
| Unavailable / red | #E24B4A | Heatmap down blocks, alerts |
| No data / gray | #E8E6DF | Heatmap stopped blocks, neutral |
| Warning / amber | #EF9F27 | Degraded status |
| Text primary | #1A1A1A | Headings, values |
| Text secondary | #888780 | Labels, metadata |
| Text muted | #B4B2A9 | Hints, footer |
| Background | #F8F7F4 | Page body |
| Card background | #FFFFFF | Cards, tables |
| Card border | #E8E6DF | Card and table borders |

### Badge styles

| State | Background | Text color |
|-------|-----------|------------|
| RUNNING / OK | #E1F5EE | #085041 |
| WARNING / DEGRADED | #FAEEDA | #633806 |
| STOPPED / DOWN | #FCEBEB | #791F1F |

### Typography

- Font: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Page title: 22px, weight 600
- Section titles: 16px, weight 600, with bottom border
- Metric card values: 24px, weight 600
- Donut center value: 24px, weight 600
- Table headers: 11px, uppercase, weight 600, letter-spacing 0.5px
- Table body: 13px
- Heatmap labels: 13px, weight 500
- Footer: 12px, muted color

### Layout

- Max width: 960px, centered
- Padding: 32px vertical, 24px horizontal
- Metric cards: 4-column grid, 12px gap
- Executive summary: 180px donut column + fluid table column
- Table columns: Instance 28%, Status 14% (centered), Availability 14%, Uptime 30% (centered), Downtime 14%
- Heatmap rows: 200px label + 52px percentage + fluid block area
- Heatmap block gap: 1px, height: 24px

### Interactive elements

- Heatmap blocks: hover opacity (0.75) + floating tooltip
- Tooltip: fixed position, dark background (#2C2C2A), white text, 11px, 4px radius
- At scale (>50 instances): HTML toggle button to show/hide full heatmap

### Chart.js donut config

- Type: doughnut, embedded inline (not CDN)
- Cutout: 74%
- Colors: [#1D9E75, #E24B4A] (or [#1D9E75, #E8E6DF] if 0% unavailable)
- Border width: 0
- Animation: rotate, 600ms
- Legend: hidden (custom center text)

---

## 10. API considerations

### Data point limits

OCI `SummarizeMetricsData` returns a maximum of 100,000 data points per call. Expected data points per metric query:

| Report period | Hours | Max instances per call |
|---------------|-------|----------------------|
| 7 days | 168 | ~595 |
| 14 days | 336 | ~297 |
| 30 days | 720 | ~138 |
| 60 days | 1,440 | ~69 |
| 90 days | 2,160 | ~46 |

When expected data points exceed 80,000 (safety margin), the script must batch instances into groups and make multiple API calls per metric.

### OCI API calls summary

| Phase | API | Call pattern |
|-------|-----|-------------|
| Discover | `Identity.GetCompartment` | 1 call |
| Discover | `Identity.ListCompartments` (subtree) | 1 call |
| Discover | `Compute.ListInstances` | 1 call per compartment (paginated) |
| Collect | `Monitoring.SummarizeMetricsData` (CpuUtilization) | 1-N calls (batched if needed) |
| Collect | `Monitoring.SummarizeMetricsData` (instance_status) | 1-N calls (batched if needed) |
| Upload | `ObjectStorage.CreateBucket` | 1 call (if needed) |
| Upload | `ObjectStorage.PutObject` | 1 call |
| Upload | `ObjectStorage.CreatePreauthenticatedRequest` | 1 call |

---

## 11. Repository structure

```
oci-compute-availability-report/
├── README.md                           # Setup, usage, examples
├── compute_availability_report.py      # Main script (single file)
├── examples/
│   └── sample_report.html              # Pre-generated sample with mock data
├── iam/
│   ├── dynamic_group.tf                # Terraform for dynamic group
│   └── policies.tf                     # Terraform for IAM policies
├── tests/
│   ├── test_availability.py            # Unit tests for computation logic
│   └── test_report.py                  # Unit tests for HTML generation
└── LICENSE
```

---

## 12. Testing

### Unit tests

| Test | Description |
|------|-------------|
| `test_classify_up_cpu_and_status_healthy` | CpuUtilization + instance_status=0 → UP |
| `test_classify_down_cpu_but_status_unhealthy` | CpuUtilization + instance_status=1 → DOWN |
| `test_classify_down_no_cpu_status_unhealthy` | No CpuUtilization + instance_status=1 → DOWN |
| `test_classify_up_no_cpu_status_healthy` | No CpuUtilization + instance_status=0 → UP |
| `test_classify_stopped_no_data` | No data from either metric → STOPPED |
| `test_availability_all_up` | All hours UP → 100% |
| `test_availability_with_downtime` | Mix of UP and DOWN → correct percentage |
| `test_availability_all_stopped` | All hours STOPPED → N/A |
| `test_availability_stopped_excluded` | STOPPED hours excluded from denominator |
| `test_fleet_aggregation` | Multiple instances → weighted fleet average |
| `test_compartment_grouping` | Instances grouped correctly by compartment |
| `test_sla_target_comparison` | 99.95 target with 99.94 actual → not meeting target |
| `test_api_batching_calculation` | Correct batch sizing for large fleets |

### Integration tests

| Test | Description |
|------|-------------|
| `test_instance_principal_auth` | Authenticate with Instance Principals on target VM |
| `test_config_auth` | Authenticate with OCI config file |
| `test_list_instances_subtree` | Discover instances across compartment subtree |
| `test_query_cpu_metrics` | Query CpuUtilization for known running instances |
| `test_query_instance_status` | Query instance_status for known running instances |
| `test_html_generation` | Generate report and validate HTML structure |
| `test_object_storage_upload` | Upload report and verify PAR URL is accessible |

---

## 13. Limitations (v1)

1. **VM instances only** — BM instances use `health_status` (different metric). v2 scope.
2. **Maximum 90-day lookback** — OCI Monitoring retains hourly data for 90 days.
3. **Monitoring must be enabled** — instances without `oci_computeagent` show as "no data."
4. **Single region per run** — multi-region requires multiple runs. v2 scope.
5. **Heartbeat proxy** — measures "was the instance emitting data" + "was the infrastructure healthy." Won't detect rare degradation not flagged by `instance_status`.
6. **Embedded Chart.js** — increases HTML file size by ~200KB. Acceptable trade-off for full offline support.

---

## 14. Future enhancements (v2+)

| Enhancement | Priority |
|-------------|----------|
| BM instances (using `health_status` metric) | High |
| Database instances and other resource types | High |
| Automated PDF generation (`--pdf` flag) | High |
| Multi-region scanning in a single run | Medium |
| Email delivery (OCI Email Delivery / SMTP) | Medium |
| `instance_accessibility_status` as opt-in check | Low |
| Dark mode (`prefers-color-scheme`) | Low |
| Multi-compartment explicit selection (multiple `--compartment-id`) | Low |

---

## 15. Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Runtime |
| `oci` (OCI Python SDK) | Latest | API calls (Compute, Monitoring, Identity, Object Storage) |
| Chart.js | 4.4.x | Donut chart (embedded inline in HTML, not loaded from CDN) |

No other dependencies. Single file, no build step.

---

## 16. Success metrics

| Metric | Target |
|--------|--------|
| Time to first report | < 5 minutes from clone to generated report |
| Accuracy | Availability % matches OCI Console within ±0.1% |
| Report generation time | < 60 seconds for 50 instances over 30 days |
| Report file size | < 300KB for 50 instances / 30 days (including embedded Chart.js) |
| Customer adoption | Field-deployable in any OCI tenancy with standard permissions |
