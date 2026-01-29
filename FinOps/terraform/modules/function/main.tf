# ============================================================================
# Function Module - OCI Function for FOCUS Report Copying
# ============================================================================

variable "compartment_ocid" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "subnet_id" {
  type    = string
  default = null
}

variable "dest_namespace" {
  type = string
}

variable "dest_bucket" {
  type = string
}

variable "lookback_days" {
  type    = number
  default = 5
}

variable "memory_mb" {
  type    = number
  default = 256
}

variable "timeout_seconds" {
  type    = number
  default = 300
}

variable "schedule_cron" {
  type    = string
  default = "0 6 * * *"
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# -----------------------------------------------------------------------------
# Function Application
# -----------------------------------------------------------------------------

resource "oci_functions_application" "finops" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.name_prefix}-app"

  # Note: In production, you should provide a proper subnet_id
  # If subnet_id is not provided, the function will need to be configured manually
  subnet_ids = var.subnet_id != null ? [var.subnet_id] : []

  config = {
    "DEST_NAMESPACE"  = var.dest_namespace
    "DEST_BUCKET"     = var.dest_bucket
    "LOOKBACK_DAYS"   = tostring(var.lookback_days)
    "PRESERVE_PATH"   = "true"
    "LOG_LEVEL"       = "INFO"
  }

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Note: Function deployment requires fn CLI or OCIR
# -----------------------------------------------------------------------------
# The actual function code needs to be deployed using:
#   1. fn CLI: fn deploy --app <app-name>
#   2. Or via Container Registry (OCIR)
#
# This Terraform creates the application and configuration.
# See docs/manual-setup.md for function deployment instructions.

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "application_ocid" {
  value = oci_functions_application.finops.id
}

output "function_ocid" {
  description = "Deploy the function using fn CLI, then reference here"
  value       = "Deploy function using: fn deploy --app ${var.name_prefix}-app"
}

output "invoke_endpoint" {
  value = "https://functions.${data.oci_identity_availability_domains.ads.availability_domains[0].name}.oci.oraclecloud.com"
}

output "deployment_instructions" {
  value = <<-EOT
    To deploy the function:
    1. cd function/
    2. fn use context <your-context>
    3. fn deploy --app ${var.name_prefix}-app
  EOT
}
