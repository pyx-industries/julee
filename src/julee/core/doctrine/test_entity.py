"""Entity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

import pytest

from julee.core.doctrine_constants import ENTITY_FORBIDDEN_SUFFIXES
from julee.core.use_cases.code_artifact.list_entities import ListEntitiesUseCase
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest

# Meta-entities in core that describe what Request/Response/UseCase ARE.
# These are exempt from the forbidden suffix rule because they're describing
# the concept (for introspection/documentation), not being instances of the concept.
META_ENTITIES = {"Request", "Response", "UseCase"}

# Supporting entities that have special implementation patterns.
# These are infrastructure utilities, not domain data models.
# (Mirrors SUPPORTING_MODELS in test_doctrine_coverage.py)
INFRASTRUCTURE_ENTITIES = {
    "ContentStream",  # Pydantic custom field type for IO streams
}

# Valid intermediate base classes that inherit from BaseModel.
# Entities inheriting from these are considered valid.
VALID_BASEMODEL_INTERMEDIATES = {
    "ClassInfo",  # Core class info pattern
    "BaseCredential",  # contrib/untp credential base
    "BaseEvent",  # contrib/untp event base
}


class TestEntityNaming:
    """Doctrine about entity naming conventions."""

    @pytest.mark.asyncio
    async def test_all_entities_MUST_be_PascalCase(self, repo):
        """All entity class names MUST be PascalCase."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning entities
        assert len(response.artifacts) > 0, "No entities found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            if not name[0].isupper():
                violations.append(
                    f"{artifact.bounded_context}.{name}: MUST start with uppercase"
                )
            if "_" in name:
                violations.append(
                    f"{artifact.bounded_context}.{name}: MUST NOT contain underscores"
                )

        assert not violations, "Entity naming violations:\n" + "\n".join(violations)

    @pytest.mark.asyncio
    async def test_all_entities_MUST_NOT_have_reserved_suffixes(self, repo):
        """All entity class names MUST NOT end with UseCase, Request, or Response.

        Exception: Meta-entities in core that describe these concepts are exempt
        (e.g., core.Request describes what a Request IS for introspection).
        """
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            name = artifact.artifact.name
            # Skip meta-entities that describe the concepts
            if artifact.bounded_context == "core" and name in META_ENTITIES:
                continue
            for forbidden_suffix in ENTITY_FORBIDDEN_SUFFIXES:
                if name.endswith(forbidden_suffix):
                    violations.append(
                        f"{artifact.bounded_context}.{name}: "
                        f"MUST NOT end with '{forbidden_suffix}'"
                    )

        assert not violations, "Entity suffix violations:\n" + "\n".join(violations)


class TestEntityDocumentation:
    """Doctrine about entity documentation."""

    @pytest.mark.asyncio
    async def test_all_entities_MUST_have_docstring(self, repo):
        """All entity classes MUST have a docstring."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Entities missing docstrings:\n" + "\n".join(violations)


class TestEntityTypeAnnotations:
    """Doctrine about entity type annotations."""

    @pytest.mark.asyncio
    async def test_all_entity_fields_MUST_have_type_annotations(self, repo):
        """All entity fields MUST have type annotations."""
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            for field in artifact.artifact.fields:
                if not field.type_annotation:
                    violations.append(
                        f"{artifact.bounded_context}.{artifact.artifact.name}.{field.name}"
                    )

        assert not violations, "Entity fields missing type annotations:\n" + "\n".join(
            violations
        )


class TestEntityImplementation:
    """Doctrine about entity implementation patterns."""

    @pytest.mark.asyncio
    async def test_all_entities_MUST_use_pydantic_BaseModel_or_Enum(self, repo):
        """All entities MUST inherit from Pydantic BaseModel or Enum.

        Data entities (classes with fields) MUST inherit from BaseModel, either:
        - Directly (e.g., `class MyEntity(BaseModel)`)
        - Via intermediate classes (e.g., ClassInfo -> BaseModel)

        Pydantic provides automatic validation, serialization, type coercion,
        and immutability (with frozen=True). Using dataclasses or plain classes
        is not permitted - this ensures consistency across the codebase.

        Enum subclasses are the exception: they represent constrained value
        objects (choices from a fixed set), not data models with fields.
        """
        use_case = ListEntitiesUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning entities
        assert len(response.artifacts) > 0, "No entities found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            bases = artifact.artifact.bases
            name = artifact.artifact.name

            # Enums are value objects (constrained choices), not data models
            is_enum = "Enum" in bases or any("Enum" in b for b in bases)
            if is_enum:
                continue

            # Skip infrastructure entities with special patterns
            if name in INFRASTRUCTURE_ENTITIES:
                continue

            # Check if inherits from valid intermediate base classes
            inherits_valid_intermediate = any(
                base in VALID_BASEMODEL_INTERMEDIATES for base in bases
            )
            if inherits_valid_intermediate:
                continue

            # Check if BaseModel is in the inheritance chain
            has_basemodel = any("BaseModel" in base for base in bases)
            if not has_basemodel:
                violations.append(
                    f"{artifact.bounded_context}.{name}: "
                    f"inherits from {bases or ['nothing']}, MUST inherit from BaseModel"
                )

        assert not violations, "Entities not using Pydantic BaseModel:\n" + "\n".join(
            violations
        )
