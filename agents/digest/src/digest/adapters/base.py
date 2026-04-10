"""Base adapter protocol."""

from __future__ import annotations

from typing import Protocol

from digest.expansion import ExpandedQuery
from digest.models import Item


class Adapter(Protocol):
    """Platform adapter interface.

    Implementations fetch items for a structured query over a time window.
    The query carries both the original topic and expansion hints (terms,
    qualifiers, topics) so adapters can route to high-signal sources.
    """

    name: str

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch items matching the expanded query within the last `days` days."""
        ...
