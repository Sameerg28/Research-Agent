from __future__ import annotations

from interfaces.search import SearchInterface
from interfaces.tool import ToolInterface


class WebSearchTool(ToolInterface):
    def __init__(self, search: SearchInterface) -> None:
        self._search = search

    def execute(self, input_data: dict | str) -> list[dict[str, str]]:
        if isinstance(input_data, dict):
            query = str(input_data.get("query", "")).strip()
            limit = int(input_data.get("limit", 5))
        else:
            query = str(input_data).strip()
            limit = 5
        return self._search.search(query, limit=limit)
