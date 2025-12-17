"""Parsers for sphinx_hcd.

Contains parsing logic for:
- gherkin.py: Feature file parsing (.feature files)
- yaml.py: App and integration manifest parsing
- ast.py: Python code introspection for accelerators
"""

from .ast import (
    parse_bounded_context,
    parse_module_docstring,
    parse_python_classes,
    scan_bounded_contexts,
)
from .gherkin import (
    ParsedFeature,
    parse_feature_content,
    parse_feature_file,
    scan_feature_directory,
)
from .yaml import (
    parse_app_manifest,
    parse_integration_manifest,
    parse_manifest_content,
    scan_app_manifests,
    scan_integration_manifests,
)

__all__ = [
    # AST - Python introspection
    "parse_bounded_context",
    "parse_module_docstring",
    "parse_python_classes",
    "scan_bounded_contexts",
    # Gherkin
    "ParsedFeature",
    "parse_feature_content",
    "parse_feature_file",
    "scan_feature_directory",
    # YAML - Apps
    "parse_app_manifest",
    "scan_app_manifests",
    # YAML - Integrations
    "parse_integration_manifest",
    "scan_integration_manifests",
    # YAML - Common
    "parse_manifest_content",
]
