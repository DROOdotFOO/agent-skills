"""FastMCP server exposing digest tools for Claude Code integration."""

from __future__ import annotations

from fastmcp import FastMCP

from digest.adapters import ADAPTERS
from digest.expansion import expand
from digest.models import DigestRequest
from digest.output import to_markdown
from digest.pipeline import run


def create_server() -> FastMCP:
    """Create a FastMCP server with digest tools."""
    mcp = FastMCP(
        "digest",
        instructions=(
            "Multi-platform activity digest. Use digest_generate to fetch and synthesize "
            "activity across HN, GitHub, Reddit, YouTube, ethresear.ch, Snapshot, Polymarket, "
            "and package registries. Use digest_list_platforms to see available sources."
        ),
    )

    @mcp.tool()
    def digest_generate(
        topic: str,
        days: int = 30,
        platforms: str = "hn,github",
        max_items: int = 50,
        no_synthesis: bool = False,
        no_expansion: bool = False,
    ) -> str:
        """Generate a synthesized activity digest for a topic.

        Args:
            topic: The topic to research (e.g. "rust async runtime", "noir zk proofs")
            days: Lookback window in days (default 30)
            platforms: Comma-separated sources (see digest_list_platforms for available names)
            max_items: Max items per platform (default 50)
            no_synthesis: Skip Claude narrative synthesis, return ranked items only
            no_expansion: Skip query expansion, search topic string literally
        """
        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
        unknown = set(platform_list) - set(ADAPTERS)
        if unknown:
            return f"Unknown platforms: {', '.join(unknown)}. Available: {', '.join(ADAPTERS)}"

        request = DigestRequest(
            topic=topic,
            days=days,
            platforms=platform_list,
            max_items_per_platform=max_items,
        )

        result, query = run(
            request,
            synthesize_narrative=not no_synthesis,
            use_expansion=not no_expansion,
        )

        output = to_markdown(result)

        if query.matched_rules:
            expansion_note = f"\n\n---\nQuery expanded: terms={query.terms}"
            if query.github_qualifiers:
                expansion_note += f", github_qualifiers={query.github_qualifiers}"
            if query.github_topics:
                expansion_note += f", github_topics={query.github_topics}"
            output += expansion_note

        return output

    @mcp.tool()
    def digest_list_platforms() -> str:
        """List available platform adapters for digest generation."""
        lines = ["Available platforms:"]
        for name in ADAPTERS:
            lines.append(f"  - {name}")
        return "\n".join(lines)

    @mcp.tool()
    def digest_expand_query(topic: str) -> str:
        """Preview how a topic would be expanded into platform-specific search queries.

        Args:
            topic: The topic to expand (e.g. "noir", "elixir otp")
        """
        query = expand(topic)
        if not query.matched_rules:
            return f"No expansion rules matched '{topic}'. Would search literally."

        lines = [f"Expansion for '{topic}':"]
        lines.append(f"  Terms: {query.terms}")
        if query.hn_terms:
            lines.append(f"  HN terms: {query.hn_terms}")
        if query.github_qualifiers:
            lines.append(f"  GitHub qualifiers: {query.github_qualifiers}")
        if query.github_topics:
            lines.append(f"  GitHub topics: {query.github_topics}")
        lines.append(f"  Rules matched: {query.matched_rules}")
        return "\n".join(lines)

    @mcp.tool()
    def digest_structured_view(
        topic: str,
        view: str = "all",
        days: int = 30,
        platforms: str = "hn,github",
        max_items: int = 50,
    ) -> str:
        """Generate a digest with structured output view.

        Args:
            topic: The topic to research
            view: View type: timeline, controversy, tags, sources, or all
            days: Lookback window in days (default 30)
            platforms: Comma-separated sources
            max_items: Max items per platform (default 50)
        """
        from digest.views import (
            all_views,
            controversy_view,
            source_breakdown_view,
            tag_trends_view,
            timeline_view,
        )

        view_funcs = {
            "timeline": timeline_view,
            "controversy": controversy_view,
            "tags": tag_trends_view,
            "sources": source_breakdown_view,
            "all": all_views,
        }
        func = view_funcs.get(view)
        if func is None:
            return f"Unknown view: {view}. Choose: {', '.join(view_funcs)}"

        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
        request = DigestRequest(
            topic=topic,
            days=days,
            platforms=platform_list,
            max_items_per_platform=max_items,
        )

        result, _ = run(request, synthesize_narrative=False, use_expansion=True)
        return func(result)

    return mcp
