"""Parsers for sphinx_hcd.

Contains parsing logic for:
- gherkin.py: Feature file parsing (.feature files)
- yaml.py: App and integration manifest parsing
- ast.py: Python code introspection for accelerators
- rst.py: RST directive parsing for Epic, Journey, Accelerator
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
from .rst import (
    ParsedAccelerator,
    ParsedEpic,
    ParsedJourney,
    parse_accelerator_content,
    parse_accelerator_file,
    parse_epic_content,
    parse_epic_file,
    parse_journey_content,
    parse_journey_file,
    scan_accelerator_directory,
    scan_epic_directory,
    scan_journey_directory,
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
    # RST - Epic
    "ParsedEpic",
    "parse_epic_content",
    "parse_epic_file",
    "scan_epic_directory",
    # RST - Journey
    "ParsedJourney",
    "parse_journey_content",
    "parse_journey_file",
    "scan_journey_directory",
    # RST - Accelerator
    "ParsedAccelerator",
    "parse_accelerator_content",
    "parse_accelerator_file",
    "scan_accelerator_directory",
    # YAML - Apps
    "parse_app_manifest",
    "scan_app_manifests",
    # YAML - Integrations
    "parse_integration_manifest",
    "scan_integration_manifests",
    # YAML - Common
    "parse_manifest_content",
]
