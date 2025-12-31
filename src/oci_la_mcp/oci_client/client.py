"""OCI Log Analytics client wrapper."""

import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import oci

from .auth import get_signer
from .rate_limiter import RateLimiter
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class OCILogAnalyticsClient:
    """Wrapper for OCI Log Analytics operations.

    This client provides async-compatible methods for interacting with
    OCI Log Analytics APIs, with built-in rate limiting and error handling.
    """

    def __init__(self, settings: Settings):
        """Initialize the OCI client.

        Args:
            settings: Application settings with OCI configuration.
        """
        self.settings = settings
        self._config, self._signer = get_signer(settings.oci)

        self._la_client = oci.log_analytics.LogAnalyticsClient(
            config=self._config, signer=self._signer
        )

        self._identity_client = oci.identity.IdentityClient(
            config=self._config, signer=self._signer
        )

        self._rate_limiter = RateLimiter()

        # Runtime context (can be changed)
        self._namespace = settings.log_analytics.namespace
        self._compartment_id = settings.log_analytics.default_compartment_id

    @property
    def namespace(self) -> str:
        """Get current Log Analytics namespace."""
        return self._namespace

    @namespace.setter
    def namespace(self, value: str) -> None:
        """Set Log Analytics namespace."""
        self._namespace = value

    @property
    def compartment_id(self) -> str:
        """Get current compartment ID."""
        return self._compartment_id

    @compartment_id.setter
    def compartment_id(self, value: str) -> None:
        """Set compartment ID."""
        self._compartment_id = value

    def _is_tenancy_ocid(self, ocid: str) -> bool:
        """Check if an OCID is a tenancy OCID.

        Args:
            ocid: The OCID to check.

        Returns:
            True if this is a tenancy OCID.
        """
        return ocid.startswith("ocid1.tenancy.")

    async def _get_all_compartments(self) -> List[str]:
        """Get ALL compartment OCIDs in the entire tenancy tree.

        Returns:
            List of all compartment OCIDs (including nested ones).
        """
        tenancy_id = self._config.get("tenancy")
        compartments = []

        try:
            # Use compartment_id_in_subtree=True to get ALL compartments
            response = self._identity_client.list_compartments(
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True,  # Get entire tree, not just first level
                lifecycle_state="ACTIVE",
                access_level="ACCESSIBLE",
            )
            compartments = [c.id for c in response.data]

            # Handle pagination
            while response.has_next_page:
                await self._rate_limiter.acquire()
                response = self._identity_client.list_compartments(
                    compartment_id=tenancy_id,
                    compartment_id_in_subtree=True,
                    lifecycle_state="ACTIVE",
                    access_level="ACCESSIBLE",
                    page=response.next_page,
                )
                compartments.extend([c.id for c in response.data])

            logger.info(f"Found {len(compartments)} total compartments in tenancy tree")
        except Exception as e:
            logger.warning(f"Failed to list compartments: {e}")

        return compartments

    async def query(
        self,
        query_string: str,
        time_start: str,
        time_end: str,
        max_results: Optional[int] = None,
        include_subcompartments: bool = False,
    ) -> Dict[str, Any]:
        """Execute a Log Analytics query.

        Args:
            query_string: The Log Analytics query to execute.
            time_start: Start time in ISO 8601 format.
            time_end: End time in ISO 8601 format.
            max_results: Maximum number of results to return.
            include_subcompartments: If True, include logs from sub-compartments.

        Returns:
            Dictionary containing query results and metadata.

        Raises:
            oci.exceptions.ServiceError: If OCI API call fails.
        """
        # Debug logging
        logger.info(f"Query called: compartment={self._compartment_id[:50]}...")
        logger.info(f"Query params: include_subcompartments={include_subcompartments}")
        is_tenancy = self._is_tenancy_ocid(self._compartment_id)
        logger.info(f"Is tenancy OCID: {is_tenancy}")

        # Check if we need to handle tenancy-level cross-compartment query
        # OCI API ignores compartment_id_in_subtree when compartment_id is tenancy OCID
        if include_subcompartments and is_tenancy:
            logger.info(
                "Detected tenancy OCID with include_subcompartments=True. "
                "Querying ALL compartments in tenancy tree..."
            )
            return await self._query_all_compartments(
                query_string, time_start, time_end, max_results
            )

        logger.info("Using single compartment query (not tenancy or subcompartments=False)")
        return await self._execute_single_query(
            query_string, time_start, time_end, max_results,
            self._compartment_id, include_subcompartments
        )

    async def _execute_single_query(
        self,
        query_string: str,
        time_start: str,
        time_end: str,
        max_results: Optional[int],
        compartment_id: str,
        include_subcompartments: bool,
    ) -> Dict[str, Any]:
        """Execute a query against a single compartment.

        Args:
            query_string: The Log Analytics query to execute.
            time_start: Start time in ISO 8601 format.
            time_end: End time in ISO 8601 format.
            max_results: Maximum number of results to return.
            compartment_id: Compartment to query.
            include_subcompartments: If True, include logs from sub-compartments.

        Returns:
            Dictionary containing query results and metadata.
        """
        await self._rate_limiter.acquire()

        max_results = max_results or self.settings.query.max_results

        # Parse time strings to datetime
        time_start_dt = datetime.fromisoformat(time_start.replace("Z", "+00:00"))
        time_end_dt = datetime.fromisoformat(time_end.replace("Z", "+00:00"))

        # Create TimeRange object for time_filter parameter
        time_range = oci.log_analytics.models.TimeRange(
            time_start=time_start_dt,
            time_end=time_end_dt,
            time_zone="UTC",
        )

        query_details = oci.log_analytics.models.QueryDetails(
            compartment_id=compartment_id,
            compartment_id_in_subtree=include_subcompartments,
            query_string=query_string,
            sub_system=oci.log_analytics.models.QueryDetails.SUB_SYSTEM_LOG,
            time_filter=time_range,
            max_total_count=max_results,
        )

        logger.info(
            f"OCI Query: compartment={compartment_id}, "
            f"include_subtree={include_subcompartments}, "
            f"namespace={self._namespace}"
        )

        try:
            response = self._la_client.query(
                namespace_name=self._namespace,
                query_details=query_details,
            )
            self._rate_limiter.reset()
            return self._parse_query_response(response.data)
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                await self._rate_limiter.handle_rate_limit()
                return await self._execute_single_query(
                    query_string, time_start, time_end, max_results,
                    compartment_id, include_subcompartments
                )
            raise

    async def _query_all_compartments(
        self,
        query_string: str,
        time_start: str,
        time_end: str,
        max_results: Optional[int],
    ) -> Dict[str, Any]:
        """Query ALL compartments in the tenancy tree and aggregate results.

        This is a workaround for OCI API behavior where compartment_id_in_subtree
        is ignored when compartment_id is a tenancy OCID.

        Args:
            query_string: The Log Analytics query to execute.
            time_start: Start time in ISO 8601 format.
            time_end: End time in ISO 8601 format.
            max_results: Maximum number of results to return.

        Returns:
            Aggregated query results from all compartments.
        """
        # Get ALL compartments in the entire tenancy tree
        compartments = await self._get_all_compartments()

        if not compartments:
            logger.warning("No compartments found, falling back to tenancy query")
            return await self._execute_single_query(
                query_string, time_start, time_end, max_results,
                self._compartment_id, True
            )

        logger.info(f"Will query {len(compartments)} compartments across tenancy tree")

        all_columns = []
        all_rows = []
        total_count = 0
        is_partial = False
        successful_queries = 0
        failed_queries = 0

        for i, comp_id in enumerate(compartments):
            try:
                if (i + 1) % 10 == 0 or i == 0:
                    logger.info(f"Querying compartment {i+1}/{len(compartments)}...")

                # Query each compartment directly (no need for include_subcompartments
                # since we're already iterating through all compartments)
                result = await self._execute_single_query(
                    query_string, time_start, time_end, max_results,
                    comp_id, False  # Don't use subtree since we query each compartment
                )

                # Use columns from first successful response
                if not all_columns and result.get("columns"):
                    all_columns = result["columns"]

                all_rows.extend(result.get("rows", []))
                total_count += result.get("total_count", 0)
                successful_queries += 1

                if result.get("is_partial", False):
                    is_partial = True

            except Exception as e:
                failed_queries += 1
                # Only log first few failures to avoid spam
                if failed_queries <= 5:
                    logger.warning(f"Failed to query compartment {comp_id[:50]}: {e}")
                elif failed_queries == 6:
                    logger.warning("Suppressing further compartment query failure logs...")
                continue

        logger.info(
            f"Cross-compartment query complete: "
            f"{successful_queries}/{len(compartments)} compartments succeeded, "
            f"{len(all_rows)} total rows, {total_count} total count"
        )

        if failed_queries > 0:
            logger.warning(f"{failed_queries} compartments failed to query (may lack log data or access)")

        return {
            "columns": all_columns,
            "rows": all_rows,
            "total_count": total_count,
            "is_partial": is_partial,
            "_cross_compartment_query": True,
            "_compartments_queried": successful_queries,
            "_compartments_failed": failed_queries,
        }

    def _parse_query_response(self, data: Any) -> Dict[str, Any]:
        """Parse query response into a structured dictionary.

        Args:
            data: Raw response data from OCI.

        Returns:
            Parsed query results.
        """
        columns = []
        if hasattr(data, "columns") and data.columns:
            columns = [
                {
                    "name": col.display_name or col.internal_name,
                    "internal_name": col.internal_name,
                    "type": col.value_type,
                }
                for col in data.columns
            ]

        rows = []
        if hasattr(data, "items") and data.items:
            for item in data.items:
                if hasattr(item, "values"):
                    # item.values could be a list/tuple or a dict's values method
                    values = item.values
                    if callable(values):
                        # It's a method (like dict.values), call it and convert to list
                        rows.append(list(values()))
                    elif isinstance(values, (list, tuple)):
                        # It's already a list/tuple
                        rows.append(list(values))
                    else:
                        # Convert whatever it is to a list
                        rows.append([values])
                elif isinstance(item, dict):
                    rows.append(list(item.values()))

        return {
            "columns": columns,
            "rows": rows,
            "total_count": getattr(data, "total_count", len(rows)),
            "is_partial": getattr(data, "is_partial_result", False),
        }

    async def list_log_sources(self, compartment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all log sources.

        Args:
            compartment_id: Optional compartment to list sources from.

        Returns:
            List of log source dictionaries.
        """
        await self._rate_limiter.acquire()

        compartment = compartment_id or self._compartment_id

        sources = []
        response = self._la_client.list_sources(
            namespace_name=self._namespace,
            compartment_id=compartment,
        )
        sources.extend(response.data.items)

        while response.has_next_page:
            await self._rate_limiter.acquire()
            response = self._la_client.list_sources(
                namespace_name=self._namespace,
                compartment_id=compartment,
                page=response.next_page,
            )
            sources.extend(response.data.items)

        self._rate_limiter.reset()

        return [
            {
                "name": s.name,
                "display_name": getattr(s, "display_name", s.name),
                "description": getattr(s, "description", ""),
                "entity_types": self._serialize_entity_types(getattr(s, "entity_types", None)),
                "is_system": getattr(s, "is_system", False),
            }
            for s in sources
        ]

    def _serialize_entity_types(self, entity_types: Any) -> List[str]:
        """Serialize entity types to JSON-compatible list of strings.

        Args:
            entity_types: Entity types from OCI SDK (may be objects or None).

        Returns:
            List of entity type names as strings.
        """
        if entity_types is None:
            return []

        result = []
        for et in entity_types:
            if hasattr(et, "name"):
                result.append(et.name)
            elif hasattr(et, "entity_type_name"):
                result.append(et.entity_type_name)
            elif isinstance(et, str):
                result.append(et)
            else:
                result.append(str(et))
        return result

    async def list_fields(self, source_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List fields, optionally filtered by source.

        Args:
            source_name: Optional log source name to filter fields.

        Returns:
            List of field dictionaries.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.list_fields(
            namespace_name=self._namespace,
            compartment_id=self._compartment_id,
        )

        fields = response.data.items
        self._rate_limiter.reset()

        result = []
        for f in fields:
            field_dict = {
                "name": f.name,
                "display_name": getattr(f, "display_name", f.name),
                "data_type": getattr(f, "data_type", "STRING"),
                "description": getattr(f, "description", ""),
            }
            result.append(field_dict)

        return result

    async def list_entities(self, entity_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List monitored entities.

        Args:
            entity_type: Optional entity type filter.

        Returns:
            List of entity dictionaries.
        """
        await self._rate_limiter.acquire()

        kwargs = {
            "namespace_name": self._namespace,
            "compartment_id": self._compartment_id,
        }
        if entity_type:
            kwargs["entity_type_name"] = [entity_type]

        response = self._la_client.list_entities(**kwargs)
        self._rate_limiter.reset()

        return [
            {
                "name": e.name,
                "entity_type": getattr(e, "entity_type_name", ""),
                "management_agent_id": getattr(e, "management_agent_id", None),
                "lifecycle_state": getattr(e, "lifecycle_state", ""),
            }
            for e in response.data.items
        ]

    async def list_parsers(self) -> List[Dict[str, Any]]:
        """List available parsers.

        Returns:
            List of parser dictionaries.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.list_parsers(
            namespace_name=self._namespace,
            compartment_id=self._compartment_id,
        )
        self._rate_limiter.reset()

        return [
            {
                "name": p.name,
                "type": getattr(p, "type", ""),
                "description": getattr(p, "description", ""),
                "is_system": getattr(p, "is_system", False),
            }
            for p in response.data.items
        ]

    async def list_labels(self) -> List[Dict[str, Any]]:
        """List label definitions.

        Returns:
            List of label dictionaries.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.list_labels(
            namespace_name=self._namespace,
            compartment_id=self._compartment_id,
        )
        self._rate_limiter.reset()

        return [
            {
                "name": label.name,
                "display_name": getattr(label, "display_name", label.name),
                "description": getattr(label, "description", ""),
                "priority": getattr(label, "priority", ""),
            }
            for label in response.data.items
        ]

    async def list_saved_searches(self) -> List[Dict[str, Any]]:
        """List saved searches.

        Returns:
            List of saved search dictionaries.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.list_log_analytics_em_bridges(
            namespace_name=self._namespace,
            compartment_id=self._compartment_id,
        )

        # Try to get saved searches via a different API
        try:
            response = self._la_client.list_scheduled_tasks(
                namespace_name=self._namespace,
                compartment_id=self._compartment_id,
                task_type="SAVED_SEARCH",
            )
            self._rate_limiter.reset()

            return [
                {
                    "id": s.id,
                    "display_name": getattr(s, "display_name", ""),
                    "task_type": getattr(s, "task_type", ""),
                    "lifecycle_state": getattr(s, "lifecycle_state", ""),
                }
                for s in response.data.items
            ]
        except Exception:
            self._rate_limiter.reset()
            return []

    async def get_saved_search(self, saved_search_id: str) -> Dict[str, Any]:
        """Get a specific saved search.

        Args:
            saved_search_id: OCID of the saved search.

        Returns:
            Saved search details dictionary.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.get_scheduled_task(
            namespace_name=self._namespace,
            scheduled_task_id=saved_search_id,
        )
        self._rate_limiter.reset()

        data = response.data
        return {
            "id": data.id,
            "display_name": getattr(data, "display_name", ""),
            "query": getattr(data, "saved_search_query", ""),
            "lifecycle_state": getattr(data, "lifecycle_state", ""),
        }

    async def list_compartments(self) -> List[Dict[str, Any]]:
        """List accessible compartments.

        Returns:
            List of compartment dictionaries.
        """
        await self._rate_limiter.acquire()

        tenancy_id = self._config.get("tenancy")
        response = self._identity_client.list_compartments(
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
        )
        self._rate_limiter.reset()

        return [
            {
                "id": c.id,
                "name": c.name,
                "description": getattr(c, "description", ""),
                "lifecycle_state": c.lifecycle_state,
            }
            for c in response.data
        ]

    async def list_log_groups(self) -> List[Dict[str, Any]]:
        """List log groups.

        Returns:
            List of log group dictionaries.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.list_log_analytics_log_groups(
            namespace_name=self._namespace,
            compartment_id=self._compartment_id,
        )
        self._rate_limiter.reset()

        return [
            {
                "id": g.id,
                "display_name": getattr(g, "display_name", ""),
                "description": getattr(g, "description", ""),
                "compartment_id": g.compartment_id,
            }
            for g in response.data.items
        ]

    async def get_namespace(self) -> str:
        """Get the Log Analytics namespace for the tenancy.

        Returns:
            Namespace string.
        """
        await self._rate_limiter.acquire()

        response = self._la_client.get_namespace(namespace_name=self._namespace)
        self._rate_limiter.reset()

        return response.data.namespace_name
