from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request

from config import SEARCH_TIMEOUT
from interfaces.search import SearchInterface

logger = logging.getLogger(__name__)

OPENALEX_URL = "https://api.openalex.org/works"


class OpenAlexSearch(SearchInterface):
    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        if not query.strip() or limit <= 0:
            return []

        params = urllib.parse.urlencode(
            {
                "search": query,
                "per-page": min(limit, 10),
            }
        )
        request_url = f"{OPENALEX_URL}?{params}"

        try:
            with urllib.request.urlopen(request_url, timeout=SEARCH_TIMEOUT) as response:
                payload = json.load(response)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("OpenAlex search failed for '%s': %s", query, exc)
            return []

        results: list[dict[str, str]] = []
        for item in payload.get("results", []):
            title = str(item.get("display_name") or item.get("title") or "").strip()
            primary_location = item.get("primary_location") or {}
            url = str(
                primary_location.get("landing_page_url")
                or item.get("doi")
                or item.get("id")
                or ""
            ).strip()
            if not title and not url:
                continue

            authors = ", ".join(
                authorship.get("author", {}).get("display_name", "").strip()
                for authorship in item.get("authorships", [])
                if authorship.get("author", {}).get("display_name")
            )
            source = primary_location.get("source") or {}
            venue = str(
                source.get("display_name") or primary_location.get("raw_source_name") or ""
            ).strip()
            year = str(item.get("publication_year") or "").strip()
            abstract = self._reconstruct_abstract(item.get("abstract_inverted_index") or {})

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": self._build_snippet(abstract, venue, authors, year),
                    "source": "OpenAlex",
                    "year": year,
                }
            )

        logger.info("Search '%s' returned %s scholarly results", query, len(results))
        return results

    def _build_snippet(self, abstract: str, venue: str, authors: str, year: str) -> str:
        parts = []
        if venue:
            parts.append(f"Venue: {venue}")
        if year:
            parts.append(f"Year: {year}")
        if authors:
            parts.append(f"Authors: {authors}")
        if abstract:
            parts.append(abstract[:500])
        return " | ".join(parts)

    def _reconstruct_abstract(self, abstract_inverted_index: dict) -> str:
        if not abstract_inverted_index:
            return ""

        positions: dict[int, str] = {}
        for word, indexes in abstract_inverted_index.items():
            for index in indexes:
                positions[index] = word

        return " ".join(positions[index] for index in sorted(positions))
