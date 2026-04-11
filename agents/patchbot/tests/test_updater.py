"""Tests for patchbot outdated output parsing."""

from __future__ import annotations

from patchbot.models import Ecosystem
from patchbot.updater import _parse_outdated


# --- npm outdated ---


def test_parse_npm_outdated():
    output = """Package  Current  Wanted  Latest  Location
express    4.18.2  4.18.2  4.19.2  node_modules/express
lodash     4.17.20 4.17.21 4.17.21 node_modules/lodash
"""
    deps = _parse_outdated(output, Ecosystem.NODE)
    assert len(deps) == 2
    assert deps[0].name == "express"
    assert deps[0].current_version == "4.18.2"
    assert deps[0].latest_version == "4.18.2"
    assert deps[1].name == "lodash"


# --- pip list --outdated ---


def test_parse_pip_outdated():
    output = """Package    Version Latest Type
---------- ------- ------ -----
requests   2.28.0  2.31.0 wheel
setuptools 67.6.1  69.0.2 wheel
"""
    deps = _parse_outdated(output, Ecosystem.PYTHON)
    assert len(deps) == 2
    assert deps[0].name == "requests"
    assert deps[0].current_version == "2.28.0"
    assert deps[0].latest_version == "2.31.0"


# --- cargo outdated ---


def test_parse_cargo_outdated():
    output = """Name     Project  Compat  Latest  Kind
----     -------  ------  ------  ----
serde    1.0.190  1.0.195 1.0.195 Normal
tokio    1.34.0   1.36.0  1.36.0  Normal
"""
    deps = _parse_outdated(output, Ecosystem.RUST)
    assert len(deps) == 2
    assert deps[0].name == "serde"


# --- Edge cases ---


def test_parse_empty_output():
    assert _parse_outdated("", Ecosystem.NODE) == []


def test_parse_header_only():
    output = "Package  Current  Wanted  Latest\n"
    assert _parse_outdated(output, Ecosystem.NODE) == []


def test_parse_skips_separator_lines():
    output = """Name     Version
----     -------
=============================
foo      1.0.0   2.0.0
"""
    deps = _parse_outdated(output, Ecosystem.PYTHON)
    assert len(deps) == 1
    assert deps[0].name == "foo"


def test_parse_skips_lines_without_version():
    output = """some-header without versions
foo 1.0.0 2.0.0
bar no-version-here
"""
    deps = _parse_outdated(output, Ecosystem.NODE)
    assert len(deps) == 1
    assert deps[0].name == "foo"


def test_parse_two_column_no_latest():
    output = "mypackage 3.2.1\n"
    deps = _parse_outdated(output, Ecosystem.PYTHON)
    assert len(deps) == 1
    assert deps[0].latest_version is None
