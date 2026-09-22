"""Tests for the handler and repository protocol rules."""

import pytest

from julee.core.doctrine.rules.protocol import (
    base_entity_type,
    handler_methods_not_returning_Acknowledgement,
    handler_protocols_outside_singular_files,
    handlers_outside_infrastructure_handlers,
    repositories_referencing_several_entities,
)
from julee.core.entities.code_info import ClassInfo, MethodInfo
from julee.core.usecases.code_artifact.uc_interfaces import CodeArtifactWithContext

pytestmark = pytest.mark.unit


def a_handler(
    name: str = "PollingResultHandler",
    file: str = "polling_result_handler.py",
    returns: tuple[str, ...] = ("Acknowledgement",),
    slug: str = "polling",
) -> CodeArtifactWithContext:
    """A handler protocol that offends none of the rules."""
    return CodeArtifactWithContext(
        bounded_context=slug,
        artifact=ClassInfo(
            name=name,
            file=file,
            methods=[
                MethodInfo(name=f"handle_{i}", return_type=r)
                for i, r in enumerate(returns)
            ],
        ),
    )


def a_repository(
    name: str = "StoryRepository",
    bases: tuple[str, ...] = ("BaseRepository[Story]",),
    references: tuple[str, ...] = ("Story",),
    slug: str = "hcd",
) -> CodeArtifactWithContext:
    """A repository protocol covering one entity."""
    artifact = ClassInfo(
        name=name,
        bases=list(bases),
        methods=[MethodInfo(name="get", return_type=f"{r} | None") for r in references],
    )
    return CodeArtifactWithContext(bounded_context=slug, artifact=artifact)


# =============================================================================
# A handler answers the same way whatever it does
# =============================================================================


def test_a_handler_returning_Acknowledgement_is_allowed() -> None:
    """The ordinary case."""
    assert handler_methods_not_returning_Acknowledgement([a_handler()]) == []


def test_a_handler_returning_something_else_is_reported() -> None:
    """The use case would have to know what the handler does."""
    objections = handler_methods_not_returning_Acknowledgement(
        [a_handler(returns=("bool",))]
    )

    assert len(objections) == 1
    assert "expected 'Acknowledgement'" in objections[0]


def test_every_offending_method_is_reported() -> None:
    """One protocol may have several, and each needs changing."""
    objections = handler_methods_not_returning_Acknowledgement(
        [a_handler(returns=("bool", "None", "Acknowledgement"))]
    )

    assert len(objections) == 2


def test_returning_None_is_not_returning_an_acknowledgement() -> None:
    """Silence is the case the pattern exists to replace."""
    assert (
        handler_methods_not_returning_Acknowledgement([a_handler(returns=("None",))])
        != []
    )


# =============================================================================
# One handler per file, named for it
# =============================================================================


def test_a_handler_in_a_singular_file_is_allowed() -> None:
    """The ordinary case."""
    assert handler_protocols_outside_singular_files([a_handler()]) == []


def test_a_handler_in_a_collective_file_is_reported() -> None:
    """handlers.py says the file is a drawer rather than a definition."""
    objections = handler_protocols_outside_singular_files(
        [a_handler(file="handlers.py")]
    )

    assert objections != []


def test_a_file_merely_containing_handler_is_not_enough() -> None:
    """handler_registry.py does not end with _handler.py."""
    assert (
        handler_protocols_outside_singular_files(
            [a_handler(file="handler_registry.py")]
        )
        != []
    )


# =============================================================================
# Implementations live together
# =============================================================================


def test_a_handler_under_handlers_is_allowed() -> None:
    """The ordinary case."""
    found = [("hcd", ClassInfo(name="EpicHandler", file="handlers/epic.py"))]

    assert handlers_outside_infrastructure_handlers(found) == []


def test_a_handler_elsewhere_in_infrastructure_is_reported() -> None:
    """Otherwise they scatter among proxies, repositories and wrappers."""
    found = [("hcd", ClassInfo(name="EpicHandler", file="services/epic.py"))]

    assert handlers_outside_infrastructure_handlers(found) != []


def test_a_temporal_layer_wrapper_is_exempt() -> None:
    """It follows the three-layer pattern for workflows instead."""
    found = [("ceap", ClassInfo(name="AssemblyHandler", file="temporal/assembly.py"))]

    assert handlers_outside_infrastructure_handlers(found) == []


def test_a_class_that_is_not_a_handler_is_ignored() -> None:
    """The rule is about handlers, not about everything in infrastructure."""
    found = [("hcd", ClassInfo(name="MemoryEpicRepository", file="memory/epic.py"))]

    assert handlers_outside_infrastructure_handlers(found) == []


# =============================================================================
# A repository covers one aggregate
# =============================================================================


def test_the_declared_entity_is_read_from_the_base() -> None:
    """Which is how the rule knows what the repository is for."""
    assert base_entity_type(a_repository().artifact) == "Story"


def test_the_entity_is_read_from_the_marker_alone() -> None:
    """RepositoryOf[T] says which entity and nothing else."""
    protocol = a_repository(bases=("RepositoryOf[Story]",)).artifact

    assert base_entity_type(protocol) == "Story"


def test_a_repository_that_is_not_CRUD_is_still_checked() -> None:
    """Declaring the entity is what the rule needs, not the CRUD methods."""
    objections = repositories_referencing_several_entities(
        [a_repository(bases=("RepositoryOf[Story]",), references=("Story", "App"))],
        {"hcd": {"Story", "App"}},
    )

    assert len(objections) == 1


def test_a_repository_declaring_nothing_has_no_primary_entity() -> None:
    """And is therefore exempt, since nothing can be told structurally."""
    assert base_entity_type(a_repository(bases=("Protocol",)).artifact) is None


def test_a_repository_covering_one_entity_is_allowed() -> None:
    """The ordinary case."""
    objections = repositories_referencing_several_entities(
        [a_repository()], {"hcd": {"Story", "App"}}
    )

    assert objections == []


def test_a_repository_naming_another_entity_is_reported() -> None:
    """Two jobs, and two things that should be able to change apart."""
    objections = repositories_referencing_several_entities(
        [a_repository(references=("Story", "App"))], {"hcd": {"Story", "App"}}
    )

    assert len(objections) == 1
    assert "App" in objections[0]


def test_a_type_that_is_not_an_entity_here_is_incidental() -> None:
    """An enum or a primitive binds the repository to nothing."""
    objections = repositories_referencing_several_entities(
        [a_repository(references=("Story", "AppType"))], {"hcd": {"Story", "App"}}
    )

    assert objections == []


def test_a_repository_without_BaseRepository_is_exempt() -> None:
    """Its primary entity cannot be told, so nothing can be said."""
    objections = repositories_referencing_several_entities(
        [a_repository(bases=("Protocol",), references=("Story", "App"))],
        {"hcd": {"Story", "App"}},
    )

    assert objections == []


# =============================================================================
# Nothing at all
# =============================================================================


@pytest.mark.parametrize(
    "rule",
    [
        lambda: handler_methods_not_returning_Acknowledgement([]),
        lambda: handler_protocols_outside_singular_files([]),
        lambda: handlers_outside_infrastructure_handlers([]),
        lambda: repositories_referencing_several_entities([], {}),
    ],
)
def test_a_codebase_with_none_of_these_offends_nothing(rule) -> None:
    """Most kits have no handlers at all."""
    assert rule() == []
