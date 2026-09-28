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
from julee.core.usecases.generic_crud import EntityNotFoundError
from julee.core.usecases.tests.crud_fixtures import (
    DeletableWidgetRepository,
    CheckedWidgetRepository,
    DerivedIdWidgetRepository,
    MintingWidgetRepository,
    SelfNamingWidgetRepository,
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
    entity: str = "Widget",
    update_fields: list[tuple[str, str]] | None = None,
) -> ModuleType:
    """Generate CRUD for a fixture entity and import the result."""
    out_file = generate(
        entity=entity,
        entity_module=FIXTURES,
        repo=repo,
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=create_fields,
        # colour carries a default the update side has to discard, since on an
        # update the only useful default is "not mentioned".
        update_fields=update_fields or [("name", "str"), ("colour", 'str = "beige"')],
        include_delete=include_delete,
        out_dir=out_dir,
    )
    # Imported as part of a package rather than from its path, because
    # the generated use cases import their messages from the dtos
    # package beside them. Loading the file alone would leave that
    # relative import with nothing to be relative to — and would be
    # testing the generator in a shape no kit ever uses.
    return _import_generated(out_dir, out_file, module_name)


def _import_generated(out_dir: Path, out_file: Path, module_name: str) -> ModuleType:
    """Import a generated module as part of its bounded context.

    Args:
        out_dir: The context package the generator wrote into
        out_file: The generated use case module
        module_name: A name unique to this test, so two generated
            packages in one run do not collide in sys.modules

    Returns:
        The imported module
    """
    package = out_dir.name
    (out_dir / "__init__.py").write_text('"""A generated context."""\n')
    sys.path.insert(0, str(out_dir.parent))
    try:
        for stale in [name for name in sys.modules if name.startswith(package)]:
            del sys.modules[stale]
        return importlib.import_module(f"{package}.usecases.{out_file.stem}")
    finally:
        sys.path.remove(str(out_dir.parent))


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

    with pytest.raises(EntityNotFoundError):
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
    use_cases = out_file.read_text()
    messages = (out_file.parent.parent / "dtos" / out_file.name).read_text()

    assert "class ListWidgetenUseCase" in use_cases
    assert "ListWidgetsUseCase" not in use_cases
    # The plural names the response field too, and that now lives with
    # the messages rather than beside the use case that returns it.
    assert "widgeten: list[Widget]" in messages


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


# =============================================================================
# An entity that names itself
# =============================================================================


async def test_an_entity_that_names_itself_is_not_handed_an_empty_id(
    tmp_path: Path,
) -> None:
    """An id field with a default means the caller may leave it out.

    c4's Relationship and DynamicStep derive a slug from what they
    already carry, so passing an empty one defeats the derivation.
    Both had this branch hand-written into files headed "Do not edit",
    and a regeneration reverted it — which is the whole argument for
    the generator knowing.
    """
    crud = _generate_widget_crud(
        tmp_path / "self-naming",
        create_fields=[("slug", 'str = ""'), ("name", "str")],
        module_name="generated_self_naming",
        entity="SelfNamingWidget",
        repo="SelfNamingWidgetRepository",
    )
    repo = SelfNamingWidgetRepository()

    response = await crud.CreateSelfNamingWidgetUseCase(repo).execute(
        crud.CreateSelfNamingWidgetRequest(name="a-widget")
    )

    assert response.self_naming_widget.slug == "a-widget-derived"


async def test_a_slug_the_caller_named_is_still_kept(tmp_path: Path) -> None:
    """Deriving is what happens when nobody said, not instead of saying."""
    crud = _generate_widget_crud(
        tmp_path / "self-naming-explicit",
        create_fields=[("slug", 'str = ""'), ("name", "str")],
        module_name="generated_self_naming_explicit",
        entity="SelfNamingWidget",
        repo="SelfNamingWidgetRepository",
    )
    repo = SelfNamingWidgetRepository()

    response = await crud.CreateSelfNamingWidgetUseCase(repo).execute(
        crud.CreateSelfNamingWidgetRequest(slug="chosen", name="a-widget")
    )

    assert response.self_naming_widget.slug == "chosen"


