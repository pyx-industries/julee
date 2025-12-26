"""Code parsers for introspection.

AST-based parsers for extracting class and module information from Python source.

Note: Imports are done lazily to avoid circular imports. Import directly from
submodules:
- julee.core.parsers.ast for class/module parsing
- julee.core.parsers.imports for import analysis
"""
