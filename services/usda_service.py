"""
Optional USDA FoodData Central lookup.

Used only to *suggest* a food name. The app is offline-first: if there is no
connection (or the request fails) the admin simply types the name manually.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


class USDAService:
    """Thin wrapper around the FoodData Central search endpoint."""

    def __init__(self, api_key: str = "nI2FcdapypzLIALjr1Tkl5XzuGzWT1O8G6cdhyRL") -> None:
        self.api_key = api_key

    def search(self, query: str, limit: int = 8, timeout: float = 8.0) -> list[str]:
        """Return a list of food description strings for *query*.

        Raises :class:`RuntimeError` with a readable message on any failure so
        the caller can show it in a snackbar.
        """
        query = query.strip()
        if not query:
            return []

        params = urllib.parse.urlencode(
            {"query": query, "pageSize": limit, "api_key": self.api_key}
        )
        request = urllib.request.Request(
            f"{API_URL}?{params}", headers={"Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"USDA lookup failed: {exc}") from exc

        suggestions: list[str] = []
        for food in payload.get("foods", []):
            description = (food.get("description") or "").strip()
            if description and description not in suggestions:
                suggestions.append(description.title())
        return suggestions
