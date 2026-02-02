# Architecture

This document explains the components and data flow of the OCI FinOps solution.

## Overview

The solution imports OCI FOCUS (FinOps Open Cost and Usage Specification) reports from Oracle's internal bucket into your tenancy for analysis in Log Analytics.

## Data Flow

```
1. Oracle generates FOCUS reports daily (with 24-72 hour delay)
           │
           ▼
2. OCI Function copies reports to your Object Storage bucket
           │
           ▼
3. Object Collection Rule detects new files via Streaming
           │
           ▼
4. Log Analytics ingests and parses the data
           │
           ▼
5. Dashboards and Alerts provide insights
```

## Components

### 1. FOCUS Reports (Source)

**Location**: Oracle-managed `bling` namespace
**Format**: CSV files organized by date
**Path**: `FOCUS Reports/{year}/{month}/{day}/`
**Update Frequency**: Daily
**Availability Delay**: 24-72 hours

FOCUS is the FinOps Open Cost and Usage Specification, a standard format that includes:
- Cost data (attributed cost, list price, effective cost)
- Usage quantities
- Service and resource identifiers
- Compartment hierarchy
- Tags (freeform and defined)

### 2. OCI Function (Report Copier)

**Purpose**: Copy FOCUS reports from Oracle's bucket to your bucket

**Key Features**:
- **Lookback Window**: Configurable (default: 5 days) to handle missed runs
- **Duplicate Detection**: Checks if file exists before copying
- **Path Preservation**: Maintains date folder structure
- **Error Handling**: Per-file error handling, continues on failure
- **Structured Logging**: Detailed logs for debugging

**Schedule**: Daily via OCI Function schedule (configurable)

**Environment Variables**:
```
LOOKBACK_DAYS=5          # Days to look back
DEST_NAMESPACE=<ns>      # Your Object Storage namespace
DEST_BUCKET=<bucket>     # Destination bucket
PRESERVE_PATH=true       # Keep folder structure
LOG_LEVEL=INFO           # Logging level
```

### 3. Object Storage Bucket

**Purpose**: Store FOCUS reports for ingestion

**Structure**:
```
finops-focus-reports/
├── FOCUS Reports/
│   └── 2025/
│       └── 01/
│           ├── 26/
│           │   └── report_26.csv
│           ├── 27/
│           │   └── report_27.csv
│           └── 28/
│               └── report_28.csv
```

**Lifecycle Policy**: Optional auto-delete after retention period (default: 365 days)

### 4. Streaming

**Purpose**: Real-time event notification for new files

When a new file is added to the bucket, an event is emitted to the stream. The Object Collection Rule consumes these events to trigger ingestion.

**Configuration**:
- 1 partition (sufficient for daily files)
- 24-hour retention

### 5. Log Analytics

**Components**:

#### Log Group
Container for the ingested FOCUS data. Provides:
- Access control (who can query)
- Data isolation
- Retention policies

#### Log Source (FOCUS_OCI)
Parser configuration that extracts fields from FOCUS CSV files:
- `oci_AttributedCost`: Cost attributed to the resource
- `oci_CostOverage`: Amount over budget
- `oci_CompartmentName`: Compartment name
- `ServiceName`: OCI service name
- `ResourceId`: Resource OCID
- `ResourceName`: Resource display name
- `UsageQuantity`: Usage amount
- Tag fields: `Tag - Team`, `Tag - Project`, etc.

#### Object Collection Rule
Automatically ingests new files from Object Storage:
- **Type**: LIVE (real-time)
- **Poll Since**: BEGINNING (process all existing files)
- **Source**: Object Storage bucket
- **Destination**: Log Group

### 6. Dashboards

Four pre-built dashboards for cost analysis:

| Dashboard | Purpose |
|-----------|---------|
| FinOps Overview | Executive summary, top spenders |
| Cost by Tag | Tag-based allocation and compliance |
| Reserved Capacity | Commitment utilization and savings |
| Cost Forecast | Trends, projections, anomalies |

### 7. IAM Policies

**Dynamic Groups**:

1. **Function Dynamic Group**: Matches OCI Functions in the compartment
   ```
   ALL {resource.type = 'fnfunc', resource.compartment.id = '<compartment>'}
   ```

2. **Log Analytics Dynamic Group**: Matches Object Collection Rules
   ```
   ALL {resource.type = 'loganalyticsobjectcollectionrule', resource.compartment.id = '<compartment>'}
   ```

**Policies**:

1. **Function Policy**: Read from usage-report tenancy, write to bucket
2. **Log Analytics Policy**: Read from bucket, use streaming

## Security Considerations

### Least Privilege

Each component has only the permissions it needs:
- Function can only read usage reports and write to one bucket
- Log Analytics can only read from that bucket
- No cross-compartment access unless explicitly configured

### Data Encryption

- Object Storage: Encrypted at rest (OCI-managed keys by default)
- Streaming: Encrypted in transit and at rest
- Log Analytics: Encrypted at rest

### Network

- Functions run in your VCN (private subnet recommended)
- No public endpoints required
- Outbound HTTPS only (to OCI services)

## Scaling Considerations

### Current Design

- **Single Region**: Deploys to one OCI region
- **Daily Processing**: Handles typical FOCUS report volumes
- **256MB Function Memory**: Sufficient for daily reports

### For Larger Deployments

If processing larger volumes:
1. Increase function memory (up to 1024MB)
2. Increase streaming partitions
3. Consider Log Analytics data limits

## Failure Handling

### Function Failures

- **Retry Logic**: Built-in per-file retry
- **Lookback Window**: Catches up on missed days
- **Alerting**: Configure OCI alarms on function errors

### Ingestion Failures

- **Object Collection Rule**: Retries on transient errors
- **Dead Letter**: Failed files remain in bucket for reprocessing

## Cost Estimation

Approximate monthly costs (varies by usage):

| Component | Estimated Cost |
|-----------|---------------|
| Object Storage | $0.02/GB |
| Functions | $0.20/million invocations |
| Streaming | $0.02/GB |
| Log Analytics | Varies by ingestion volume |

For most tenancies, expect < $10/month for the FinOps solution itself.
