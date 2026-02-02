# Manual Setup Guide

This guide walks through deploying the FinOps solution without Terraform. Use this if you prefer manual control or cannot use Terraform in your environment.

## Step 1: Create Object Storage Bucket

1. Navigate to **Storage** > **Object Storage** > **Buckets**
2. Click **Create Bucket**
3. Configure:
   - **Name**: `finops-focus-reports`
   - **Default Storage Tier**: Standard
   - **Encryption**: Oracle-managed keys (default)
   - **Versioning**: Disabled
4. Click **Create**

Note your bucket namespace (shown at top of bucket details page).

## Step 2: Create Dynamic Groups

Navigate to **Identity & Security** > **Dynamic Groups**

### Function Dynamic Group

1. Click **Create Dynamic Group**
2. Configure:
   - **Name**: `finops-function-dg`
   - **Description**: Dynamic group for FinOps FOCUS report copier function
   - **Matching Rule**:
     ```
     ALL {resource.type = 'fnfunc', resource.compartment.id = '<your-compartment-ocid>'}
     ```
3. Click **Create**

### Log Analytics Dynamic Group

1. Click **Create Dynamic Group**
2. Configure:
   - **Name**: `finops-logan-dg`
   - **Description**: Dynamic group for Log Analytics object collection rules
   - **Matching Rule**:
     ```
     ALL {resource.type = 'loganalyticsobjectcollectionrule', resource.compartment.id = '<your-compartment-ocid>'}
     ```
3. Click **Create**

## Step 3: Create IAM Policies

Navigate to **Identity & Security** > **Policies**

### Function Policy

1. Click **Create Policy**
2. Configure:
   - **Name**: `finops-function-policy`
   - **Description**: Allow FinOps function to read usage reports and write to bucket
   - **Compartment**: Root compartment (required for cross-tenancy)
   - **Policy Statements**:
     ```
     define tenancy usage-report as ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq
     endorse dynamic-group finops-function-dg to read objects in tenancy usage-report
     allow dynamic-group finops-function-dg to manage objects in compartment <your-compartment>
     allow dynamic-group finops-function-dg to inspect compartments in tenancy
     allow dynamic-group finops-function-dg to inspect tenancies in tenancy
     ```
3. Click **Create**

> **Note: Identity Domains**
>
> If your dynamic groups are in the **OracleIdentityCloudService** domain (not Default), you must qualify the group name with the domain. Use this syntax instead:
>
> ```
> define tenancy usage-report as ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq
> endorse dynamic-group 'OracleIdentityCloudService'/'finops-function-dg' to read objects in tenancy usage-report
> allow dynamic-group 'OracleIdentityCloudService'/'finops-function-dg' to manage objects in compartment <your-compartment>
> allow dynamic-group 'OracleIdentityCloudService'/'finops-function-dg' to inspect compartments in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-function-dg' to inspect tenancies in tenancy
> ```

### Log Analytics Policy

1. Click **Create Policy**
2. Configure:
   - **Name**: `finops-logan-policy`
   - **Description**: Allow Log Analytics to read from bucket and use streaming
   - **Compartment**: Root compartment
   - **Policy Statements**:
     ```
     allow dynamic-group finops-logan-dg to read buckets in tenancy
     allow dynamic-group finops-logan-dg to read objects in tenancy
     allow dynamic-group finops-logan-dg to manage cloudevents-rules in tenancy
     allow dynamic-group finops-logan-dg to inspect compartments in tenancy
     allow dynamic-group finops-logan-dg to use tag-namespaces in tenancy
     allow dynamic-group finops-logan-dg to {STREAM_CONSUME} in tenancy
     ```
3. Click **Create**

> **Note: Identity Domains**
>
> For **OracleIdentityCloudService** domain, use this syntax instead:
>
> ```
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to read buckets in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to read objects in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to manage cloudevents-rules in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to inspect compartments in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to use tag-namespaces in tenancy
> allow dynamic-group 'OracleIdentityCloudService'/'finops-logan-dg' to {STREAM_CONSUME} in tenancy
> ```

## Step 4: Create Streaming

1. Navigate to **Analytics & AI** > **Streaming** > **Stream Pools**
2. Click **Create Stream Pool**
3. Configure:
   - **Name**: `finops-stream-pool`
   - **Compartment**: Your compartment
   - **Auto Create Topics**: Enabled
4. Click **Create**

5. After creation, click **Create Stream**
6. Configure:
   - **Name**: `finops-focus-stream`
   - **Partitions**: 1
   - **Retention**: 24 hours
7. Click **Create**

Note the Stream OCID for later steps.

## Step 5: Create Function Application

1. Navigate to **Developer Services** > **Functions** > **Applications**
2. Click **Create Application**
3. Configure:
   - **Name**: `finops-app`
   - **VCN**: Select your VCN
   - **Subnet**: Select a subnet (private recommended)
