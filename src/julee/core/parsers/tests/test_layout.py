"""Tests for where each layer of a bounded context is read from."""

from pathlib import Path

import pytest

from julee.core import doctrine_constants
from julee.core.doctrine_constants import (
    DOMAIN_KIND_DIRECTORIES,
    DTOS_PATH,
    ENTITIES_PATH,
    REPOSITORIES_PATH,
    USE_CASES_PATH,
    VALUES_PATH,
)
from julee.core.parsers.layout import (
    areas_of,
    kind_directory_of,
    layer_directories,
    python_files_in,
)

pytestmark = pytest.mark.unit


def a_context(root: Path, *files: str) -> Path:
    """Write a bounded context holding the files named, each empty."""
    context = root / "ledger"
    for file in files:
        path = context / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    return context


def read_from(context: Path, layer: tuple[str, ...]) -> list[tuple[str, bool]]:
    """Each directory a layer is read from, and whether with what is beneath it."""
    return [
        (str(found.path.relative_to(context)), found.with_subdirectories)
        for found in layer_directories(context, layer)
    ]


class TestAContextWithoutAreas:
    def test_a_layer_has_its_own_directory_and_no_other(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path, "domain/models/invoice.py", "domain/repositories/invoice.py"
        )

        assert read_from(context, ENTITIES_PATH) == [("domain/models", True)]
        assert read_from(context, REPOSITORIES_PATH) == [("domain/repositories", True)]
        assert areas_of(context) == []

    def test_its_own_directory_is_named_whether_or_not_it_exists(
        self, tmp_path: Path
    ) -> None:
        context = a_context(tmp_path, "usecases/bill.py")

        assert read_from(context, ENTITIES_PATH) == [("domain/models", True)]

    def test_what_is_beneath_a_kind_directory_belongs_to_the_kind(
        self, tmp_path: Path
    ) -> None:
        """A subdirectory of domain/models/ is more models, not an area,
        and a kind's name down there decides nothing."""
        context = a_context(
            tmp_path,
            "domain/models/billing/invoice.py",
            "domain/models/repositories/oddly_placed.py",
        )

        assert areas_of(context) == []
        assert read_from(context, ENTITIES_PATH) == [("domain/models", True)]
        assert read_from(context, REPOSITORIES_PATH) == [("domain/repositories", True)]


class TestAnArea:
    def test_a_directory_under_domain_that_is_no_kinds_is_an_area(
        self, tmp_path: Path
    ) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert areas_of(context) == [context / "domain" / "billing"]

    def test_an_area_is_read_as_entities_without_what_is_beneath_it(
        self, tmp_path: Path
    ) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models", True),
            ("domain/billing", False),
        ]

    def test_an_area_is_read_as_nothing_else(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert read_from(context, VALUES_PATH) == [("domain/values", True)]
        assert read_from(context, REPOSITORIES_PATH) == [("domain/repositories", True)]

    @pytest.mark.parametrize("kind", sorted(DOMAIN_KIND_DIRECTORIES))
    def test_a_kind_directory_in_an_area_is_read_as_that_kind(
        self, tmp_path: Path, kind: str
    ) -> None:
        context = a_context(tmp_path, f"domain/billing/{kind}/invoice.py")

        assert read_from(context, ("domain", kind))[-1] == (
            f"domain/billing/{kind}",
            True,
        )

    def test_a_kind_directory_in_an_area_is_not_an_area(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "domain/billing/repositories/invoice.py")

        assert areas_of(context) == [context / "domain" / "billing"]

    def test_an_area_may_hold_areas(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path,
            "domain/billing/invoice.py",
            "domain/billing/refunds/refund.py",
            "domain/billing/refunds/repositories/refund.py",
        )

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models", True),
            ("domain/billing", False),
            ("domain/billing/refunds", False),
        ]
        assert read_from(context, REPOSITORIES_PATH) == [
            ("domain/repositories", True),
            ("domain/billing/refunds/repositories", True),
        ]

    def test_areas_are_listed_in_the_same_order_every_time(
        self, tmp_path: Path
    ) -> None:
        context = a_context(
            tmp_path, "domain/shipping/parcel.py", "domain/billing/invoice.py"
        )

        assert [area.name for area in areas_of(context)] == ["billing", "shipping"]

    @pytest.mark.parametrize("name", ["__pycache__", ".cache", "tests"])
    def test_a_directory_nothing_is_read_from_is_not_an_area(
        self, tmp_path: Path, name: str
    ) -> None:
        context = a_context(tmp_path, f"domain/{name}/invoice.py")

        assert areas_of(context) == []

    def test_a_module_directly_under_domain_is_in_no_layer(
        self, tmp_path: Path
    ) -> None:
        context = a_context(tmp_path, "domain/errors.py")

        assert areas_of(context) == []
        assert read_from(context, ENTITIES_PATH) == [("domain/models", True)]


