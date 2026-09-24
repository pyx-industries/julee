"""Unit tests for the ADR 008 build-time CRUD generator.

The generator emits source, so these tests generate a module, import it, and
exercise the use cases it wrote. Asserting on the text alone would not have
caught an update that validated fine and then overwrote the fields it was not
asked to change.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from julee.core.usecases.generate_crud import generate
from julee.core.usecases.tests.crud_fixtures import (
    DeletableWidgetRepository,
    MintingWidgetRepository,
    Widget,
    WidgetRepository,
)

pytestmark = pytest.mark.unit

FIXTURES = "julee.core.usecases.tests.crud_fixtures"


def _generate_widget_crud(
    out_dir: Path,
    create_fields: list[tuple[str, str]],
    module_name: str = "generated_crud_widget",
    repo: str = "WidgetRepository",
    include_delete: bool = False,
) -> ModuleType:
    """Generate CRUD for the Widget fixture and import the result."""
    out_file = generate(
        entity="Widget",
        entity_module=FIXTURES,
        repo=repo,
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=create_fields,
        # colour carries a default the update side has to discard, since on an
        # update the only useful default is "not mentioned".
        update_fields=[("name", "str"), ("colour", 'str = "beige"')],
        include_delete=include_delete,
        out_dir=out_dir,
    )
    spec = importlib.util.spec_from_file_location(module_name, out_file)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def crud(tmp_path: Path) -> ModuleType:
    """CRUD for an entity whose id the repository mints."""
    return _generate_widget_crud(
        tmp_path,
        [("name", "str"), ("colour", "str")],
        repo="MintingWidgetRepository",
    )


@pytest.fixture
def deletable_crud(tmp_path: Path) -> ModuleType:
    """CRUD including delete, over a repository that opted in."""
    return _generate_widget_crud(
        tmp_path / "deletable",
        [("slug", "str"), ("name", "str")],
        module_name="generated_crud_widget_deletable",
        repo="DeletableWidgetRepository",
        include_delete=True,
    )


@pytest.fixture
def keyed_crud(tmp_path: Path) -> ModuleType:
    """CRUD for an entity the caller keys itself, with optional fields."""
    return _generate_widget_crud(
        tmp_path / "keyed",
        [("slug", "str"), ("name", "str"), ("colour", 'str = "beige"')],
        module_name="generated_crud_widget_keyed",
    )


# =============================================================================
# What the generator writes
# =============================================================================


def test_generated_module_is_importable_python(crud: ModuleType) -> None:
    """The point of a code generator: the output loads and has the classes."""
    assert crud.GetWidgetUseCase is not None
    assert crud.ListWidgetsUseCase is not None
    assert crud.CreateWidgetUseCase is not None
    assert crud.UpdateWidgetUseCase is not None


def test_create_request_requires_its_fields(crud: ModuleType) -> None:
    """Creating is all-or-nothing, so create fields stay required."""
    with pytest.raises(ValueError):
        crud.CreateWidgetRequest(name="hammer")


def test_create_field_can_carry_a_default(keyed_crud: ModuleType) -> None:
    """A field the entity defaults should not be compulsory on the way in."""
    request = keyed_crud.CreateWidgetRequest(slug="hammer", name="Hammer")

    assert request.colour == "beige"


def test_update_request_requires_only_the_id(crud: ModuleType) -> None:
    """An update names what changes; the id says what to change it on."""
    request = crud.UpdateWidgetRequest(slug="hammer")

    assert request.slug == "hammer"
    assert request.name is None


# =============================================================================
# What the generated use cases do
# =============================================================================


async def test_create_mints_an_id_when_the_entity_has_no_natural_key(
    crud: ModuleType,
) -> None:
    """Without the id among its fields, the repository decides the key."""
    repo = MintingWidgetRepository()

    response = await crud.CreateWidgetUseCase(repo).execute(
        crud.CreateWidgetRequest(name="Hammer", colour="red")
    )

    assert response.widget.slug == "generated-id"


async def test_create_keeps_the_key_the_caller_supplied(
    keyed_crud: ModuleType,
) -> None:
    """A slug derived from a name is the caller's to choose, not the repo's."""
    repo = WidgetRepository()

    response = await keyed_crud.CreateWidgetUseCase(repo).execute(
        keyed_crud.CreateWidgetRequest(slug="hammer", name="Hammer")
    )

    # The repository has no generate_id at all, so this only passes because
    # the create never reached for one.
    assert not hasattr(repo, "generate_id")
    assert response.widget.slug == "hammer"
    assert repo.storage["hammer"].colour == "beige"


async def test_update_leaves_out_fields_the_request_did_not_name(
    crud: ModuleType,
) -> None:
    """The bug this test exists for: a partial update clobbered the rest."""
    repo = MintingWidgetRepository()
    repo.storage["hammer"] = Widget(slug="hammer", name="Hammer", colour="red")

    response = await crud.UpdateWidgetUseCase(repo).execute(
        crud.UpdateWidgetRequest(slug="hammer", name="Sledgehammer")
    )

    assert response.widget.name == "Sledgehammer"
    assert response.widget.colour == "red"


async def test_update_passing_none_explicitly_clears_the_field(
    crud: ModuleType,
) -> None:
    """Unset means leave alone, so None has to be free to mean something."""
    repo = MintingWidgetRepository()
    repo.storage["hammer"] = Widget(slug="hammer", name="Hammer", colour="red")

    response = await crud.UpdateWidgetUseCase(repo).execute(
        crud.UpdateWidgetRequest(slug="hammer", colour=None)
    )

    assert response.widget.colour is None
    assert response.widget.name == "Hammer"


async def test_update_saves_what_it_returns(crud: ModuleType) -> None:
    """The response is not a preview; the repository has the same entity."""
    repo = MintingWidgetRepository()
    repo.storage["hammer"] = Widget(slug="hammer", name="Hammer", colour="red")

    await crud.UpdateWidgetUseCase(repo).execute(
        crud.UpdateWidgetRequest(slug="hammer", name="Sledgehammer")
    )

    assert repo.storage["hammer"].name == "Sledgehammer"


async def test_updating_an_absent_entity_is_not_a_silent_create(
    crud: ModuleType,
) -> None:
    """Update means update."""
    repo = MintingWidgetRepository()

    with pytest.raises(crud.EntityNotFoundError):
        await crud.UpdateWidgetUseCase(repo).execute(
            crud.UpdateWidgetRequest(slug="missing", name="Nothing")
        )


def test_the_plural_is_guessed_when_the_caller_says_nothing(
    tmp_path: Path,
) -> None:
    """Most entities pluralise the way inflect thinks they do."""
    crud = _generate_widget_crud(tmp_path, [("name", "str")])

    assert crud.ListWidgetsUseCase is not None


def test_a_caller_can_say_what_several_of_something_are_called(
    tmp_path: Path,
) -> None:
    """inflect makes "personae" of a persona; the domain says "personas"."""
    out_file = generate(
        entity="Widget",
        entity_module=FIXTURES,
        repo="WidgetRepository",
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=[("name", "str")],
        update_fields=[("name", "str")],
        plural="Widgeten",
        out_dir=tmp_path / "plural",
    )
    source = out_file.read_text()

    assert "class ListWidgetenUseCase" in source
    assert "widgeten: list[Widget]" in source
    assert "ListWidgetsUseCase" not in source


# =============================================================================
# Delete
# =============================================================================


def test_delete_is_not_emitted_unless_asked(crud: ModuleType) -> None:
    """Opt in, where the other four are opt out.

    Two of the five kits must never delete — ceap and polling keep the
    record of what they processed — so a destructive use case appearing
    because nobody said otherwise is the wrong way for this to fail.
    """
    assert not hasattr(crud, "DeleteWidgetUseCase")
    assert not hasattr(crud, "DeleteWidgetRequest")


def test_asking_for_delete_emits_the_trio(deletable_crud: ModuleType) -> None:
    assert hasattr(deletable_crud, "DeleteWidgetRequest")
    assert hasattr(deletable_crud, "DeleteWidgetResponse")
    assert hasattr(deletable_crud, "DeleteWidgetUseCase")


def test_the_other_four_are_still_emitted_beside_it(
    deletable_crud: ModuleType,
) -> None:
    """Delete is added to CRUD, not swapped for part of it."""
    for name in (
        "GetWidgetUseCase",
        "ListWidgetsUseCase",  # the list one is named by the plural
        "CreateWidgetUseCase",
        "UpdateWidgetUseCase",
    ):
        assert hasattr(deletable_crud, name), name


def test_the_request_asks_only_for_the_id(deletable_crud: ModuleType) -> None:
    request = deletable_crud.DeleteWidgetRequest(slug="a")

    assert request.slug == "a"
    assert set(deletable_crud.DeleteWidgetRequest.model_fields) == {"slug"}


async def test_deleting_an_entity_removes_it(deletable_crud: ModuleType) -> None:
    repo = DeletableWidgetRepository()
    repo.storage["a"] = Widget(slug="a", name="Anvil")
    use_case = deletable_crud.DeleteWidgetUseCase(repo)

    response = await use_case.execute(deletable_crud.DeleteWidgetRequest(slug="a"))

    assert response.deleted is True
    assert await repo.get("a") is None


async def test_deleting_something_absent_reports_rather_than_raising(
    deletable_crud: ModuleType,
) -> None:
    """The decision this use case exists to encode.

    Get and Update raise EntityNotFoundError, because an absent entity
    means the caller is working from something stale. Delete does not:
    "it was already gone" is the outcome the caller asked for. Both kits
    that hand-wrote delete before this existed chose the same.
    """
    repo = DeletableWidgetRepository()
    use_case = deletable_crud.DeleteWidgetUseCase(repo)

    response = await use_case.execute(deletable_crud.DeleteWidgetRequest(slug="gone"))

    assert response.deleted is False


async def test_deleting_twice_is_not_an_error(deletable_crud: ModuleType) -> None:
    repo = DeletableWidgetRepository()
    repo.storage["a"] = Widget(slug="a", name="Anvil")
    use_case = deletable_crud.DeleteWidgetUseCase(repo)
    request = deletable_crud.DeleteWidgetRequest(slug="a")

    first = await use_case.execute(request)
    second = await use_case.execute(request)

    assert (first.deleted, second.deleted) == (True, False)


async def test_deleting_one_leaves_the_others(deletable_crud: ModuleType) -> None:
    repo = DeletableWidgetRepository()
    repo.storage["a"] = Widget(slug="a", name="Anvil")
    repo.storage["b"] = Widget(slug="b", name="Bellows")
    use_case = deletable_crud.DeleteWidgetUseCase(repo)

    await use_case.execute(deletable_crud.DeleteWidgetRequest(slug="a"))

    assert await repo.get("b") is not None
