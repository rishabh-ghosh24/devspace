# ============================================================================
# Log Analytics Module - Log Group and Object Collection Rule
# ============================================================================

variable "compartment_ocid" {
  type = string
}

variable "tenancy_ocid" {
  type = string
}

variable "namespace" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "log_group_name" {
  type = string
}

variable "log_source_name" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "stream_id" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}

# -----------------------------------------------------------------------------
# Data Source - Log Analytics Namespace
# -----------------------------------------------------------------------------

data "oci_log_analytics_namespaces" "current" {
  compartment_id = var.tenancy_ocid
}

locals {
  logan_namespace = data.oci_log_analytics_namespaces.current.namespace_collection[0].items[0].namespace
}

# -----------------------------------------------------------------------------
# Log Group
# -----------------------------------------------------------------------------

resource "oci_log_analytics_log_analytics_log_group" "finops" {
  compartment_id = var.compartment_ocid
  namespace      = local.logan_namespace
  display_name   = var.log_group_name
  description    = "Log group for FinOps FOCUS cost and usage data"

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Object Collection Rule
# -----------------------------------------------------------------------------
# This rule automatically ingests new files from the bucket into Log Analytics

resource "oci_log_analytics_log_analytics_object_collection_rule" "focus" {
  compartment_id      = var.compartment_ocid
  namespace           = local.logan_namespace
  name                = "${var.name_prefix}-focus-collection-rule"
  description         = "Ingest FOCUS reports from Object Storage"

  os_namespace        = var.namespace
  os_bucket_name      = var.bucket_name
  collection_type     = "LIVE"
  poll_since          = "BEGINNING"

  log_group_id        = oci_log_analytics_log_analytics_log_group.finops.id
  log_source_name     = var.log_source_name

  # Optional: Filter to only process FOCUS report files
  # object_name_filters = ["FOCUS Reports/*.csv"]

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "log_group_ocid" {
  value = oci_log_analytics_log_analytics_log_group.finops.id
}

output "log_group_name" {
  value = oci_log_analytics_log_analytics_log_group.finops.display_name
}

output "object_collection_rule_ocid" {
  value = oci_log_analytics_log_analytics_object_collection_rule.focus.id
}

output "logan_namespace" {
  value = local.logan_namespace
}
