"""Check that generated code uses pydantic for config validation."""

from __future__ import annotations

from .checks import (
    function_has_return_annotation,
    uses_pydantic_basemodel,
    uses_pydantic_field,
)


def evaluate(code: str) -> dict[str, bool]:
    return {
        "uses_pydantic": uses_pydantic_basemodel(code),
        "has_field_constraints": uses_pydantic_field(code),
        "has_type_hints": function_has_return_annotation(code, "load_config"),
    }
