"""Platform adapters for fetching items."""

from digest.adapters.base import Adapter
from digest.adapters.ethresearch import EthResearchAdapter
from digest.adapters.github import GitHubAdapter
from digest.adapters.hackernews import HackerNewsAdapter
from digest.adapters.packages import PackagesAdapter
from digest.adapters.reddit import RedditAdapter
from digest.adapters.snapshot import SnapshotAdapter
from digest.adapters.youtube import YouTubeAdapter

ADAPTERS: dict[str, type[Adapter]] = {
    "hn": HackerNewsAdapter,
    "github": GitHubAdapter,
    "reddit": RedditAdapter,
    "youtube": YouTubeAdapter,
    "snapshot": SnapshotAdapter,
    "ethresearch": EthResearchAdapter,
    "packages": PackagesAdapter,
}


def get_adapter(name: str) -> Adapter:
    if name not in ADAPTERS:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(ADAPTERS)}")
    return ADAPTERS[name]()
