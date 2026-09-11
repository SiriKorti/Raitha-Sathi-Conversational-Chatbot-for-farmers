"""
metadata_filter.py — Metadata-Based Result Filtering

After FAISS retrieval returns top-k candidates by vector similarity,
this module applies additional metadata filters to refine results.

Filters can narrow results by:
- crop_name (e.g. only tomato entries)
- season    (e.g. kharif, rabi)
- region    (e.g. North Karnataka, Coastal)
- language  (e.g. kn, en)
- topic     (e.g. pest, disease, fertilizer)

Usage:
    from app.rag.metadata_filter import MetadataFilter
    mf = MetadataFilter()
    filtered = mf.filter(results, crop_name="ಟೊಮ್ಯಾಟೊ", topic="ರೋಗ")
"""

from app.utils.logger import logger


class MetadataFilter:
    """
    Filters FAISS retrieval results by dataset metadata fields.

    Filtering is soft — if strict filtering reduces results below
    min_results, the filter is relaxed to preserve recall.
    """

    def filter(
        self,
        results: list[dict],
        crop_name: str = None,
        season: str = None,
        region: str = None,
        language: str = None,
        topic: str = None,
        min_results: int = 2,
    ) -> list[dict]:
        """
        Apply metadata filters to a list of FAISS results.

        Args:
            results:     List of retrieved entry dicts (from FAISSIndex.search)
            crop_name:   Filter by crop name (case-insensitive partial match)
            season:      Filter by season
            region:      Filter by region
            language:    Filter by language code (e.g. "kn")
            topic:       Filter by topic (case-insensitive partial match)
            min_results: If filtered count < min_results, return all original results

        Returns:
            Filtered list of entry dicts
        """
        if not results:
            return results

        # Build the list of active filters
        filters = {}
        if crop_name:
            filters["crop_name"] = crop_name.lower()
        if season:
            filters["season"] = season.lower()
        if region:
            filters["region"] = region.lower()
        if language:
            filters["language"] = language.lower()
        if topic:
            filters["topic"] = topic.lower()

        if not filters:
            return results  # No filters — return as-is

        filtered = [
            entry for entry in results
            if self._matches_filters(entry, filters)
        ]

        # We no longer soft-fallback because returning results for the WRONG crop
        # is a fatal error in agricultural advice. If filtered is empty, it means
        # we do not have data for this crop, and we should return an empty list.
        
        logger.debug(
            "Metadata filter applied: {before} → {after} results",
            before=len(results), after=len(filtered)
        )
        return filtered

    def _matches_filters(self, entry: dict, filters: dict) -> bool:
        """
        Check if a single entry matches all active filters.

        Uses exact matching for crop_name to prevent cross-crop bleed 
        (e.g., "ಜೋಳ" bleeding into "ಮೆಕ್ಕೆಜೋಳ").
        """
        for field, value in filters.items():
            entry_value = str(entry.get(field, "")).lower()

            if field == "topic":
                if not entry_value:
                    return False
                # Partial match for topic lookup
                if value not in entry_value and entry_value not in value:
                    return False
            else:
                # Flexible match for crop_name: DB stores "ಅರಿಶಿನ (Turmeric)"
                # but query extracts "ಅರಿಶಿನ". Allow prefix match.
                # Still prevents "ಜೋಳ" matching "ಮೆಕ್ಕೆಜೋಳ" via startswith check.
                if field == "crop_name":
                    if entry_value != value and not entry_value.startswith(value) and not value.startswith(entry_value):
                        return False
                elif entry_value != value:
                    return False

        return True
