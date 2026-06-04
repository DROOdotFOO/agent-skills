"""Check that generated code uses context managers for resource cleanup."""

from __future__ import annotations

from .checks import (
    function_has_return_annotation,
    has_manual_close_call,
    uses_with_statement,
)


def evaluate(code: str) -> dict[str, bool]:
    return {
        "uses_with_statement": uses_with_statement(code),
        "no_manual_close": not has_manual_close_call(code),
        "has_type_hints": function_has_return_annotation(code, "export_report"),
    }
