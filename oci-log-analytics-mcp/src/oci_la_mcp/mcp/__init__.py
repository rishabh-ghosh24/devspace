"""MCP protocol layer for Log Analytics."""

from .tools import get_tools
from .resources import get_resources, get_query_templates, get_syntax_guide
from .handlers import MCPHandlers

__all__ = [
    "get_tools",
    "get_resources",
    "get_query_templates",
    "get_syntax_guide",
    "MCPHandlers",
]
