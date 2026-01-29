# ============================================================================
# OCI FinOps Solution - Terraform Variables
# ============================================================================

# -----------------------------------------------------------------------------
# Required Variables
# -----------------------------------------------------------------------------

variable "tenancy_ocid" {
  description = "The OCID of your OCI tenancy"
  type        = string
}

variable "compartment_ocid" {
  description = "The OCID of the compartment where resources will be created"
  type        = string
}

variable "region" {
  description = "The OCI region where resources will be created (e.g., us-ashburn-1)"
  type        = string
}

# -----------------------------------------------------------------------------
# Optional Variables - Naming
# -----------------------------------------------------------------------------

variable "project_name" {
  description = "Project name prefix for all resources"
  type        = string
  default     = "finops"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "prod"
}

# -----------------------------------------------------------------------------
# Optional Variables - Object Storage
# -----------------------------------------------------------------------------

variable "bucket_name" {
  description = "Name of the Object Storage bucket for FOCUS reports"
  type        = string
  default     = "finops-focus-reports"
}

variable "bucket_retention_days" {
  description = "Number of days to retain FOCUS reports (0 = forever)"
  type        = number
  default     = 365
}

# -----------------------------------------------------------------------------
# Optional Variables - Function
# -----------------------------------------------------------------------------

variable "function_lookback_days" {
  description = "Number of days to look back when copying FOCUS reports"
  type        = number
  default     = 5
}

variable "function_memory_mb" {
  description = "Memory allocation for the function (MB)"
  type        = number
  default     = 256
}

variable "function_timeout_seconds" {
  description = "Function timeout in seconds"
  type        = number
  default     = 300
}

variable "function_schedule_cron" {
  description = "Cron expression for function schedule (UTC)"
  type        = string
  default     = "0 6 * * *"  # Daily at 6 AM UTC
}

# -----------------------------------------------------------------------------
# Optional Variables - Log Analytics
# -----------------------------------------------------------------------------

variable "log_group_name" {
  description = "Name of the Log Analytics log group"
  type        = string
  default     = "finops-log-group"
}

variable "log_source_name" {
  description = "Name of the Log Analytics log source"
  type        = string
  default     = "FOCUS_OCI"
}

# -----------------------------------------------------------------------------
# Optional Variables - Notifications
# -----------------------------------------------------------------------------

variable "notification_email" {
  description = "Email address for alert notifications (optional)"
  type        = string
  default     = ""
}

variable "alert_threshold_overage" {
  description = "Cost overage threshold (in currency) to trigger alerts"
  type        = number
  default     = 100
}

# -----------------------------------------------------------------------------
# Optional Variables - Tagging
# -----------------------------------------------------------------------------

variable "freeform_tags" {
  description = "Freeform tags to apply to all resources"
  type        = map(string)
  default = {
    "Project"   = "FinOps"
    "ManagedBy" = "Terraform"
  }
}

variable "defined_tags" {
  description = "Defined tags to apply to all resources"
  type        = map(string)
  default     = {}
}
