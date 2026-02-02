"""
OCI FOCUS Report Copier Function

Copies FOCUS (FinOps Open Cost and Usage Specification) reports from Oracle's
internal usage report bucket to the customer's Object Storage bucket for
ingestion into Log Analytics.

Environment Variables:
    LOOKBACK_DAYS: Number of days to look back for reports (default: 5)
    DEST_NAMESPACE: Destination Object Storage namespace
    DEST_BUCKET: Destination bucket name (default: "finops-focus-reports")
    PRESERVE_PATH: Whether to preserve date folder structure (default: "true")
    LOG_LEVEL: Logging level (default: "INFO")

Author: Based on Oracle oci-o11y-solutions, enhanced for production use
License: UPL-1.0
"""

import io
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

import oci
from fdk import response

# Configuration from environment variables
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "5"))
DEST_NAMESPACE = os.environ.get("DEST_NAMESPACE", "")
DEST_BUCKET = os.environ.get("DEST_BUCKET", "finops-focus-reports")
PRESERVE_PATH = os.environ.get("PRESERVE_PATH", "true").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Oracle's internal FOCUS report location (constant)
REPORTING_NAMESPACE = "bling"

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FocusReportCopier:
    """Handles copying FOCUS reports from Oracle's internal bucket to customer bucket."""

    def __init__(self, signer):
        """Initialize with OCI signer for authentication."""
        self.object_storage = oci.object_storage.ObjectStorageClient(
            config={}, signer=signer
        )
        self.stats = {
            "days_processed": 0,
            "files_checked": 0,
            "files_copied": 0,
            "files_skipped": 0,
            "bytes_copied": 0,
            "errors": []
        }

    def get_source_tenancy_ocid(self) -> str:
        """Get the source tenancy OCID from the signer."""
        try:
            identity = oci.identity.IdentityClient(
                config={}, signer=self.object_storage.base_client.signer
            )
            tenancy = identity.get_tenancy(
                self.object_storage.base_client.signer.tenancy_id
            ).data
            return tenancy.id
        except Exception as e:
            logger.warning(f"Could not get tenancy OCID: {e}")
            # Fallback: use the signer's tenancy_id directly
            return self.object_storage.base_client.signer.tenancy_id

    def file_exists_in_destination(self, object_name: str) -> bool:
        """Check if a file already exists in the destination bucket."""
        try:
            self.object_storage.head_object(
                namespace_name=DEST_NAMESPACE,
                bucket_name=DEST_BUCKET,
                object_name=object_name
            )
            return True
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return False
            raise

    def copy_file(self, source_tenancy: str, source_object_name: str) -> bool:
        """
        Copy a single file from source to destination.

        Returns True if file was copied, False if skipped or failed.
        """
        # Determine destination object name
        if PRESERVE_PATH:
            # Keep the full path: FOCUS Reports/2025/01/26/report.csv
            dest_object_name = source_object_name
        else:
            # Just the filename: report.csv
            dest_object_name = source_object_name.rsplit("/", 1)[-1]

        # Check if file already exists
        if self.file_exists_in_destination(dest_object_name):
            logger.debug(f"Skipping (exists): {dest_object_name}")
            self.stats["files_skipped"] += 1
            return False

        try:
            # Get object from source
            logger.info(f"Copying: {source_object_name}")
            obj_response = self.object_storage.get_object(
                namespace_name=REPORTING_NAMESPACE,
                bucket_name=source_tenancy,
                object_name=source_object_name
            )

            # Stream to destination
            content = obj_response.data.content
            content_length = len(content)

            self.object_storage.put_object(
                namespace_name=DEST_NAMESPACE,
                bucket_name=DEST_BUCKET,
                object_name=dest_object_name,
                put_object_body=content
            )

            self.stats["files_copied"] += 1
            self.stats["bytes_copied"] += content_length
            logger.info(f"Copied: {dest_object_name} ({content_length:,} bytes)")
            return True

        except oci.exceptions.ServiceError as e:
            error_msg = f"Failed to copy {source_object_name}: {e.message}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return False

    def process_day(self, source_tenancy: str, target_date: datetime) -> int:
        """
        Process all FOCUS reports for a specific day.

        Returns number of files copied.
        """
        prefix = (
            f"FOCUS Reports/{target_date.year}/"
            f"{target_date.strftime('%m')}/{target_date.strftime('%d')}"
        )

        logger.info(f"Processing date: {target_date.strftime('%Y-%m-%d')} (prefix: {prefix})")

        try:
            # List all objects with this prefix
            objects = oci.pagination.list_call_get_all_results(
                self.object_storage.list_objects,
                namespace_name=REPORTING_NAMESPACE,
                bucket_name=source_tenancy,
                prefix=prefix
            )

            files_copied = 0
            for obj in objects.data.objects:
                self.stats["files_checked"] += 1
                if self.copy_file(source_tenancy, obj.name):
                    files_copied += 1

            self.stats["days_processed"] += 1
            return files_copied

        except oci.exceptions.ServiceError as e:
            error_msg = f"Failed to list objects for {prefix}: {e.message}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return 0

    def run(self, source_tenancy: str) -> dict:
        """
        Main execution: process all days in the lookback window.

        Returns statistics dictionary.
        """
        logger.info(f"Starting FOCUS report copy (lookback: {LOOKBACK_DAYS} days)")
        logger.info(f"Source: {REPORTING_NAMESPACE}/{source_tenancy}")
        logger.info(f"Destination: {DEST_NAMESPACE}/{DEST_BUCKET}")

        # Process each day in the lookback window (oldest first)
        for days_ago in range(LOOKBACK_DAYS, 0, -1):
            target_date = datetime.now() - timedelta(days=days_ago)
            self.process_day(source_tenancy, target_date)

        # Log summary
        logger.info(
            f"Complete: {self.stats['files_copied']} copied, "
            f"{self.stats['files_skipped']} skipped, "
            f"{len(self.stats['errors'])} errors"
        )

        return self.stats


def handler(ctx, data: io.BytesIO = None) -> response.Response:
    """
    OCI Function entry point.

    Can be triggered by:
    - Schedule (daily)
    - Manual invocation
    - Event (optional)
    """
    try:
        # Validate configuration
        if not DEST_NAMESPACE:
            raise ValueError("DEST_NAMESPACE environment variable is required")

        # Get resource principal signer
        signer = oci.auth.signers.get_resource_principals_signer()

        # Get source tenancy OCID (the customer's tenancy)
        copier = FocusReportCopier(signer)
        source_tenancy = copier.get_source_tenancy_ocid()

        # Run the copy process
        stats = copier.run(source_tenancy)

        # Determine response status
        if stats["errors"]:
            status_msg = "Completed with errors"
        elif stats["files_copied"] == 0 and stats["files_skipped"] == 0:
            status_msg = "No files found"
        elif stats["files_copied"] == 0:
            status_msg = "All files already synced"
        else:
            status_msg = "Success"

        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": status_msg,
                "stats": stats
            }),
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        logger.exception("Function failed")
        return response.Response(
            ctx,
            response_data=json.dumps({
                "status": "Failed",
                "error": str(e)
            }),
            headers={"Content-Type": "application/json"},
            status_code=500
        )


# For local testing
if __name__ == "__main__":
    # Mock context for local testing
    class MockContext:
        pass

    # Set test environment
    os.environ.setdefault("DEST_NAMESPACE", "your-namespace")
    os.environ.setdefault("DEST_BUCKET", "finops-focus-reports")
    os.environ.setdefault("LOOKBACK_DAYS", "3")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")

    print("Running in test mode...")
    print("Note: This requires OCI CLI configuration for local testing")
