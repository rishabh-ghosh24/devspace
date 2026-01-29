# OCI FinOps Solution

A production-ready solution for importing OCI FOCUS (FinOps Open Cost and Usage Specification) reports into Log Analytics for advanced cost analysis, dashboards, and alerting.

## Features

- **One-Click Deployment**: Terraform-based infrastructure as code
- **Automated Data Ingestion**: Daily scheduled function copies FOCUS reports
- **Lookback Recovery**: Configurable lookback window (default: 5 days) ensures no data loss
- **Pre-Built Dashboards**: 4 comprehensive dashboards for cost analysis
- **Anomaly Detection**: Identify cost spikes and trends
- **Tag-Based Allocation**: Track costs by team, project, environment

## Quick Start

### Prerequisites

- OCI CLI configured with appropriate permissions
- Terraform >= 1.0.0
- An OCI compartment for deployment

### Deploy with Terraform

```bash
# Clone and navigate
cd FinOps/terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your tenancy details

# Deploy
terraform init
terraform plan
terraform apply
```

### Deploy the Function

After Terraform completes:

```bash
cd ../function
fn use context <your-context>
fn deploy --app finops-prod-app
```

### Import Dashboards

1. Navigate to **Observability & Management** > **Management Dashboards**
2. Click **Import Dashboards**
3. Import JSON files from the `dashboards/` directory

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Oracle Internal                                │
│  ┌─────────────────┐                                                    │
│  │  FOCUS Reports  │  (Cost & Usage data, updated daily)                │
│  │  (bling bucket) │                                                    │
│  └────────┬────────┘                                                    │
└───────────┼─────────────────────────────────────────────────────────────┘
            │
            ▼  (Daily scheduled function)
┌─────────────────────────────────────────────────────────────────────────┐
│                          Your OCI Tenancy                                │
│                                                                          │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │   OCI Function  │────▶│  Object Storage │────▶│    Streaming    │   │
│  │ (Report Copier) │     │ (FOCUS Reports) │     │                 │   │
│  └─────────────────┘     └─────────────────┘     └────────┬────────┘   │
│                                                           │             │
│                                                           ▼             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐   │
│  │    Dashboards   │◀────│  Log Analytics  │◀────│ Object Collect  │   │
│  │    & Alerts     │     │   (Querying)    │     │     Rule        │   │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Dashboards

| Dashboard | Description |
|-----------|-------------|
| **FinOps Overview** | Total spend, overage, consumption trends, top compartments/services |
| **Cost by Tag** | Tag-based cost allocation (team, project, environment) |
| **Reserved Capacity** | Commitment utilization, savings vs on-demand |
| **Cost Forecast** | Trend analysis, projections, anomaly detection |

## Configuration

### Function Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOOKBACK_DAYS` | 5 | Days to look back for reports |
| `DEST_NAMESPACE` | (required) | Your Object Storage namespace |
| `DEST_BUCKET` | finops-focus-reports | Destination bucket name |
| `PRESERVE_PATH` | true | Keep date folder structure |
| `LOG_LEVEL` | INFO | Logging verbosity |

### Terraform Variables

See `terraform/terraform.tfvars.example` for all configurable options including:
- Bucket retention policies
- Function schedule (cron)
- Alert thresholds
- Resource tagging

## Directory Structure

```
FinOps/
├── README.md                 # This file
├── ATTRIBUTION.md            # Original source credits
├── docs/                     # Detailed documentation
│   ├── prerequisites.md
│   ├── architecture.md
│   ├── manual-setup.md
│   ├── customization.md
│   └── troubleshooting.md
├── terraform/                # Infrastructure as code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
├── function/                 # FOCUS report copier function
│   ├── func.py
│   ├── func.yaml
│   └── requirements.txt
├── dashboards/               # Log Analytics dashboards
│   ├── finops-overview.json
│   ├── cost-by-tag.json
│   ├── reserved-capacity.json
│   └── cost-forecast.json
├── parsers/                  # Log Analytics parser
│   └── FOCUS_OCI_*.zip
└── images/                   # Documentation images
```

## Documentation

- [Prerequisites](docs/prerequisites.md) - What you need before starting
- [Architecture](docs/architecture.md) - Detailed component explanation
- [Manual Setup](docs/manual-setup.md) - Step-by-step without Terraform
- [Customization](docs/customization.md) - Modify queries and dashboards
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Credits

Based on content from [oracle-quickstart/oci-o11y-solutions](https://github.com/oracle-quickstart/oci-o11y-solutions) under the UPL-1.0 license. See [ATTRIBUTION.md](ATTRIBUTION.md) for details.

## License

Universal Permissive License v1.0 (UPL-1.0)
