"""Meta-test ensuring doctrine coverage for all entities.

This test ensures the 1:1 mapping between domain/models/ entities and
doctrine/ test files is maintained. It catches:
1. New entities added without corresponding doctrine tests
2. Orphan doctrine tests without corresponding entities
"""

from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "entities"
DOCTRINE_DIR = Path(__file__).parent

# Supporting models that don't need their own doctrine test files.
# These are either:
# - Part of another entity (e.g., StructuralMarkers is part of BoundedContext)
# - Generic base classes (e.g., ClassInfo is superseded by specific types)
# - Infrastructure models (e.g., EvaluationResult is for semantic evaluation)
# - Tested via consolidated doctrine tests (e.g., pipeline routing models)
# - Tested via policies (e.g., Policy is verified in policies/, not doctrine/)
SUPPORTING_MODELS = {
    "acknowledgement",  # Handler response type - infrastructure for workflow orchestration
    "code_info",  # Contains FieldInfo, MethodInfo, BoundedContextInfo - supporting models
    "content_stream",  # Pydantic IO stream wrapper - infrastructure utility
    "doctrine",  # Meta-entity describing doctrine rules - validated by tests=doctrine pattern
    "documentation",  # Tested via sphinx-documentation policy
    "evaluation",  # Contains EvaluationResult - infrastructure for semantic evaluation
    "policy",  # Policy entity - tested via policies/ infrastructure, not doctrine
    # Pipeline routing models are tested via test_route_doctrine.py in tests/domain/models/
    "pipeline_dispatch",
    "pipeline_route",
    "pipeline_router",
    # Execution record models - infrastructure for observability and projections
    "operation_record",  # Records service operation invocations within use cases
    "pipeline_output",  # Output artifacts produced by pipeline executions
    "use_case_execution",  # Records of use case executions with their operations
}

# Meta-doctrine tests that aren't about specific entities.
# These define organizational/structural rules rather than entity doctrine.
# Note: test_mcp and test_tests were moved to policies/ (ADR 005)
META_DOCTRINE_TESTS = {
    "test_doctrine_coverage",  # This test file itself
    "test_sphinx_extension",  # SPHINX-EXTENSION app type rules (subset of application)
    "test_documentation_links",  # Documentation link integrity (not entity-specific)
}


class TestDoctrineCoverage:
    """Ensure every entity has doctrine tests and vice versa."""

    def test_every_entity_MUST_have_doctrine_tests(self):
        """Every entity file in domain/models/ MUST have corresponding doctrine tests.

        This ensures we don't add new entities without defining their doctrine.
        If you're adding a new entity file, you must also add a corresponding
        test file in doctrine/.
        """
        # Find all entity files in domain/models/
        entity_files = {
            f.stem
            for f in MODELS_DIR.glob("*.py")
            if not f.name.startswith("_") and f.stem not in SUPPORTING_MODELS
        }

        # Find all doctrine test files (excluding meta-doctrine tests)
        doctrine_entities = {
            f.stem.replace("test_", "")
            for f in DOCTRINE_DIR.glob("test_*.py")
            if f.stem not in META_DOCTRINE_TESTS
        }

        # Check coverage
        missing_doctrine = entity_files - doctrine_entities
        assert (
            not missing_doctrine
        ), f"Entity files missing doctrine tests: {missing_doctrine}"

    def test_every_doctrine_MUST_have_entity(self):
        """Every doctrine test file MUST correspond to an entity file.

        This ensures we don't have orphan doctrine tests. If a doctrine test
        exists, there should be a corresponding entity file in domain/models/.
        Meta-doctrine tests (about organization, not entities) are excluded.
        """
        doctrine_entities = {
            f.stem.replace("test_", "")
            for f in DOCTRINE_DIR.glob("test_*.py")
            if f.stem not in META_DOCTRINE_TESTS
        }

        # All possible entity file names (including supporting models)
        entity_files = {
            f.stem for f in MODELS_DIR.glob("*.py") if not f.name.startswith("_")
        }

        orphan_doctrine = doctrine_entities - entity_files
        assert (
            not orphan_doctrine
        ), f"Doctrine tests without corresponding entity files: {orphan_doctrine}"

    def test_doctrine_test_files_MUST_follow_naming_convention(self):
        """All doctrine test files MUST be named test_{entity_name}.py."""
        for test_file in DOCTRINE_DIR.glob("*.py"):
            if test_file.name.startswith("_"):
                continue
            if test_file.name == "conftest.py":
                continue

            assert test_file.name.startswith("test_"), (
                f"Doctrine file {test_file.name} MUST start with 'test_'. "
                "This ensures pytest discovers it."
            )

    def test_entity_files_MUST_have_docstring(self):
        """All entity files in domain/models/ MUST have a module docstring.

        The module or class docstring serves as the definition shown by
        `doctrine show`.
        """
        for entity_file in MODELS_DIR.glob("*.py"):
            if entity_file.name.startswith("_"):
                continue
            if entity_file.stem in SUPPORTING_MODELS:
                continue

            content = entity_file.read_text()
            # Check for module docstring (starts with """ or ''')
            stripped = content.lstrip()
            has_docstring = stripped.startswith('"""') or stripped.startswith("'''")

            assert has_docstring, (
                f"{entity_file.name} MUST have a module docstring. "
                "This docstring is used as the definition in `doctrine show`."
            )
