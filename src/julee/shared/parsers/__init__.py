"""Code parsers for introspection.

AST-based parsers for extracting class and module information from Python source.

Note: Imports are done lazily to avoid circular imports. Import directly from
submodules:
- julee.shared.parsers.ast for class/module parsing
- julee.shared.parsers.imports for import analysis
"""


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name in (
        "parse_bounded_context",
        "parse_module_docstring",
        "parse_python_classes",
        "parse_python_classes_from_file",
        "scan_bounded_contexts",
    ):
        from julee.shared.parsers import ast

        return getattr(ast, name)
    if name in ("classify_import_layer", "extract_imports", "ImportInfo"):
        from julee.shared.parsers import imports

        return getattr(imports, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # ast module
    "parse_bounded_context",
    "parse_module_docstring",
    "parse_python_classes",
    "parse_python_classes_from_file",
    "scan_bounded_contexts",
    # imports module
    "classify_import_layer",
    "extract_imports",
    "ImportInfo",
]
