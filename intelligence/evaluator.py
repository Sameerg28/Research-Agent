from __future__ import annotations


class ResearchEvaluator:
    def evaluate(
        self,
        *,
        query: str,
        insights: list[str],
        sources: list[dict[str, str]],
        previous_insights: list[str] | None = None,
    ) -> dict:
        previous_insights = previous_insights or []

        relevance = self._score_relevance(query, insights)
        novelty = self._score_novelty(insights, previous_insights)
        confidence = self._score_confidence(insights, sources)
        source_quality = self._score_source_quality(sources)

        score = round(
            relevance * 0.35
            + novelty * 0.25
            + confidence * 0.2
            + source_quality * 0.2,
            3,
        )
        reason = (
            f"relevance={relevance:.2f}, novelty={novelty:.2f}, "
            f"confidence={confidence:.2f}, source_quality={source_quality:.2f}"
        )
        return {"score": score, "reason": reason}

    def _score_relevance(self, query: str, insights: list[str]) -> float:
        if not insights:
            return 0.0
        query_terms = {term for term in query.lower().split() if len(term) > 3}
        if not query_terms:
            return 0.5
        matches = 0
        for insight in insights:
            insight_terms = set(insight.lower().split())
            if query_terms & insight_terms:
                matches += 1
        return min(matches / max(len(insights), 1) + 0.2, 1.0)

    def _score_novelty(self, insights: list[str], previous_insights: list[str]) -> float:
        if not insights:
            return 0.0
        previous = {item.lower() for item in previous_insights}
        new_items = [item for item in insights if item.lower() not in previous]
        return min(len(new_items) / max(len(insights), 1) + 0.2, 1.0)

    def _score_confidence(self, insights: list[str], sources: list[dict[str, str]]) -> float:
        if not insights:
            return 0.0
        source_factor = min(len(sources) / 3, 1.0)
        density_factor = min(sum(1 for item in insights if len(item.split()) >= 10) / len(insights), 1.0)
        return round((source_factor * 0.6) + (density_factor * 0.4), 3)

    def _score_source_quality(self, sources: list[dict[str, str]]) -> float:
        if not sources:
            return 0.0
        quality = 0.0
        for source in sources:
            if source.get("url"):
                quality += 0.35
            if source.get("year"):
                quality += 0.25
            if source.get("source"):
                quality += 0.2
            if source.get("snippet"):
                quality += 0.2
        return min(quality / len(sources), 1.0)
