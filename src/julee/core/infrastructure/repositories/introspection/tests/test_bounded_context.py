"""Tests for the structural markers the filesystem repository detects.

A bounded context laid out as ADR 001 prescribes keeps its domain under
``domain/``. The markers say which layers it has, and callers ask them
through ``BoundedContext.has_layer``.
"""

from pathlib import Path

import pytest

from julee.core.infrastructure.repositories.introspection.bounded_context import (  # noqa: E501
    FilesystemBoundedContextRepository,
)

pytestmark = pytest.mark.unit

ADR_001_LAYERS = (
    "domain/models",
    "domain/repositories",
    "domain/services",
    "use_cases",
)


def package(path: Path) -> Path:
    """Make ``path`` a python package, with its parents."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "__init__.py").write_text("")
    return path


@pytest.fixture
def solution(tmp_path: Path) -> Path:
    """A solution whose one context is laid out as ADR 001 prescribes."""
    context = package(tmp_path / "src" / "solution" / "ordering")
    (context / "__init__.py").write_text('"""Ordering."""\n')
    for layer in ADR_001_LAYERS:
        package(context / layer)
    return tmp_path


async def test_a_context_under_domain_reports_the_layers_it_has(
    solution: Path,
) -> None:
    repository = FilesystemBoundedContextRepository(solution, "src/solution")

    (ordering,) = await repository.list_all()

    assert ordering.markers.has_domain_models
    assert ordering.markers.has_domain_repositories
    assert ordering.markers.has_domain_services
    assert ordering.markers.has_domain_use_cases


async def test_each_layer_is_visible_through_has_layer(
    solution: Path,
) -> None:
    repository = FilesystemBoundedContextRepository(solution, "src/solution")

    (ordering,) = await repository.list_all()

    for layer in ("models", "repositories", "services", "use_cases"):
        assert ordering.has_layer(layer), layer
