"""Output formatters for digest results."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown

from digest.models import DigestResult


def to_markdown(result: DigestResult) -> str:
    header = (
        f"# Digest: {result.topic}\n\n"
        f"**Window:** last {result.days} days  \n"
        f"**Items:** {len(result.items)}  \n"
        f"**Generated:** {result.generated_at.isoformat()}\n\n"
        f"---\n\n"
    )

    body = result.narrative + "\n\n---\n\n## Sources\n\n"
    for idx, item in enumerate(result.items, 1):
        body += (
            f"{idx}. [{item.source}] [{item.title}]({item.url}) "
            f"-- {item.engagement} engagement\n"
        )
    return header + body


def print_terminal(result: DigestResult) -> None:
    console = Console()
    console.print(Markdown(to_markdown(result)))
