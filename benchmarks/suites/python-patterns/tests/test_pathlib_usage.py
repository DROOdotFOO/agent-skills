"""Check that generated code uses pathlib instead of os.path."""

from __future__ import annotations

from .checks import (
    function_has_param_annotations,
    function_has_return_annotation,
    has_import,
    has_no_import,
)


def evaluate(code: str) -> dict[str, bool]:
    return {
        "uses_pathlib": has_import(code, "pathlib"),
        "no_os_path": has_no_import(code, "os") and has_no_import(code, "os.path"),
        "has_type_hints": (
            function_has_return_annotation(code, "find_config")
            and function_has_param_annotations(code, "find_config")
            if "def find_config" in code
            else function_has_return_annotation(code, "find_config")
        ),
    }
