"""Check that generated code has proper type annotations."""

from __future__ import annotations

from .checks import (
    function_has_param_annotations,
    function_has_return_annotation,
    has_keyword_only_arg,
)


def evaluate(code: str) -> dict[str, bool]:
    return {
        "has_return_annotation": function_has_return_annotation(code, "fetch_user"),
        "has_param_annotations": function_has_param_annotations(code, "fetch_user"),
        "uses_keyword_only": has_keyword_only_arg(code, "fetch_user", "include_posts"),
    }
