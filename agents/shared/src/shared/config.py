"""Shared configuration utilities."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


def load_toml(path: Path) -> dict:
    """Load a TOML file and return its contents as a dict."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_toml_string(text: str) -> dict:
    """Parse a TOML string and return its contents as a dict."""
    return tomllib.loads(text)
