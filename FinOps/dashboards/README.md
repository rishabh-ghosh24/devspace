# FinOps Dashboards

This directory contains pre-built Log Analytics dashboards for FinOps analysis.

## Available Dashboards

| Dashboard | Description |
|-----------|-------------|
| `finops-overview.json` | Main dashboard with overage, consumption, top compartments/services |
| `cost-by-tag.json` | Tag-based cost allocation (team, project, environment) |
| `reserved-capacity.json` | Commitment utilization and savings tracking |
| `cost-forecast.json` | Trend analysis and spend projections |

## Importing Dashboards

### Via OCI Console

1. Navigate to **Observability & Management** > **Management Dashboards**
2. Click **Import Dashboards**
3. Select the JSON file(s) you want to import
4. Choose your Log Group when prompted
5. Click **Import**

### Via OCI CLI

```bash
# Import a single dashboard
oci management-dashboard dashboard import \
  --from-json file://finops-overview.json

# Import all dashboards
for f in *.json; do
  oci management-dashboard dashboard import --from-json file://$f
done
```

## Customization

### Modifying Queries

Each dashboard uses Log Analytics queries against the `FOCUS_OCI` log source. Key fields available:

| Field | Description |
|-------|-------------|
| `oci_AttributedCost` | Attributed cost in your billing currency |
| `oci_CostOverage` | Amount over committed budget |
| `oci_CompartmentName` | OCI Compartment name |
| `ServiceName` | OCI service name (Compute, Storage, etc.) |
| `subAccountName` | Sub-account/tenancy name |
| `ResourceId` | Resource OCID |
| `ResourceName` | Resource display name |
| `UsageQuantity` | Usage amount |

### Adding Custom Widgets

1. Open the dashboard in Log Analytics
2. Click **Edit Dashboard**
3. Add a new widget with your custom query
4. Save the dashboard

Example query - Cost by environment tag:
```sql
'Log Source' = FOCUS_OCI
| stats sum(oci_AttributedCost) as Cost by 'Tag - Environment'
| sort -Cost
```

## Notes

- Dashboards are parameterized and should work in any tenancy
- You may need to adjust time ranges based on your data availability
- The FOCUS_OCI parser must be imported before dashboards will work
