"""Tests for mounting what the adopted kits contribute."""

from pathlib import Path

import pytest

from julee.core.entities.kit import Kit
from julee.integrations.fastapi import include_kit_routers, kit_routers

pytestmark = pytest.mark.unit


class FakeApp:
    """Enough of a FastAPI application to see what was mounted."""

    def __init__(self) -> None:
        """Start with nothing mounted."""
        self.mounted: list[tuple[object, dict[str, object]]] = []

    def include_router(self, router: object, **kwargs: object) -> None:
        """Record the mount rather than doing one."""
        self.mounted.append((router, kwargs))


def a_kit(slug: str, *paths: str) -> Kit:
    """A kit contributing these routers."""
    return Kit(
        slug=slug,
        name=slug.upper(),
        package=f"julee_{slug}",
        contributes={"fastapi.routers": tuple(paths)} if paths else {},
    )


@pytest.fixture
def solution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A solution adopting two kits, one of which serves nothing."""
    adopted = (
        a_kit("ceap", "julee.core.kits:adopted_kits"),
        a_kit("polling"),
    )
    monkeypatch.setattr("julee.core.kits.adopted_kits", lambda _root: adopted)
    return tmp_path


def test_a_contributed_router_is_resolved(solution: Path) -> None:
    """The path names an object, and this is that object."""
    routers = kit_routers(solution)

    assert len(routers) == 1
    assert callable(routers[0])


def test_a_kit_serving_nothing_contributes_nothing(solution: Path) -> None:
    """Most kits serve nothing, and that is not an error."""
    assert len(kit_routers(solution)) == 1


def test_every_router_is_mounted(solution: Path) -> None:
    """The point of the helper."""
    app = FakeApp()

    mounted = include_kit_routers(app, solution)

    assert mounted == 1
    assert len(app.mounted) == 1


def test_arguments_reach_include_router(solution: Path) -> None:
    """So a solution can put every kit's routes under a prefix."""
    app = FakeApp()

    include_kit_routers(app, solution, prefix="/api")

    assert app.mounted[0][1] == {"prefix": "/api"}


def test_a_solution_adopting_nothing_mounts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An application should not have to check before calling."""
    monkeypatch.setattr("julee.core.kits.adopted_kits", lambda _root: ())
    app = FakeApp()

    assert include_kit_routers(app, tmp_path) == 0


def test_a_router_that_is_not_there_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """At startup, naming the manifest to fix, rather than mounting nothing."""
    monkeypatch.setattr(
        "julee.core.kits.adopted_kits",
        lambda _root: (a_kit("ceap", "julee.core.kits:no_such_router"),),
    )

    with pytest.raises(AttributeError, match="no_such_router"):
        kit_routers(tmp_path)
