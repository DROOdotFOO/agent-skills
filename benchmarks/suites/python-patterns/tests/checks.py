"""Shared AST-based checks for Python pattern detection."""

from __future__ import annotations

import ast
import re


def parse_code(code: str) -> ast.Module | None:
    """Parse Python code, returning AST or None on syntax error."""
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def has_import(code: str, module: str) -> bool:
    """Check if code imports the given module."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == module or alias.name.startswith(f"{module}."):
                    return True
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == module or node.module.startswith(f"{module}.")):
                return True
    return False


def has_no_import(code: str, module: str) -> bool:
    """Check that code does NOT import the given module."""
    return not has_import(code, module)


def function_has_return_annotation(code: str, func_name: str) -> bool:
    """Check if a specific function has a return type annotation."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name and node.returns is not None:
                return True
    return False


def function_has_param_annotations(code: str, func_name: str) -> bool:
    """Check if a function has type annotations on all non-self parameters.

    Returns True for functions with zero parameters (nothing to annotate).
    """
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name != func_name:
                continue
            args = node.args
            all_args = args.args + args.posonlyargs + args.kwonlyargs
            non_self_args = [a for a in all_args if a.arg not in ("self", "cls")]
            if not non_self_args:
                return True  # no params to annotate
            for arg in non_self_args:
                if arg.annotation is None:
                    return False
            return True
    return False


def has_keyword_only_arg(code: str, func_name: str, arg_name: str) -> bool:
    """Check if a function has a specific keyword-only argument."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                for arg in node.args.kwonlyargs:
                    if arg.arg == arg_name:
                        return True
    return False


def uses_list_comprehension(code: str) -> bool:
    """Check if code contains a list comprehension."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ListComp):
            return True
    return False


def uses_with_statement(code: str) -> bool:
    """Check if code contains a with statement."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            return True
    return False


def has_map_filter_lambda(code: str) -> bool:
    """Check if code uses map() or filter() with lambda."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("map", "filter"):
                if any(isinstance(arg, ast.Lambda) for arg in node.args):
                    return True
    return False


def has_manual_close_call(code: str) -> bool:
    """Check if code calls .close() outside of context manager definitions.

    .close() inside a @contextmanager-decorated function's finally block
    is correct usage, not "manual" cleanup.
    """
    tree = parse_code(code)
    if tree is None:
        return False

    # Find functions decorated with @contextmanager
    cm_func_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                dec_name = ""
                if isinstance(dec, ast.Name):
                    dec_name = dec.id
                elif isinstance(dec, ast.Attribute):
                    dec_name = dec.attr
                if dec_name == "contextmanager":
                    cm_func_names.add(node.name)

    # Check for .close() calls NOT inside context manager functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in cm_func_names:
                continue  # skip context manager bodies
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute) and child.func.attr == "close":
                        return True
    return False


def uses_pydantic_basemodel(code: str) -> bool:
    """Check if code defines a class inheriting from BaseModel."""
    tree = parse_code(code)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseModel":
                    return True
                if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
                    return True
    return False


def uses_pydantic_field(code: str) -> bool:
    """Check if code uses Field() with constraints (ge, le, gt, lt)."""
    source = code.lower()
    return bool(re.search(r"field\s*\(.*\b(ge|le|gt|lt)\s*=", source))
