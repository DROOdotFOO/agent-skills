"""Platform adapters for fetching items."""

from digest.adapters.base import Adapter
from digest.adapters.github import GitHubAdapter
from digest.adapters.hackernews import HackerNewsAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    "hn": HackerNewsAdapter,
    "github": GitHubAdapter,
}


def get_adapter(name: str) -> Adapter:
    if name not in ADAPTERS:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(ADAPTERS)}")
    return ADAPTERS[name]()
