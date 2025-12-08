"""Custom page registry to track decorated pages.

This module provides a custom page registry to replace the deprecated
get_decorated_pages() function from Reflex.
"""

from typing import Dict, List

# Global registry to store page information
_pages: List[Dict[str, str]] = []


def register_page(route: str, title: str | None = None, description: str | None = None):
    """Register a page in the registry.

    Args:
        route: The route of the page.
        title: The title of the page.
        description: The description of the page.
    """
    page_info = {
        "route": route,
        "title": title or route.strip("/").capitalize(),
        "description": description or "",
    }
    # Avoid duplicates
    existing_routes = {page["route"] for page in _pages}
    if route not in existing_routes:
        _pages.append(page_info)


def get_pages() -> List[Dict[str, str]]:
    """Get all registered pages.

    Returns:
        A list of dictionaries containing page information (route, title, description).
    """
    return _pages.copy()


def clear_registry():
    """Clear the page registry. Useful for testing."""
    _pages.clear()