4. Click **Create**

5. After creation, add configuration variables:
   - Click the application
   - Go to **Configuration** tab
   - Add:
     ```
     DEST_NAMESPACE = <your-namespace>
     DEST_BUCKET = finops-focus-reports
     LOOKBACK_DAYS = 5
     PRESERVE_PATH = true
     LOG_LEVEL = INFO
     ```

## Step 6: Deploy Function

Using OCI Cloud Shell:

### 6.1 Setup fn CLI

```bash
# List available contexts
fn list context

# Use your region context (e.g., eu-frankfurt-1)
fn use context eu-frankfurt-1

# Set compartment ID
fn update context oracle.compartment-id <your-compartment-ocid>

# Set container registry (replace with your region and namespace)
fn update context registry fra.ocir.io/<namespace>/<repo-prefix>
```

> **Note:** The repo name should be lowercase and can include hyphens.
> Example: `fn update context registry fra.ocir.io/frxfz3gch4zb/finops-app`

Or follow steps 2-4 under your Functions app **Getting Started** > **Cloud Shell setup** in the OCI Console.

### 6.2 Clone and Deploy

```bash
# Clone the repository
git clone https://github.com/rishabh-ghosh24/devspace.git
cd devspace/FinOps/function

# Deploy the function
fn deploy --app finops-app
```

### 6.3 Verify Deployment

After deployment, invoke the function to verify it works:

```bash
fn invoke finops-app focus-report-copier
```

Expected output:
```json
{
  "status": "Success",
  "stats": {
    "days_processed": 5,
    "files_copied": 5,
    "files_skipped": 0,
    "errors": []
  }
}
```

Check your Object Storage bucket (`finops-focus-reports`) - you should see FOCUS report files under the `FOCUS Reports/` folder.

**If successful, proceed to Step 7.** If there are errors, check the [Troubleshooting Guide](troubleshooting.md).

## Step 7: Create Function Schedule

1. Navigate to your function in the console
2. Go to **Schedules** tab
3. Click **Add Schedule**
4. Configure:
   - **Name**: `daily-focus-copy`
   - **Schedule**: `0 6 * * *` (daily at 6 AM UTC)
5. Click **Add**

## Step 8: Create Log Analytics Log Group

1. Navigate to **Observability & Management** > **Log Analytics** > **Administration**
2. Click **Log Groups**
3. Click **Create Log Group**
4. Configure:
   - **Name**: `finops-log-group`
   - **Description**: Log group for FinOps FOCUS cost data
5. Click **Create**

Note the Log Group OCID.

## Step 9: Import FOCUS Parser

1. Navigate to **Log Analytics** > **Administration**
2. Click **Import Configuration Content**
3. Upload `parsers/FOCUS_OCI_*.zip`
4. Click **Import**

## Step 10: Create Object Collection Rule

Using OCI CLI (not available in Console):

```bash
# Create JSON file
cat > focus-rule.json << 'EOF'
{
  "name": "finops-focus-collection-rule",
  "compartmentId": "<your-compartment-ocid>",
  "osNamespace": "<your-namespace>",
  "osBucketName": "finops-focus-reports",
  "logGroupId": "<log-group-ocid>",
  "logSourceName": "FOCUS_OCI",
  "streamId": "<stream-ocid>"
}
EOF

# Create the rule
oci log-analytics object-collection-rule create \
  --from-json file://focus-rule.json \
  --namespace-name <log-analytics-namespace>
```

## Step 11: Import Dashboards

1. Navigate to **Observability & Management** > **Management Dashboards**
2. Click **Import Dashboards**
3. Select dashboard files from `dashboards/` directory:
   - `finops-overview.json`
   - `cost-by-tag.json`
   - `reserved-capacity.json`
   - `cost-forecast.json`
4. Select the log group when prompted
5. Click **Import**

## Step 12: Test the Setup (Optional)

> **Note:** This step is optional if you already verified the function in Step 6.3. Use this for troubleshooting or re-testing after configuration changes.

### Invoke Function Manually

Using fn CLI (simpler):
```bash
fn invoke finops-app focus-report-copier
```

Or using OCI CLI:
```bash
oci fn function invoke \
  --function-id <function-ocid> \
  --body "" \
  --file -
```

Expected output:
```json
{
  "status": "Success",
  "stats": {
    "days_processed": 5,
    "files_copied": 5,
    "files_skipped": 0,
    "errors": []
  }
}
```

### Verify Data in Log Analytics

1. Navigate to **Log Analytics** > **Log Explorer**
2. Run query:
   ```
   'Log Source' = FOCUS_OCI | stats count(*)
   ```
3. You should see record counts

### Check Dashboards

1. Navigate to **Management Dashboards**
2. Open **FinOps Overview**
3. Verify widgets show data

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.
