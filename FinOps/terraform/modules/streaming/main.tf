# ============================================================================
# Streaming Module - Stream Pool and Stream
# ============================================================================

variable "compartment_ocid" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}

# -----------------------------------------------------------------------------
# Stream Pool
# -----------------------------------------------------------------------------

resource "oci_streaming_stream_pool" "finops" {
  compartment_id = var.compartment_ocid
  name           = "${var.name_prefix}-stream-pool"

  kafka_settings {
    auto_create_topics_enable = true
    log_retention_hours       = 24
    num_partitions            = 1
  }

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Stream
# -----------------------------------------------------------------------------

resource "oci_streaming_stream" "finops" {
  name               = "${var.name_prefix}-focus-stream"
  stream_pool_id     = oci_streaming_stream_pool.finops.id
  partitions         = 1
  retention_in_hours = 24

  freeform_tags = var.freeform_tags
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "stream_pool_id" {
  value = oci_streaming_stream_pool.finops.id
}

output "stream_id" {
  value = oci_streaming_stream.finops.id
}

output "stream_messages_endpoint" {
  value = oci_streaming_stream_pool.finops.endpoint_fqdn
}
