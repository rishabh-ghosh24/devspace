# ============================================================================
# OCI FinOps Solution - Terraform Outputs
# ============================================================================

# -----------------------------------------------------------------------------
# Object Storage
# -----------------------------------------------------------------------------

output "bucket_name" {
  description = "Name of the FOCUS reports bucket"
  value       = module.storage.bucket_name
}

output "bucket_namespace" {
  description = "Object Storage namespace"
  value       = data.oci_objectstorage_namespace.current.namespace
}

# -----------------------------------------------------------------------------
# Function
# -----------------------------------------------------------------------------

output "function_ocid" {
  description = "OCID of the FOCUS report copier function"
  value       = module.function.function_ocid
}

output "function_invoke_endpoint" {
  description = "Endpoint to invoke the function"
  value       = module.function.invoke_endpoint
}

# -----------------------------------------------------------------------------
# Streaming
# -----------------------------------------------------------------------------

output "stream_ocid" {
  description = "OCID of the streaming stream"
  value       = module.streaming.stream_id
}

# -----------------------------------------------------------------------------
# Log Analytics
# -----------------------------------------------------------------------------

output "log_group_ocid" {
  description = "OCID of the Log Analytics log group"
  value       = module.log_analytics.log_group_ocid
}

output "object_collection_rule_ocid" {
  description = "OCID of the object collection rule"
  value       = module.log_analytics.object_collection_rule_ocid
}

# -----------------------------------------------------------------------------
# Dashboard URLs
# -----------------------------------------------------------------------------

output "log_analytics_console_url" {
  description = "URL to access Log Analytics in the OCI Console"
  value       = "https://cloud.oracle.com/loganalytics/home?region=${var.region}"
}

output "dashboard_import_instructions" {
  description = "Instructions to import the FinOps dashboards"
  value       = <<-EOT
    To import the FinOps dashboards:
    1. Go to Observability & Management > Management Dashboards
    2. Click "Import Dashboards"
    3. Upload the JSON files from the dashboards/ directory
    4. Select the log group: ${var.log_group_name}
  EOT
}

# -----------------------------------------------------------------------------
# Quick Start
# -----------------------------------------------------------------------------

output "next_steps" {
  description = "Next steps after deployment"
  value       = <<-EOT

    FinOps Solution Deployed Successfully!
    =====================================

    Resources Created:
    - Bucket: ${module.storage.bucket_name}
    - Function: focus-report-copier (runs daily at ${var.function_schedule_cron} UTC)
    - Log Group: ${var.log_group_name}
    - Object Collection Rule: Configured to ingest FOCUS reports

    Next Steps:
    1. Wait for the function to run (or invoke manually)
    2. Import the dashboards from the dashboards/ directory
    3. Configure alerts in Log Analytics

    Manual Function Invocation:
    $ oci fn function invoke --function-id ${module.function.function_ocid} --body "" --file -

  EOT
}
