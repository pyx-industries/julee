"""ServiceProtocol doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A Service is semantically bound to TWO OR MORE entity types and is typically
responsible for TRANSFORMATION between them. This distinguishes Services from
Repositories:

    Repository: Protocol → 1 Entity → Persistence
    Service:    Protocol → N Entities → Transformation (N >= 2)

Services transform data between entity types. Examples:
- SemanticEvaluationService: ClassInfo, MethodInfo, FieldInfo → EvaluationResult
- SuggestionContextService: Story, Epic, Journey, etc. → cross-entity queries
- PipelineRequestTransformer: Response entities → Request entities

Implementation note: Service protocols define the interface; infrastructure
implementations handle the actual transformation logic.
"""

import pytest

from julee.core.doctrine_constants import (
    PROTOCOL_BASES,
    SERVICE_SUFFIX,
)
from julee.core.parsers.ast import parse_python_classes
from julee.core.use_cases.code_artifact.list_entities import ListEntitiesUseCase
from julee.core.use_cases.code_artifact.list_service_protocols import (
    ListServiceProtocolsUseCase,
)
from julee.core.use_cases.code_artifact.uc_interfaces import ListCodeArtifactsRequest


class TestServiceProtocolNaming:
    """Doctrine about service protocol naming conventions."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_end_with_Service(self, repo):
        """All service protocol names MUST end with 'Service'."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        # Canary: ensure we're actually scanning service protocols
        assert (
            len(response.artifacts) > 0
        ), "No service protocols found - detector may be broken"

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.name.endswith(SERVICE_SUFFIX):
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert (
            not violations
        ), f"Service protocols not ending with '{SERVICE_SUFFIX}':\n" + "\n".join(
            violations
        )


class TestServiceProtocolDocumentation:
    """Doctrine about service protocol documentation."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_have_docstring(self, repo):
        """All service protocol classes MUST have a docstring."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            if not artifact.artifact.docstring:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name}"
                )

        assert not violations, "Service protocols missing docstrings:\n" + "\n".join(
            violations
        )


class TestServiceProtocolInheritance:
    """Doctrine about service protocol inheritance."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_inherit_from_Protocol(self, repo):
        """All service protocols MUST inherit from Protocol."""
        use_case = ListServiceProtocolsUseCase(repo)
        response = await use_case.execute(ListCodeArtifactsRequest())

        violations = []
        for artifact in response.artifacts:
            # Explicit check for Protocol or Protocol[T] generic
            has_protocol = any(
                base in PROTOCOL_BASES for base in artifact.artifact.bases
            )
            if not has_protocol:
                violations.append(
                    f"{artifact.bounded_context}.{artifact.artifact.name} "
                    f"(bases: {artifact.artifact.bases})"
                )

        assert (
            not violations
        ), "Service protocols not inheriting from Protocol:\n" + "\n".join(violations)


# Infrastructure protocols that are intentionally generic.
# These use BaseModel or similar generics because they operate on
# ANY entity types, not specific ones. They're plumbing, not domain services.
GENERIC_INFRASTRUCTURE_PROTOCOLS = {
    "PipelineRequestTransformer",  # Transforms any Response → any Request
    "RequestTransformer",  # Alias for PipelineRequestTransformer
}


# Types to exclude from entity binding analysis.
# These are generic/utility types, not domain entities.
NON_ENTITY_TYPES = {
    # Python builtins and typing
    "Any",
    "None",
    "Protocol",
    "BaseModel",
    "Self",
    "Type",
    "TypeVar",
    "Generic",
    # Common containers (the types inside them are what matter)
    "Optional",
    "Union",
    "List",
    "Dict",
    "Set",
    "Tuple",
    "Sequence",
    "Mapping",
    "Iterable",
    "Iterator",
    "Callable",
    "Awaitable",
    "Coroutine",
    # Primitives (not entities)
    "str",
    "int",
    "float",
    "bool",
    "bytes",
}


class TestServiceProtocolEntityBinding:
    """Doctrine about service protocol entity binding."""

    @pytest.mark.asyncio
    async def test_all_service_protocols_MUST_be_bound_to_multiple_entity_types(
        self, repo, project_root
    ):
        """All service protocols MUST be bound to 2+ entity types.

        A Service is semantically bound to TWO OR MORE entity types and is
        responsible for TRANSFORMATION between them. This is the defining
        characteristic that distinguishes Services from Repositories:

            Repository: bound to 1 entity type (persistence)
            Service: bound to 2+ entity types (transformation)

        This test:
        1. Discovers all entity types across bounded contexts
        2. For each service protocol, extracts referenced types from method signatures
        3. Filters to only entity types (excludes primitives, builtins, generics)
        4. Verifies each service references at least 2 distinct entity types

        Note: The service's own name and Protocol are excluded from the count.
        """
        # Step 1: Collect all known entity names across bounded contexts
        entities_use_case = ListEntitiesUseCase(repo)
        entities_response = await entities_use_case.execute(ListCodeArtifactsRequest())

        all_entity_names: set[str] = set()
        for artifact in entities_response.artifacts:
            all_entity_names.add(artifact.artifact.name)

        # Also scan core entities (shared across all contexts)
        core_entities_dir = project_root / "src" / "julee" / "core" / "entities"
        if core_entities_dir.exists():
            core_entities = parse_python_classes(core_entities_dir)
            for entity in core_entities:
                all_entity_names.add(entity.name)

        # Step 2: Get all service protocols
        services_use_case = ListServiceProtocolsUseCase(repo)
        services_response = await services_use_case.execute(ListCodeArtifactsRequest())

        # Also check core services
        core_services_dir = project_root / "src" / "julee" / "core" / "services"

        class ArtifactLike:
            def __init__(self, artifact, bounded_context):
                self.artifact = artifact
                self.bounded_context = bounded_context

        core_services = (
            parse_python_classes(core_services_dir)
            if core_services_dir.exists()
            else []
        )
        all_service_artifacts = list(services_response.artifacts) + [
            ArtifactLike(svc, "core")
            for svc in core_services
            if svc.name.endswith("Service") or svc.name.endswith("Transformer")
        ]

        # Step 3: Check each service for entity binding
        violations = []
        for artifact in all_service_artifacts:
            service = artifact.artifact
            service_name = service.name

            # Skip generic infrastructure protocols (intentionally use BaseModel)
            if service_name in GENERIC_INFRASTRUCTURE_PROTOCOLS:
                continue

            # Get all types referenced in method signatures
            referenced_types = service.referenced_types

            # Filter to only entity types (exclude primitives, builtins, self)
            entity_refs = referenced_types & all_entity_names
            entity_refs -= NON_ENTITY_TYPES
            entity_refs.discard(service_name)  # Exclude self-reference

            if len(entity_refs) < 2:
                violations.append(
                    f"{artifact.bounded_context}.{service_name}: "
                    f"bound to {len(entity_refs)} entity types {sorted(entity_refs)}, "
                    f"needs 2+ (referenced: {sorted(referenced_types - NON_ENTITY_TYPES)})"
                )

        assert not violations, (
            "Service protocols MUST be bound to 2+ entity types:\n"
            + "\n".join(violations)
            + "\n\nServices transform data between entity types. "
            "If a service only references one entity type, it may belong "
            "in a repository instead."
        )
