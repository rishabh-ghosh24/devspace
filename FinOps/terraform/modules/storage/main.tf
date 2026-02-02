# ============================================================================
# Storage Module - Object Storage Bucket
# ============================================================================

variable "compartment_ocid" {
  type = string
}

variable "namespace" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "retention_days" {
  type    = number
  default = 365
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}

# -----------------------------------------------------------------------------
# Object Storage Bucket
# -----------------------------------------------------------------------------

resource "oci_objectstorage_bucket" "focus_reports" {
  compartment_id = var.compartment_ocid
  namespace      = var.namespace
  name           = var.bucket_name

  access_type           = "NoPublicAccess"
  storage_tier          = "Standard"
  versioning            = "Disabled"
  auto_tiering          = "Disabled"

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Lifecycle Policy (Optional - for data retention)
# -----------------------------------------------------------------------------

resource "oci_objectstorage_object_lifecycle_policy" "retention" {
  count = var.retention_days > 0 ? 1 : 0

  namespace = var.namespace
  bucket    = oci_objectstorage_bucket.focus_reports.name

  rules {
    name        = "delete-old-reports"
    action      = "DELETE"
    is_enabled  = true
    time_amount = var.retention_days
    time_unit   = "DAYS"

    object_name_filter {
      inclusion_prefixes = ["FOCUS Reports/"]
    }
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "bucket_name" {
  value = oci_objectstorage_bucket.focus_reports.name
}

output "bucket_ocid" {
  value = oci_objectstorage_bucket.focus_reports.bucket_id
}
