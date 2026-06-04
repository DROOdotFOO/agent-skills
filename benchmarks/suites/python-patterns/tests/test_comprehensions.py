"""Check that generated code uses comprehensions over map/filter."""

from __future__ import annotations

from .checks import (
    function_has_return_annotation,
    has_map_filter_lambda,
    uses_list_comprehension,
)


def evaluate(code: str) -> dict[str, bool]:
    return {
        "uses_comprehension": uses_list_comprehension(code),
        "no_map_filter_lambda": not has_map_filter_lambda(code),
        "has_type_hints": function_has_return_annotation(code, "process_orders"),
    }