class TestALayerOutsideDomain:
    @pytest.mark.parametrize("layer", [USE_CASES_PATH, DTOS_PATH])
    def test_it_has_one_directory_whatever_domain_holds(
        self, tmp_path: Path, layer: tuple[str, ...]
    ) -> None:
        context = a_context(
            tmp_path, "domain/billing/invoice.py", "usecases/billing/bill.py"
        )

        assert read_from(context, layer) == [("/".join(layer), True)]


class TestTheFilesOfADirectory:
    def test_an_area_gives_only_its_own_modules(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path,
            "domain/billing/__init__.py",
            "domain/billing/invoice.py",
            "domain/billing/repositories/invoice.py",
        )
        _, area = layer_directories(context, ENTITIES_PATH)

        assert [path.name for path in python_files_in(area)] == [
            "__init__.py",
            "invoice.py",
        ]

    def test_a_kind_directory_gives_what_is_beneath_it_too(
        self, tmp_path: Path
    ) -> None:
        context = a_context(
            tmp_path,
            "domain/repositories/invoice.py",
            "domain/repositories/refunds/refund.py",
        )
        (own,) = layer_directories(context, REPOSITORIES_PATH)

        assert [path.name for path in python_files_in(own)] == [
            "invoice.py",
            "refund.py",
        ]

    def test_test_files_are_left_out(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path,
            "domain/models/invoice.py",
            "domain/models/test_invoice.py",
            "domain/models/tests/factories.py",
        )
        (own,) = layer_directories(context, ENTITIES_PATH)

        assert [path.name for path in python_files_in(own)] == ["invoice.py"]

    def test_a_directory_that_is_not_there_gives_nothing(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "usecases/bill.py")
        (own,) = layer_directories(context, ENTITIES_PATH)

        assert python_files_in(own) == []


class TestTheKindDirectoryOfAFile:
    @pytest.mark.parametrize(
        ("file", "kind"),
        [
            ("domain/repositories/invoice.py", "repositories"),
            ("domain/billing/repositories/invoice.py", "repositories"),
            ("domain/billing/refunds/oracles/rates.py", "oracles"),
            ("domain/models/repositories/oddly_placed.py", "models"),
            ("domain/billing/invoice.py", None),
            ("domain/errors.py", None),
            ("domain/repositories.py", None),
            ("infrastructure/repositories/invoice.py", None),
            ("usecases/bill.py", None),
        ],
    )
    def test_it_is_the_first_kind_named_on_the_way_down(
        self, file: str, kind: str | None
    ) -> None:
        assert kind_directory_of(file.split("/")) == kind


def test_every_layer_under_domain_is_a_kind() -> None:
    """The guard against a layer being added and read as an area.

    A layer path under domain/ that is missing from the kinds would have
    its directory taken for an area, and its classes read as entities.
    """
    declared = {
        getattr(doctrine_constants, name)[-1]
        for name in dir(doctrine_constants)
        if name.endswith("_PATH")
        and len(getattr(doctrine_constants, name)) > 1
        and getattr(doctrine_constants, name)[0] == "domain"
    }

    assert declared
    assert declared == DOMAIN_KIND_DIRECTORIES
