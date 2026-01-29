# ============================================================================
# OCI FinOps Solution - Main Terraform Configuration
# ============================================================================
#
# This Terraform configuration deploys a complete FinOps solution for OCI:
# - Object Storage bucket for FOCUS reports
# - OCI Function to copy reports from Oracle's internal bucket
# - Streaming for real-time ingestion
# - Log Analytics for querying and dashboards
# - IAM policies for least-privilege access
#
# Usage:
#   terraform init
#   terraform plan -var-file="terraform.tfvars"
#   terraform apply -var-file="terraform.tfvars"
#
# ============================================================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.region
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "oci_identity_tenancy" "current" {
  tenancy_id = var.tenancy_ocid
}

data "oci_objectstorage_namespace" "current" {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_regions" "available" {}

# -----------------------------------------------------------------------------
# Local Values
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.freeform_tags, {
    "Environment" = var.environment
  })

  # Oracle's FOCUS report tenancy (constant)
  usage_report_tenancy = "ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq"
}

# -----------------------------------------------------------------------------
# IAM Module
# -----------------------------------------------------------------------------

module "iam" {
  source = "./modules/iam"

  compartment_ocid        = var.compartment_ocid
  tenancy_ocid            = var.tenancy_ocid
  name_prefix             = local.name_prefix
  usage_report_tenancy    = local.usage_report_tenancy
  freeform_tags           = local.common_tags
}

# -----------------------------------------------------------------------------
# Object Storage Module
# -----------------------------------------------------------------------------

module "storage" {
  source = "./modules/storage"

  compartment_ocid      = var.compartment_ocid
  namespace             = data.oci_objectstorage_namespace.current.namespace
  bucket_name           = var.bucket_name
  retention_days        = var.bucket_retention_days
  freeform_tags         = local.common_tags
}

# -----------------------------------------------------------------------------
# Streaming Module
# -----------------------------------------------------------------------------

module "streaming" {
  source = "./modules/streaming"

  compartment_ocid = var.compartment_ocid
  name_prefix      = local.name_prefix
  freeform_tags    = local.common_tags
}

# -----------------------------------------------------------------------------
# Function Module
# -----------------------------------------------------------------------------

module "function" {
  source = "./modules/function"

  compartment_ocid     = var.compartment_ocid
  name_prefix          = local.name_prefix
  subnet_id            = null  # Will use default VCN or you can provide one
  dest_namespace       = data.oci_objectstorage_namespace.current.namespace
  dest_bucket          = module.storage.bucket_name
  lookback_days        = var.function_lookback_days
  memory_mb            = var.function_memory_mb
  timeout_seconds      = var.function_timeout_seconds
  schedule_cron        = var.function_schedule_cron
  freeform_tags        = local.common_tags

  depends_on = [module.iam, module.storage]
}

# -----------------------------------------------------------------------------
# Log Analytics Module
# -----------------------------------------------------------------------------

module "log_analytics" {
  source = "./modules/log-analytics"

  compartment_ocid     = var.compartment_ocid
  tenancy_ocid         = var.tenancy_ocid
  namespace            = data.oci_objectstorage_namespace.current.namespace
  name_prefix          = local.name_prefix
  log_group_name       = var.log_group_name
  log_source_name      = var.log_source_name
  bucket_name          = module.storage.bucket_name
  stream_id            = module.streaming.stream_id
  freeform_tags        = local.common_tags

  depends_on = [module.storage, module.streaming]
}
