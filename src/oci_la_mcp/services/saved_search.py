"""Saved search operations service."""

from typing import Optional, List, Dict, Any

from ..oci_client.client import OCILogAnalyticsClient
from ..cache.manager import CacheManager


class SavedSearchService:
    """Service for managing saved searches."""

    def __init__(self, oci_client: OCILogAnalyticsClient, cache: CacheManager):
        """Initialize saved search service.

        Args:
            oci_client: OCI Log Analytics client.
            cache: Cache manager.
        """
        self.oci_client = oci_client
        self.cache = cache

    async def list_searches(self) -> List[Dict[str, Any]]:
        """List all saved searches.

        Returns:
            List of saved search dictionaries.
        """
        cache_key = "saved_searches"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        searches = await self.oci_client.list_saved_searches()
        self.cache.set(cache_key, searches)
        return searches

    async def get_search_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a saved search by display name.

        Args:
            name: Display name of the saved search.

        Returns:
            Saved search dictionary if found, None otherwise.
        """
        searches = await self.list_searches()
        for search in searches:
            if search.get("display_name", "").lower() == name.lower():
                return await self.get_search_by_id(search["id"])
        return None

    async def get_search_by_id(self, search_id: str) -> Dict[str, Any]:
        """Get a saved search by ID.

        Args:
            search_id: OCID of the saved search.

        Returns:
            Saved search details.
        """
        cache_key = f"saved_search:{search_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        search = await self.oci_client.get_saved_search(search_id)
        self.cache.set(cache_key, search)
        return search

    async def find_searches(
        self, keyword: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find saved searches matching a keyword.

        Args:
            keyword: Optional keyword to filter by.
            limit: Maximum number of results.

        Returns:
            List of matching saved searches.
        """
        searches = await self.list_searches()

        if keyword:
            keyword_lower = keyword.lower()
            searches = [
                s
                for s in searches
                if keyword_lower in s.get("display_name", "").lower()
            ]

        return searches[:limit]
