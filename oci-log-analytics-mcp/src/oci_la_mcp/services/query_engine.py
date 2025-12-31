"""Query execution service for Log Analytics."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..oci_client.client import OCILogAnalyticsClient
from ..cache.manager import CacheManager
from ..logging.query_logger import QueryLogger
from ..utils.time_parser import parse_time_range


class QueryEngine:
    """Handles query execution and result processing."""

    def __init__(
        self,
        oci_client: OCILogAnalyticsClient,
        cache: CacheManager,
        logger: QueryLogger,
    ):
        """Initialize query engine.

        Args:
            oci_client: OCI Log Analytics client.
            cache: Cache manager for results.
            logger: Query logger for audit.
        """
        self.oci_client = oci_client
        self.cache = cache
        self.logger = logger

    async def execute(
        self,
        query: str,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        time_range: Optional[str] = None,
        max_results: Optional[int] = None,
        include_subcompartments: bool = False,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Execute a Log Analytics query.

        Args:
            query: The Log Analytics query string.
            time_start: Absolute start time (ISO 8601).
            time_end: Absolute end time (ISO 8601).
            time_range: Relative time range (e.g., 'last_1_hour').
            max_results: Maximum number of results to return.
            include_subcompartments: If True, include logs from sub-compartments.
            use_cache: Whether to use cached results.

        Returns:
            Dictionary containing query results and metadata.
        """
        # Parse time parameters
        start, end = parse_time_range(time_start, time_end, time_range)

        # Check cache (include subcompartments flag in cache key)
        cache_key = self._make_cache_key(query, start, end, include_subcompartments)
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                return {"source": "cache", "data": cached}

        # Execute query
        start_time = datetime.now()
        try:
            result = await self.oci_client.query(
                query_string=query,
                time_start=start.isoformat(),
                time_end=end.isoformat(),
                max_results=max_results,
                include_subcompartments=include_subcompartments,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Cache result
            if use_cache:
                self.cache.set(cache_key, result)

            # Log query
            self.logger.log_query(
                query=query,
                time_start=start,
                time_end=end,
                execution_time=execution_time,
                result_count=len(result.get("rows", [])),
                success=True,
            )

            return {"source": "live", "data": result}

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.log_query(
                query=query,
                time_start=start,
                time_end=end,
                execution_time=execution_time,
                result_count=0,
                success=False,
                error=str(e),
            )
            raise

    async def execute_batch(
        self,
        queries: List[Dict[str, Any]],
        include_subcompartments: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute multiple queries concurrently.

        Args:
            queries: List of query dictionaries with query parameters.
            include_subcompartments: If True, include logs from sub-compartments.

        Returns:
            List of result dictionaries.
        """
        tasks = [
            self.execute(
                query=q["query"],
                time_start=q.get("time_start"),
                time_end=q.get("time_end"),
                time_range=q.get("time_range"),
                max_results=q.get("max_results"),
                include_subcompartments=q.get("include_subcompartments", include_subcompartments),
            )
            for q in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            {"success": True, "result": r}
            if not isinstance(r, Exception)
            else {"success": False, "error": str(r)}
            for r in results
        ]

    def _make_cache_key(
        self,
        query: str,
        start: datetime,
        end: datetime,
        include_subcompartments: bool = False,
    ) -> str:
        """Generate cache key for a query.

        Args:
            query: The query string.
            start: Start time.
            end: End time.
            include_subcompartments: Whether sub-compartments are included.

        Returns:
            Cache key string.
        """
        sub_flag = "sub" if include_subcompartments else "nosub"
        return f"{query}:{start.isoformat()}:{end.isoformat()}:{sub_flag}"