def test_the_generated_create_names_the_ids_real_type(tmp_path: Path) -> None:
    """A slug field typed Slug must be constructed as one.

    The request says str because that is what crosses the wire, and
    the entity says Slug because that is what it is. Handing the str
    straight over type-checks nowhere: c4 had Slug(entity_id) written
    into every generated create by hand, and a regeneration took it
    out and failed mypy in six files.
    """
    out_file = generate(
        entity="SelfNamingWidget",
        entity_module=FIXTURES,
        repo="SelfNamingWidgetRepository",
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=[("slug", 'str = ""'), ("name", "str")],
        update_fields=[("name", "str")],
        out_dir=tmp_path / "id-type",
    )
    source = out_file.read_text()

    assert "slug=Slug(entity_id)" in source
    assert "from julee.core.entities.text import Slug" in source


def test_a_plain_str_id_is_not_wrapped(tmp_path: Path) -> None:
    """Nothing is wrapped that does not need wrapping."""
    out_file = generate(
        entity="Widget",
        entity_module=FIXTURES,
        repo="WidgetRepository",
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=[("slug", "str"), ("name", "str")],
        update_fields=[("name", "str")],
        out_dir=tmp_path / "plain-id",
    )
    source = out_file.read_text()

    assert "slug=entity_id" in source
    assert "str(entity_id)" not in source


async def test_an_entity_whose_id_is_a_property_is_not_handed_one(
    tmp_path: Path,
) -> None:
    """An id that is a property is derived, not chosen and not minted.

    c4's Relationship is named after its two ends. There is nothing
    for a caller to supply and no repository to ask, so the generated
    create must neither pass an id nor reach for generate_id — the
    repository has none, and asking would fail.
    """
    crud = _generate_widget_crud(
        tmp_path / "derived-id",
        create_fields=[("left", "str"), ("right", "str")],
        module_name="generated_derived_id",
        entity="DerivedIdWidget",
        repo="DerivedIdWidgetRepository",
    )
    repo = DerivedIdWidgetRepository()

    response = await crud.CreateDerivedIdWidgetUseCase(repo).execute(
        crud.CreateDerivedIdWidgetRequest(left="api", right="db")
    )

    assert response.derived_id_widget.slug == "api-to-db"
    assert await repo.get("api-to-db") is not None


async def test_updating_a_frozen_dataclass_entity(tmp_path: Path) -> None:
    """An update rebuilds a dataclass entity rather than model_copying it.

    The base class reached for model_copy, which a dataclass has not
    got. c4 found it the moment its entities stopped being pydantic —
    polling never did, having no CRUD at all.
    """
    crud = _generate_widget_crud(
        tmp_path / "update-dataclass",
        create_fields=[("left", "str"), ("right", "str")],
        module_name="generated_update_dataclass",
        entity="DerivedIdWidget",
        repo="DerivedIdWidgetRepository",
        update_fields=[("left", "str"), ("right", "str")],
    )
    repo = DerivedIdWidgetRepository()
    await crud.CreateDerivedIdWidgetUseCase(repo).execute(
        crud.CreateDerivedIdWidgetRequest(left="api", right="db")
    )

    response = await crud.UpdateDerivedIdWidgetUseCase(repo).execute(
        crud.UpdateDerivedIdWidgetRequest(slug="api-to-db", left="gateway")
    )

    assert response.derived_id_widget.left == "gateway"
    assert response.derived_id_widget.right == "db"


async def test_an_update_still_has_to_satisfy_the_entity(tmp_path: Path) -> None:
    """replace() runs __post_init__, so a rule survives an update.

    model_copy does not validate, which is the long-standing
    complaint about it. A dataclass gets the stronger behaviour for
    free, and this pins that it is actually happening.
    """
    crud = _generate_widget_crud(
        tmp_path / "update-validates",
        create_fields=[("slug", 'str = ""'), ("name", "str")],
        module_name="generated_update_validates",
        entity="CheckedWidget",
        repo="CheckedWidgetRepository",
        update_fields=[("name", "str")],
    )
    repo = CheckedWidgetRepository()
    await crud.CreateCheckedWidgetUseCase(repo).execute(
        crud.CreateCheckedWidgetRequest(slug="w", name="fine")
    )

    with pytest.raises(ValueError, match="may not be blank"):
        await crud.UpdateCheckedWidgetUseCase(repo).execute(
            crud.UpdateCheckedWidgetRequest(slug="w", name="")
        )
