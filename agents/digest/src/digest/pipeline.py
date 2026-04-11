"""Top-level digest pipeline: expand -> fetch -> dedupe -> rank -> synthesize."""

from __future__ import annotations

from digest.adapters import get_adapter
from digest.dedup import dedupe
from digest.expansion import ExpandedQuery, expand, literal
from digest.models import DigestRequest, DigestResult, Item
from digest.ranking import rank
from digest.synthesis import synthesize


def run(
    request: DigestRequest,
    *,
    synthesize_narrative: bool = True,
    use_expansion: bool = True,
) -> tuple[DigestResult, ExpandedQuery]:
    """Run the full digest pipeline.

    Returns the result plus the expanded query that was used (so the CLI can
    show the user which rules fired).
    """
    query = expand(request.topic) if use_expansion else literal(request.topic)

    raw_items: list[Item] = []
    for platform in request.platforms:
        adapter = get_adapter(platform)
        raw_items.extend(adapter.fetch(query, request.days, request.max_items_per_platform))

    deduped = dedupe(raw_items)
    ranked = rank(deduped, limit=request.max_items_per_platform)
    narrative = (
        synthesize(request.topic, request.days, ranked)
        if synthesize_narrative
        else "_Synthesis skipped (--no-synthesis). Ranked items below._"
    )

    result = DigestResult(
        topic=request.topic,
        days=request.days,
        items=ranked,
        narrative=narrative,
    )
    return result, query
