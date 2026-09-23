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
from julee.core.usecases.tests.crud_fixtures import Widget, WidgetRepository

pytestmark = pytest.mark.unit

FIXTURES = "julee.core.usecases.tests.crud_fixtures"


def _generate_widget_crud(out_dir: Path) -> ModuleType:
    """Generate CRUD for the Widget fixture and import the result."""
    out_file = generate(
        entity="Widget",
        entity_module=FIXTURES,
        repo="WidgetRepository",
        repo_module=FIXTURES,
        id_field="slug",
        create_fields=[("name", "str"), ("colour", "str")],
        update_fields=[("name", "str"), ("colour", "str")],
        out_dir=out_dir,
    )
    spec = importlib.util.spec_from_file_location("generated_crud_widget", out_file)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generated_crud_widget"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def crud(tmp_path: Path) -> ModuleType:
    """The generated CRUD module for Widget."""
    return _generate_widget_crud(tmp_path)


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


def test_update_request_requires_only_the_id(crud: ModuleType) -> None:
    """An update names what changes; the id says what to change it on."""
    request = crud.UpdateWidgetRequest(slug="hammer")

    assert request.slug == "hammer"
    assert request.name is None


# =============================================================================
# What the generated use cases do
# =============================================================================


async def test_update_leaves_out_fields_the_request_did_not_name(
    crud: ModuleType,
) -> None:
    """The bug this test exists for: a partial update clobbered the rest."""
    repo = WidgetRepository()
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
    repo = WidgetRepository()
    repo.storage["hammer"] = Widget(slug="hammer", name="Hammer", colour="red")

    response = await crud.UpdateWidgetUseCase(repo).execute(
        crud.UpdateWidgetRequest(slug="hammer", colour=None)
    )

    assert response.widget.colour is None
    assert response.widget.name == "Hammer"


async def test_update_saves_what_it_returns(crud: ModuleType) -> None:
    """The response is not a preview; the repository has the same entity."""
    repo = WidgetRepository()
    repo.storage["hammer"] = Widget(slug="hammer", name="Hammer", colour="red")

    await crud.UpdateWidgetUseCase(repo).execute(
        crud.UpdateWidgetRequest(slug="hammer", name="Sledgehammer")
    )

    assert repo.storage["hammer"].name == "Sledgehammer"


async def test_updating_an_absent_entity_is_not_a_silent_create(
    crud: ModuleType,
) -> None:
    """Update means update."""
    repo = WidgetRepository()

    with pytest.raises(crud.EntityNotFoundError):
        await crud.UpdateWidgetUseCase(repo).execute(
            crud.UpdateWidgetRequest(slug="missing", name="Nothing")
        )
