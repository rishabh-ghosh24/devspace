# Troubleshooting Guide

Common issues and solutions for the OCI FinOps solution.

## Function Issues

### Function Fails with "Permission Denied"

**Symptoms**: Function returns error about not being able to read from usage-report tenancy.

**Causes**:
1. Dynamic group not matching the function
2. Policy not correctly endorsing cross-tenancy access

**Solutions**:

1. Verify dynamic group matching rule:
   ```bash
   oci iam dynamic-group get --dynamic-group-id <dg-ocid>
   ```
   Ensure compartment OCID matches where function is deployed.

2. Verify policy exists at root compartment:
   ```bash
   oci iam policy list --compartment-id <tenancy-ocid> | grep finops
   ```

3. Check policy syntax:
   ```
   define tenancy usage-report as ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq
   endorse dynamic-group <dg-name> to read objects in tenancy usage-report
   ```

### Function Returns "No Files Found"

**Symptoms**: Function succeeds but copies 0 files.

**Causes**:
1. FOCUS reports not yet available for the date range
2. Incorrect lookback configuration
3. Reports already copied (duplicate detection)

**Solutions**:

1. FOCUS reports have 24-72 hour delay. Check if looking far enough back:
   ```bash
   # Invoke with debug logging
   oci fn function update --function-id <fn-ocid> --config '{"LOG_LEVEL": "DEBUG"}'
   oci fn function invoke --function-id <fn-ocid> --body "" --file -
   ```

2. Increase lookback window:
   ```bash
   oci fn function update --function-id <fn-ocid> --config '{"LOOKBACK_DAYS": "7"}'
   ```

3. Check if files already exist in destination bucket:
   ```bash
   oci os object list --bucket-name finops-focus-reports --prefix "FOCUS Reports/"
   ```

### Function Timeout

**Symptoms**: Function fails after 300 seconds.

**Causes**:
1. Too many files to process in time limit
2. Network issues
3. Large files

**Solutions**:

1. Increase function timeout (max 300s):
   ```bash
   oci fn function update --function-id <fn-ocid> --timeout-in-seconds 300
   ```

2. Increase memory (improves performance):
   ```bash
   oci fn function update --function-id <fn-ocid> --memory-in-mbs 512
   ```

3. Reduce lookback window for initial sync, then increase after caught up.

## Log Analytics Issues

### No Data in Log Analytics

**Symptoms**: Dashboards show no data, queries return empty.

**Causes**:
1. Object Collection Rule not working
2. Parser not imported
3. Files in bucket but not ingested

**Solutions**:

1. Check Object Collection Rule status:
   ```bash
   oci log-analytics object-collection-rule list \
     --namespace-name <logan-namespace> \
     --compartment-id <compartment-ocid>
   ```

2. Verify parser is imported:
   - Go to **Log Analytics** > **Administration** > **Sources**
   - Search for "FOCUS_OCI"
   - If missing, import from `parsers/` directory

3. Check rule is pointing to correct bucket and log group.

4. Trigger manual ingestion:
   - Go to **Log Analytics** > **Upload Logs**
   - Select a file from the bucket manually

### Parser Errors

**Symptoms**: Data is ingested but fields are not parsed correctly.

**Causes**:
1. CSV format changed
2. Parser version mismatch

**Solutions**:

1. Test parser manually:
   - Go to **Log Analytics** > **Administration** > **Sources**
   - Click on FOCUS_OCI source
   - Use **Test Source** with a sample file

2. Check for parser updates in the repository.

3. Export and review field mappings:
   ```bash
   oci log-analytics source get \
     --namespace-name <logan-namespace> \
     --source-name FOCUS_OCI
   ```

### Query Performance

**Symptoms**: Queries timeout or run slowly.

**Solutions**:

1. Add time filters to reduce data scanned:
   ```sql
   'Log Source' = FOCUS_OCI and Time > dateRelative(7day)
   ```

2. Limit result sets:
   ```sql
   ... | head 100
   ```

3. Avoid expensive operations on large datasets:
   - `distinct()` on high-cardinality fields
   - Nested subqueries
   - Cross-joins

## Streaming Issues

### Object Collection Rule Not Triggering

**Symptoms**: Files in bucket but Log Analytics doesn't see them.

**Causes**:
1. Streaming not connected properly
2. Stream consumer stopped

**Solutions**:

1. Check stream health:
   ```bash
   oci streaming stream get --stream-id <stream-ocid>
   ```

2. Verify Object Collection Rule uses correct stream:
   ```bash
   oci log-analytics object-collection-rule get \
     --namespace-name <logan-namespace> \
     --object-collection-rule-id <rule-ocid>
   ```

3. Recreate the Object Collection Rule if needed.

## Dashboard Issues

### Import Fails

**Symptoms**: Dashboard import shows errors.

**Causes**:
1. Missing log group
2. Invalid JSON format
3. OCID references to non-existent objects

**Solutions**:

1. Ensure log group exists and is accessible.

2. Validate JSON:
   ```bash
   python -m json.tool < dashboard.json
   ```

3. Use the parameterized dashboards from this repository (no hardcoded OCIDs).

### Widgets Show "No Data"

**Symptoms**: Dashboard imported but widgets are empty.

**Causes**:
1. No data ingested yet
2. Time range doesn't match data
3. Log group not selected

**Solutions**:

1. Verify data exists:
   ```sql
   'Log Source' = FOCUS_OCI | stats count(*)
   ```

2. Adjust dashboard time range (top right).

3. Check widget query references correct log source.

## IAM Issues

### Policy Not Taking Effect

**Symptoms**: Permissions don't work despite policies being created.

**Causes**:
1. Policy propagation delay (up to 10 minutes)
2. Policy in wrong compartment
3. Syntax errors

**Solutions**:

1. Wait 10 minutes and retry.

2. Verify policy compartment:
   - Cross-tenancy policies must be at root
   - Dynamic group policies typically at root

3. Validate syntax in OCI Console (provides error highlighting).

### Dynamic Group Not Matching

**Symptoms**: Resources not matching dynamic group rules.

**Solutions**:

1. Test matching rule:
   ```bash
   oci iam dynamic-group get --dynamic-group-id <dg-ocid>
   ```

2. Verify resource type:
   - Functions: `resource.type = 'fnfunc'`
   - Object Collection Rules: `resource.type = 'loganalyticsobjectcollectionrule'`

3. Check compartment OCID is correct (not name).

## Terraform Issues

### Provider Authentication Fails

**Symptoms**: Terraform can't authenticate to OCI.

**Solutions**:

1. Check OCI CLI configuration:
   ```bash
   oci iam region list
   ```

2. Verify environment variables or config file:
   ```bash
   export OCI_CONFIG_FILE=~/.oci/config
   export OCI_CONFIG_PROFILE=DEFAULT
   ```

### Resource Already Exists

**Symptoms**: Terraform fails because resource exists.

**Solutions**:

1. Import existing resource:
   ```bash
   terraform import module.storage.oci_objectstorage_bucket.focus_reports <bucket-ocid>
   ```

2. Or remove and recreate (destructive):
   ```bash
   terraform destroy -target=module.storage
   terraform apply
   ```

## Getting Help

If issues persist:

1. Check OCI service health: [status.oracle.com](https://status.oracle.com)
2. Review OCI documentation
3. Open GitHub issue with:
   - Error messages
   - Terraform version
   - OCI region
   - Relevant logs (sanitized)
