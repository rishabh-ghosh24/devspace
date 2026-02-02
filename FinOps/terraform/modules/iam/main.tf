# ============================================================================
# IAM Module - Dynamic Groups and Policies
# ============================================================================

variable "compartment_ocid" {
  type = string
}

variable "tenancy_ocid" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "usage_report_tenancy" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}

# -----------------------------------------------------------------------------
# Dynamic Group for Functions
# -----------------------------------------------------------------------------

resource "oci_identity_dynamic_group" "function" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-function-dg"
  description    = "Dynamic group for FinOps FOCUS report copier function"

  matching_rule = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Dynamic Group for Log Analytics Object Collection Rule
# -----------------------------------------------------------------------------

resource "oci_identity_dynamic_group" "log_analytics" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-logan-dg"
  description    = "Dynamic group for Log Analytics object collection rules"

  matching_rule = "ALL {resource.type = 'loganalyticsobjectcollectionrule', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Policy for Function to Access Usage Reports
# -----------------------------------------------------------------------------

resource "oci_identity_policy" "function_usage_reports" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-function-policy"
  description    = "Allow FinOps function to read usage reports and write to bucket"

  statements = [
    # Allow function to read from Oracle's usage report tenancy
    "define tenancy usage-report as ${var.usage_report_tenancy}",
    "endorse dynamic-group ${oci_identity_dynamic_group.function.name} to read objects in tenancy usage-report",

    # Allow function to manage objects in the destination bucket
    "allow dynamic-group ${oci_identity_dynamic_group.function.name} to manage objects in compartment id ${var.compartment_ocid}",

    # Allow function to inspect compartments and tenancy (for validation)
    "allow dynamic-group ${oci_identity_dynamic_group.function.name} to inspect compartments in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.function.name} to inspect tenancies in tenancy",
  ]

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Policy for Log Analytics Object Collection
# -----------------------------------------------------------------------------

resource "oci_identity_policy" "log_analytics" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-logan-policy"
  description    = "Allow Log Analytics to read from bucket and use streaming"

  statements = [
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to read buckets in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to read objects in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to manage cloudevents-rules in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to inspect compartments in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to use tag-namespaces in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.log_analytics.name} to {STREAM_CONSUME} in tenancy",
  ]

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "function_dynamic_group_ocid" {
  value = oci_identity_dynamic_group.function.id
}

output "log_analytics_dynamic_group_ocid" {
  value = oci_identity_dynamic_group.log_analytics.id
}
