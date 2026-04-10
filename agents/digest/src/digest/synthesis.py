"""Claude synthesis step: raw items -> narrative brief."""

from __future__ import annotations

from anthropic import Anthropic

from digest.models import Item

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """You are a research analyst producing activity digests on technical topics.

Given a ranked list of items from multiple platforms (Hacker News, GitHub, Reddit, etc.),
write a concise narrative brief that:

1. Opens with 2-3 sentences capturing the dominant themes
2. Groups related items into 3-6 thematic sections with short headings
3. Cites specific items using markdown links to their URLs
4. Notes contrasts, debates, or shifts in sentiment where visible
5. Ends with a "What's new" section highlighting the most recent or accelerating developments

Write in plain prose, not bullet points. Be specific. Prefer concrete claims backed by
citations over generic summaries. Do not editorialize or recommend actions."""


def synthesize(topic: str, days: int, items: list[Item]) -> str:
    """Call Claude to turn ranked items into a narrative brief."""
    client = Anthropic()

    items_md = "\n".join(
        f"- [{item.source}] {item.title} "
        f"({item.engagement} engagement, {item.timestamp.date().isoformat()}) "
        f"- {item.url}"
        for item in items
    )

    user_prompt = (
        f"Topic: {topic}\n"
        f"Window: last {days} days\n"
        f"Items ({len(items)}):\n\n{items_md}\n\n"
        f"Write the digest brief now."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()
