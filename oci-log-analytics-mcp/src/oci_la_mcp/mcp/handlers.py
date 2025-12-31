"""MCP request handlers for tool and resource operations."""

import json
import logging
from typing import Any, Dict, List, Optional

from ..services.query_engine import QueryEngine
from ..services.schema_manager import SchemaManager
from ..services.visualization import VisualizationEngine, ChartType
from ..services.query_validator import QueryValidator
from ..services.saved_search import SavedSearchService
from ..services.export import ExportService
from ..oci_client.client import OCILogAnalyticsClient
from ..cache.manager import CacheManager
from ..logging.query_logger import QueryLogger
from ..config.settings import Settings
from .resources import get_query_templates, get_syntax_guide

logger = logging.getLogger(__name__)


class MCPHandlers:
    """Handlers for MCP tool and resource requests."""

    def __init__(
        self,
        settings: Settings,
        oci_client: OCILogAnalyticsClient,
        cache: CacheManager,
        query_logger: QueryLogger,
    ):
        """Initialize MCP handlers.

        Args:
            settings: Application settings.
            oci_client: OCI Log Analytics client.
            cache: Cache manager.
            query_logger: Query logger.
        """
        self.settings = settings
        self.oci_client = oci_client
        self.cache = cache
        self.query_logger = query_logger

        # Initialize services
        self.schema_manager = SchemaManager(oci_client, cache)
        self.query_engine = QueryEngine(oci_client, cache, query_logger)
        self.validator = QueryValidator(self.schema_manager)
        self.visualization = VisualizationEngine()
        self.saved_search = SavedSearchService(oci_client, cache)
        self.export_service = ExportService()

    async def handle_tool_call(
        self, name: str, arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Route tool calls to appropriate handlers.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            List of content items (text or image).
        """
        handlers = {
            # Schema exploration
            "list_log_sources": self._list_log_sources,
            "list_fields": self._list_fields,
            "list_entities": self._list_entities,
            "list_parsers": self._list_parsers,
            "list_labels": self._list_labels,
            "list_saved_searches": self._list_saved_searches,
            "list_log_groups": self._list_log_groups,
            # Query execution
            "validate_query": self._validate_query,
            "run_query": self._run_query,
            "run_saved_search": self._run_saved_search,
            "run_batch_queries": self._run_batch_queries,
            # Visualization
            "visualize": self._visualize,
            # Export
            "export_results": self._export_results,
            # Configuration
            "set_compartment": self._set_compartment,
            "set_namespace": self._set_namespace,
            "get_current_context": self._get_current_context,
            "list_compartments": self._list_compartments,
        }

        handler = handlers.get(name)
        if not handler:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]

        try:
            result = await handler(arguments)
            return result
        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [{"type": "text", "text": f"Error executing {name}: {str(e)}"}]

    async def handle_resource_read(self, uri: str) -> Any:
        """Handle resource read requests.

        Args:
            uri: Resource URI.

        Returns:
            Resource content.

        Raises:
            ValueError: If unknown resource URI.
        """
        if uri == "loganalytics://schema":
            return await self.schema_manager.get_full_schema()
        elif uri == "loganalytics://query-templates":
            return get_query_templates()
        elif uri == "loganalytics://syntax-guide":
            return get_syntax_guide()
        elif uri == "loganalytics://recent-queries":
            return self.query_logger.get_recent_queries(limit=10)
        else:
            raise ValueError(f"Unknown resource: {uri}")

    # Tool implementations

    async def _list_log_sources(self, args: Dict) -> List[Dict]:
        """List log sources."""
        sources = await self.schema_manager.get_log_sources(
            compartment_id=args.get("compartment_id")
        )
        return [{"type": "text", "text": json.dumps(sources, indent=2)}]

    async def _list_fields(self, args: Dict) -> List[Dict]:
        """List fields."""
        fields = await self.schema_manager.get_fields(source_name=args.get("source_name"))
        field_dicts = [
            {
                "name": f.name,
                "data_type": f.data_type,
                "description": f.description,
                "possible_values": f.possible_values,
                "hint": f.hint,
            }
            for f in fields
        ]
        return [{"type": "text", "text": json.dumps(field_dicts, indent=2)}]

    async def _list_entities(self, args: Dict) -> List[Dict]:
        """List entities."""
        entities = await self.schema_manager.get_entities(
            entity_type=args.get("entity_type")
        )
        return [{"type": "text", "text": json.dumps(entities, indent=2)}]

    async def _list_parsers(self, args: Dict) -> List[Dict]:
        """List parsers."""
        parsers = await self.schema_manager.get_parsers()
        return [{"type": "text", "text": json.dumps(parsers, indent=2)}]

    async def _list_labels(self, args: Dict) -> List[Dict]:
        """List labels."""
        labels = await self.schema_manager.get_labels()
        return [{"type": "text", "text": json.dumps(labels, indent=2)}]

    async def _list_saved_searches(self, args: Dict) -> List[Dict]:
        """List saved searches."""
        searches = await self.saved_search.list_searches()
        return [{"type": "text", "text": json.dumps(searches, indent=2)}]

    async def _list_log_groups(self, args: Dict) -> List[Dict]:
        """List log groups."""
        groups = await self.oci_client.list_log_groups()
        return [{"type": "text", "text": json.dumps(groups, indent=2)}]

    async def _validate_query(self, args: Dict) -> List[Dict]:
        """Validate a query."""
        result = await self.validator.validate(
            query=args["query"],
            time_start=args.get("time_start"),
            time_end=args.get("time_end"),
        )
        result_dict = {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "estimated_cost": result.estimated_cost,
            "suggested_fix": result.suggested_fix,
        }
        return [{"type": "text", "text": json.dumps(result_dict, indent=2)}]

    async def _run_query(self, args: Dict) -> List[Dict]:
        """Execute a query."""
        result = await self.query_engine.execute(
            query=args["query"],
            time_range=args.get("time_range"),
            time_start=args.get("time_start"),
            time_end=args.get("time_end"),
            max_results=args.get("max_results"),
            include_subcompartments=args.get("include_subcompartments", False),
        )
        return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

    async def _run_saved_search(self, args: Dict) -> List[Dict]:
        """Run a saved search."""
        search_id = args.get("id")
        search_name = args.get("name")

        if not search_id and search_name:
            search = await self.saved_search.get_search_by_name(search_name)
            if search:
                search_id = search.get("id")

        if not search_id:
            return [{"type": "text", "text": "Saved search not found"}]

        saved = await self.saved_search.get_search_by_id(search_id)
        query = saved.get("query", "")

        if not query:
            return [{"type": "text", "text": "Saved search has no query defined"}]

        result = await self.query_engine.execute(
            query=query, time_range="last_1_hour"
        )
        return [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]

    async def _run_batch_queries(self, args: Dict) -> List[Dict]:
        """Run batch queries."""
        results = await self.query_engine.execute_batch(
            args["queries"],
            include_subcompartments=args.get("include_subcompartments", False),
        )
        return [{"type": "text", "text": json.dumps(results, indent=2, default=str)}]

    async def _visualize(self, args: Dict) -> List[Dict]:
        """Generate visualization."""
        # Execute query first - support all time parameters
        query_result = await self.query_engine.execute(
            query=args["query"],
            time_range=args.get("time_range", "last_1_hour"),
            time_start=args.get("time_start"),
            time_end=args.get("time_end"),
            include_subcompartments=args.get("include_subcompartments", False),
        )

        # Log for debugging
        data = query_result.get("data", {})
        row_count = len(data.get("rows", []))
        col_count = len(data.get("columns", []))
        logger.info(f"Visualize: Query returned {row_count} rows, {col_count} columns")

        # Generate visualization
        chart_type = ChartType(args["chart_type"])
        viz_result = self.visualization.generate(
            data=data,
            chart_type=chart_type,
            title=args.get("title"),
        )

        return [
            {
                "type": "image",
                "data": viz_result["image_base64"],
                "mimeType": "image/png",
            },
            {
                "type": "text",
                "text": f"Raw data ({len(viz_result['raw_data'])} records): "
                + json.dumps(viz_result["raw_data"][:10], indent=2, default=str),
            },
        ]

    async def _export_results(self, args: Dict) -> List[Dict]:
        """Export query results."""
        result = await self.query_engine.execute(
            query=args["query"],
            time_range=args.get("time_range", "last_1_hour"),
            time_start=args.get("time_start"),
            time_end=args.get("time_end"),
            include_subcompartments=args.get("include_subcompartments", False),
        )

        exported = self.export_service.export(
            data=result["data"], format=args["format"]
        )
        return [{"type": "text", "text": exported}]

    async def _set_compartment(self, args: Dict) -> List[Dict]:
        """Set compartment context."""
        self.oci_client.compartment_id = args["compartment_id"]
        self.cache.clear()
        return [
            {"type": "text", "text": f"Compartment set to: {args['compartment_id']}"}
        ]

    async def _set_namespace(self, args: Dict) -> List[Dict]:
        """Set namespace context."""
        self.oci_client.namespace = args["namespace"]
        self.cache.clear()
        return [{"type": "text", "text": f"Namespace set to: {args['namespace']}"}]

    async def _get_current_context(self, args: Dict) -> List[Dict]:
        """Get current context."""
        context = {
            "namespace": self.oci_client.namespace,
            "compartment_id": self.oci_client.compartment_id,
            "default_time_range": self.settings.query.default_time_range,
            "max_results": self.settings.query.max_results,
        }
        return [{"type": "text", "text": json.dumps(context, indent=2)}]

    async def _list_compartments(self, args: Dict) -> List[Dict]:
        """List compartments."""
        compartments = await self.oci_client.list_compartments()
        return [{"type": "text", "text": json.dumps(compartments, indent=2)}]
