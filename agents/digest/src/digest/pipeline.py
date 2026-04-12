"""Top-level digest pipeline: expand -> fetch -> dedupe -> rank -> synthesize."""

from __future__ import annotations

from digest.adapters import get_adapter
from digest.dedup import dedupe
from digest.expansion import ExpandedQuery, expand, literal
from digest.hooks import post_tool_use, sanitize_context
from digest.models import DigestRequest, DigestResult, Item
from digest.ranking import rank
from digest.synthesis import synthesize


def run(
    request: DigestRequest,
    *,
    synthesize_narrative: bool = True,
    use_expansion: bool = True,
    store_memory: bool = False,
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

    # PostToolUse: strip items with injection patterns before synthesis
    raw_items = post_tool_use(raw_items)

    deduped = dedupe(raw_items)
    ranked = rank(deduped, limit=request.max_items_per_platform, topic=request.topic)
    # Pull historical context from recall if available
    recall_context = ""
    try:
        from digest.recall_bridge import fetch_from_recall, format_recall_context

        entries = fetch_from_recall(request.topic)
        recall_context = sanitize_context(format_recall_context(entries))
    except Exception:
        pass

    narrative = (
        synthesize(request.topic, request.days, ranked, recall_context=recall_context)
        if synthesize_narrative
        else "_Synthesis skipped (--no-synthesis). Ranked items below._"
    )

    result = DigestResult(
        topic=request.topic,
        days=request.days,
        items=ranked,
        narrative=narrative,
    )

    if store_memory:
        from digest.memory import FeedMemory

        mem = FeedMemory()
        mem.store(result)
        mem.close()

        # Update source credibility scores based on item persistence
        try:
            from digest.source_tracker import SourceTracker

            tracker = SourceTracker()
            tracker.update_scores(request.topic)
            tracker.close()
        except Exception:
            pass

        # Also store highlights to recall
        try:
            from digest.recall_bridge import recall_available, store_to_recall

            if recall_available():
                store_to_recall(result)
        except Exception:
            pass

    return result, query
