# Customization Guide

This guide explains how to customize the FinOps solution for your specific needs.

## Customizing Queries

### Available Fields

The FOCUS parser extracts these fields from cost reports:

| Field | Type | Description |
|-------|------|-------------|
| `oci_AttributedCost` | Number | Cost attributed to the resource |
| `oci_CostOverage` | Number | Amount exceeding budget |
| `oci_CompartmentName` | String | Compartment name |
| `oci_CompartmentPath` | String | Full compartment path |
| `ServiceName` | String | OCI service name |
| `ResourceId` | String | Resource OCID |
| `ResourceName` | String | Resource display name |
| `UsageQuantity` | Number | Usage amount |
| `ChargeType` | String | Usage, Purchase, Tax, etc. |
| `CommitmentDiscountType` | String | Type of commitment discount |
| `subAccountName` | String | Sub-account/tenancy name |
| `skuID` | String | SKU identifier |
| `Tag - *` | String | Freeform and defined tags |

### Query Examples

#### Cost by Custom Tag
```sql
'Log Source' = FOCUS_OCI
| eval CostCenter = if(isNull('Tag - CostCenter'), 'Untagged', 'Tag - CostCenter')
| stats sum(oci_AttributedCost) as Cost by CostCenter
| sort -Cost
```

#### Daily Cost with Moving Average
```sql
'Log Source' = FOCUS_OCI
| timestats span=1day sum(oci_AttributedCost) as DailyCost
| eventstats avg(DailyCost) as AvgCost
| fields Time, DailyCost, AvgCost
```

#### Resources Over Cost Threshold
```sql
'Log Source' = FOCUS_OCI
| stats sum(oci_AttributedCost) as Cost by ResourceId, ResourceName, ServiceName
| where Cost > 100
| sort -Cost
| head 50
```

#### Cost Anomaly Detection (> 2 Std Dev)
```sql
'Log Source' = FOCUS_OCI
| timestats span=1day sum(oci_AttributedCost) as DailyCost
| eventstats avg(DailyCost) as Mean, stddev(DailyCost) as StdDev
| eval UpperBound = Mean + (2 * StdDev)
| eval IsAnomaly = if(DailyCost > UpperBound, 'Yes', 'No')
| where IsAnomaly = 'Yes'
```

#### Month-over-Month Comparison
```sql
'Log Source' = FOCUS_OCI
| eval Month = formatDate(Time, 'yyyy-MM')
| stats sum(oci_AttributedCost) as Cost by Month
| sort Month
| eval PrevMonthCost = lag(Cost)
| eval ChangePercent = round(((Cost - PrevMonthCost) / PrevMonthCost) * 100, 1)
```

## Customizing Dashboards

### Adding Widgets

1. Open a dashboard in **Management Dashboards**
2. Click **Edit Dashboard**
3. Click **Add Widget**
4. Select visualization type
5. Enter your query
6. Configure display options
7. Save

### Widget Types

| Type | Best For |
|------|----------|
| `tile` | Single metric (total cost, count) |
| `pie` | Proportional breakdown |
| `hbar` / `vbar` | Comparisons, rankings |
| `line` | Trends over time |
| `records_histogram` | Time-series with grouping |
| `table` | Detailed data exploration |
| `cloud` | Tag clouds, word prominence |
| `treemap` | Hierarchical data |

### Creating New Dashboards

1. Navigate to **Management Dashboards**
2. Click **Create Dashboard**
3. Add widgets with your custom queries
4. Arrange layout
5. Save

### Exporting Dashboards

To share or backup:

```bash
oci management-dashboard dashboard export \
  --dashboard-id <dashboard-ocid> \
  > my-dashboard.json
```

## Customizing Alerts

### Creating Detection Rules

1. Navigate to **Log Analytics** > **Administration** > **Detection Rules**
2. Click **Create**
3. Configure:
   - **Query**: Your cost threshold query
   - **Metric Namespace**: Custom (e.g., `finops_metrics`)
   - **Metric Name**: e.g., `daily_overage`
4. Save

Example query for overage detection:
```sql
'Log Source' = FOCUS_OCI
| stats sum(oci_CostOverage) as TotalOverage
| where TotalOverage > 0
```

### Creating Alarms

1. Navigate to **Observability & Management** > **Monitoring** > **Alarm Definitions**
2. Click **Create Alarm**
3. Configure:
   - **Metric**: Your detection rule metric
   - **Threshold**: Value that triggers alarm
   - **Notification Topic**: Where to send alerts
4. Save

### Notification Topics

Create topics for different alert types:

```bash
# Create topic
oci ons topic create \
  --name "finops-alerts" \
  --compartment-id <compartment-ocid>

# Create email subscription
oci ons subscription create \
  --topic-id <topic-ocid> \
  --protocol EMAIL \
  --subscription-endpoint "finops-team@example.com"
```

## Customizing the Function

### Changing Lookback Period

Edit the function configuration in OCI Console or Terraform:

```bash
# Via OCI CLI
oci fn function update \
  --function-id <function-ocid> \
  --config '{"LOOKBACK_DAYS": "7"}'
```

### Adding Custom Processing

Modify `function/func.py` to add custom logic:

```python
def process_day(self, source_tenancy: str, target_date: datetime) -> int:
    # ... existing code ...

    for obj in objects.data.objects:
        # Add custom filtering
        if self.should_skip_file(obj.name):
            continue

        # Add custom transformation
        content = self.transform_content(obj.data)

        # ... rest of processing ...
```

### Changing Schedule

Update the function schedule:

1. Navigate to your function
2. Go to **Schedules** tab
3. Edit or create schedule with new cron expression

Common schedules:
- `0 6 * * *` - Daily at 6 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Weekly on Monday

## Customizing Tags

### Adding Tag-Based Dashboards

1. Identify your organization's tagging strategy
2. Create queries using your tag names:
   ```sql
   'Log Source' = FOCUS_OCI
   | stats sum(oci_AttributedCost) by 'Tag - YourTagName'
   ```
3. Create dashboard widgets

### Enforcing Tagging

Track untagged resource costs:

```sql
'Log Source' = FOCUS_OCI
| where isNull('Tag - Team') and isNull('Tag - Project')
| stats sum(oci_AttributedCost) as UntaggedCost by ServiceName, oci_CompartmentName
| sort -UntaggedCost
```

## Multi-Tenancy Customization

### Sub-Account Analysis

If managing multiple tenancies:

```sql
'Log Source' = FOCUS_OCI
| stats sum(oci_AttributedCost) as Cost by subAccountName
| sort -Cost
```

### Compartment Hierarchy

Navigate compartment paths:

```sql
'Log Source' = FOCUS_OCI
| eval RootCompartment = split(oci_CompartmentPath, '/')[0]
| stats sum(oci_AttributedCost) as Cost by RootCompartment
```

## Best Practices

1. **Test Queries First**: Use Log Explorer before adding to dashboards
2. **Limit Data Scope**: Use time filters to improve performance
3. **Name Clearly**: Use descriptive names for dashboards and widgets
4. **Document Changes**: Keep notes on custom queries and their purpose
5. **Version Control**: Export dashboards to JSON and track in git
