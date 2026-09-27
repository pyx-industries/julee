"""Tests for the dependency rule."""

from pathlib import Path

import pytest

from julee.core.doctrine.resolution import package_of
from julee.core.doctrine.rules.dependency import (
    absolute_module,
    usecases_importing_outward,
)
from julee.core.parsers.imports import ImportInfo

pytestmark = pytest.mark.unit

CONTEXT = "acme.stories"
PACKAGES = {"stories": CONTEXT}
PACKAGE_OF_FILE = "acme.stories.usecases"


def an_import(module: str, level: int = 0) -> ImportInfo:
    """One import, absolute unless a level is given."""
    return ImportInfo(
        module=module,
        level=level,
        is_relative=level > 0,
        file="usecases/get_story.py",
        line=3,
    )


def objections(module: str, level: int = 0, kits: tuple[str, ...] = ()) -> list[str]:
    """What the rule says about one import from a use case."""
    return usecases_importing_outward(
        [("stories", PACKAGE_OF_FILE, an_import(module, level))], PACKAGES, kits
    )


ALLOWED = {
    "its own domain": "acme.stories.domain.models.story",
    "its own ports": "acme.stories.domain.repositories.story",
    "a sibling use case": "acme.stories.usecases.other",
    "the language": "dataclasses",
    "a language submodule": "datetime.timezone",
    "collections.abc": "collections.abc",
    "future annotations": "__future__",
    "julee's entities": "julee.core.entities.text",
    "julee's use case bases": "julee.core.usecases.generic_crud",
    "julee's port protocols": "julee.core.repositories.bounded_context",
}

FORBIDDEN = {
    "pydantic": "pydantic",
    "a third-party package": "yaml",
    "serialisation": "json",
    "the filesystem": "pathlib",
    "logging": "logging",
    "execution": "asyncio",
    "non-determinism": "random",
    "mutable containers": "collections",
    "its own infrastructure": "acme.stories.infrastructure.memory",
    "its own apps": "acme.stories.apps.api",
    "julee's adapters": "julee.repositories.memory.base",
    "julee's integrations": "julee.integrations.temporal.clock",
    "julee's cli": "julee.cli.main",
    "julee's own infrastructure": "julee.core.infrastructure.repositories.file",
}


def test_a_usecase_may_import_only_inward() -> None:
    """The rule accepts what points inward and refuses everything else.

    Every case is tried before reporting, so a failure names all of
    them.
    """
    refused = [what for what, module in ALLOWED.items() if objections(module)]
    assert not refused, "refused an inward import: " + ", ".join(refused)

    leaked = [what for what, module in FORBIDDEN.items() if not objections(module)]
    assert not leaked, "accepted an outward import: " + ", ".join(leaked)


@pytest.mark.parametrize(
    ("module", "level", "expected"),
    [
        ("other", 1, "acme.stories.usecases.other"),
        ("domain.models.story", 2, "acme.stories.domain.models.story"),
        ("infrastructure.memory", 2, "acme.stories.infrastructure.memory"),
        ("json", 0, "json"),
    ],
    ids=["sibling", "own-domain", "own-infrastructure", "absolute"],
)
def test_a_relative_import_resolves_to_what_it_names(
    module: str, level: int, expected: str
) -> None:
    """Without the level, a sibling and an adapter read the same."""
    assert absolute_module(an_import(module, level), PACKAGE_OF_FILE) == expected


def test_a_relative_import_of_infrastructure_is_refused() -> None:
    """The case the parser could not see before it recorded the level."""
    assert objections("infrastructure.memory", level=2) != []


def test_a_relative_import_of_a_sibling_is_allowed() -> None:
    """The one it used to be indistinguishable from."""
    assert objections("other", level=1) == []


def test_an_adopted_kit_offers_its_domain_and_use_cases() -> None:
    """A solution's use case may build on a kit it adopted."""
    assert objections("julee_hcd.domain.models.story", kits=("julee_hcd",)) == []
    assert objections("julee_hcd.usecases.get_story", kits=("julee_hcd",)) == []


def test_an_adopted_kit_does_not_offer_its_insides() -> None:
    """ADR 012 section 3, for a use case rather than a composition root."""
    assert objections("julee_hcd.infrastructure.memory", kits=("julee_hcd",)) != []


def test_an_unadopted_package_is_third_party() -> None:
    """A kit nobody adopted is a dependency nobody declared."""
    assert objections("julee_hcd.domain.models.story") != []


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("get_story.py", "acme.stories.usecases"),
        ("__init__.py", "acme.stories.usecases"),
    ],
    ids=["a module", "a package init"],
)
def test_a_files_package_is_where_its_relative_imports_start(
    tmp_path: Path, name: str, expected: str
) -> None:
    """A package's init sits in the package, not beside it.

    Getting this wrong resolved every relative import in an __init__
    one level too high, which reported a sibling as living outside the
    use cases.
    """
    context = tmp_path / "acme" / "stories" / "usecases"
    context.mkdir(parents=True)
    for package in (tmp_path / "acme", tmp_path / "acme" / "stories", context):
        (package / "__init__.py").write_text("")
    (context / name).write_text("")

    assert package_of(context / name) == expected


def test_the_objection_names_the_file_the_line_and_the_module() -> None:
    """So an author can act on it without rerunning anything."""
    assert objections("json") == [
        "usecases/get_story.py:3 imports json, but it is in the standard "
        "library but not part of the language a use case speaks"
    ]
