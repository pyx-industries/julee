"""Tests for where each layer of a bounded context is read from."""

from pathlib import Path

import pytest

from julee.core import doctrine_constants
from julee.core.doctrine_constants import (
    DOMAIN_KIND_DIRECTORIES,
    DTOS_PATH,
    ENTITIES_PATH,
    ERRORS_PATH,
    REPOSITORIES_PATH,
    USE_CASES_PATH,
    VALUES_PATH,
)
from julee.core.parsers.layout import areas_of, kind_of, layer_files

pytestmark = pytest.mark.unit


def a_context(root: Path, *files: str) -> Path:
    """Write a bounded context holding the files named, each empty."""
    context = root / "ledger"
    for file in files:
        path = context / file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
    return context


def read_from(context: Path, layer: tuple[str, ...]) -> list[tuple[str, str]]:
    """Each module a layer is read from, and what its path is counted from."""
    return [
        (
            str(found.path.relative_to(context)),
            str(found.counted_from.relative_to(context)),
        )
        for found in layer_files(context, layer)
    ]


class TestAContextWithoutAreas:
    def test_a_layer_is_read_from_its_own_directory(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path, "domain/models/invoice.py", "domain/repositories/invoice.py"
        )

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models/invoice.py", "domain/models")
        ]
        assert read_from(context, REPOSITORIES_PATH) == [
            ("domain/repositories/invoice.py", "domain/repositories")
        ]
        assert areas_of(context) == []

    def test_a_layer_with_no_module_is_read_from_nothing(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "usecases/bill.py")

        assert read_from(context, ENTITIES_PATH) == []

    def test_what_is_beneath_a_kind_directory_belongs_to_the_kind(
        self, tmp_path: Path
    ) -> None:
        """A subdirectory of domain/models/ is more models, not an area,
        and a kind's name down there decides nothing."""
        context = a_context(
            tmp_path,
            "domain/models/billing/invoice.py",
            "domain/models/repositories/oddly_placed.py",
            "domain/models/errors.py",
        )

        assert areas_of(context) == []
        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models/billing/invoice.py", "domain/models"),
            ("domain/models/errors.py", "domain/models"),
            ("domain/models/repositories/oddly_placed.py", "domain/models"),
        ]
        assert read_from(context, REPOSITORIES_PATH) == []
        assert read_from(context, ERRORS_PATH) == []


class TestAnArea:
    def test_a_directory_under_domain_that_is_no_kinds_is_an_area(
        self, tmp_path: Path
    ) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert areas_of(context) == [context / "domain" / "billing"]

    def test_a_module_an_area_holds_is_read_as_entities(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/billing/invoice.py", "domain")
        ]

    def test_it_is_read_as_nothing_else(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "domain/billing/invoice.py")

        assert read_from(context, VALUES_PATH) == []
        assert read_from(context, REPOSITORIES_PATH) == []

    @pytest.mark.parametrize("kind", sorted(DOMAIN_KIND_DIRECTORIES))
    def test_a_kind_directory_in_an_area_is_read_as_that_kind(
        self, tmp_path: Path, kind: str
    ) -> None:
        context = a_context(tmp_path, f"domain/billing/{kind}/planning/invoice.py")

        assert read_from(context, ("domain", kind)) == [
            (f"domain/billing/{kind}/planning/invoice.py", "domain")
        ]

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
            ("domain/billing/invoice.py", "domain"),
            ("domain/billing/refunds/refund.py", "domain"),
        ]
        assert read_from(context, REPOSITORIES_PATH) == [
            ("domain/billing/refunds/repositories/refund.py", "domain")
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
        assert read_from(context, ENTITIES_PATH) == []


class TestAModuleDirectlyUnderDomain:
    def test_it_is_read_as_entities(self, tmp_path: Path) -> None:
        """domain/ is the outermost area."""
        context = a_context(tmp_path, "domain/__init__.py", "domain/ledger.py")

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/__init__.py", "domain"),
            ("domain/ledger.py", "domain"),
        ]
        assert areas_of(context) == []

    def test_the_layers_own_directory_comes_first(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path,
            "domain/ledger.py",
            "domain/billing/invoice.py",
            "domain/models/customer.py",
        )

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models/customer.py", "domain/models"),
            ("domain/billing/invoice.py", "domain"),
            ("domain/ledger.py", "domain"),
        ]


class TestAModuleNamedForAKind:
    @pytest.mark.parametrize("kind", sorted(DOMAIN_KIND_DIRECTORIES))
    def test_it_holds_that_kind_under_domain_and_in_an_area(
        self, tmp_path: Path, kind: str
    ) -> None:
        context = a_context(tmp_path, f"domain/{kind}.py", f"domain/billing/{kind}.py")

        assert read_from(context, ("domain", kind)) == [
            (f"domain/billing/{kind}.py", "domain"),
            (f"domain/{kind}.py", "domain"),
        ]

    @pytest.mark.parametrize("kind", sorted(DOMAIN_KIND_DIRECTORIES - {"models"}))
    def test_it_is_not_read_as_entities(self, tmp_path: Path, kind: str) -> None:
        context = a_context(tmp_path, f"domain/{kind}.py", f"domain/billing/{kind}.py")

        assert read_from(context, ENTITIES_PATH) == []

    def test_a_directory_and_a_module_of_one_kind_are_both_read(
        self, tmp_path: Path
    ) -> None:
        context = a_context(
            tmp_path, "domain/errors/billing.py", "domain/billing/errors.py"
        )

        assert read_from(context, ERRORS_PATH) == [
            ("domain/errors/billing.py", "domain/errors"),
            ("domain/billing/errors.py", "domain"),
        ]


class TestALayerOutsideDomain:
    @pytest.mark.parametrize("layer", [USE_CASES_PATH, DTOS_PATH])
    def test_it_has_one_directory_whatever_domain_holds(
        self, tmp_path: Path, layer: tuple[str, ...]
    ) -> None:
        name = "/".join(layer)
        context = a_context(
            tmp_path,
            "domain/billing/invoice.py",
            f"domain/{name}.py",
            f"{name}/billing/bill.py",
        )

        assert read_from(context, layer) == [(f"{name}/billing/bill.py", name)]


class TestWhatIsLeftOut:
    def test_test_files_are_left_out(self, tmp_path: Path) -> None:
        context = a_context(
            tmp_path,
            "domain/models/invoice.py",
            "domain/models/test_invoice.py",
            "domain/models/tests/factories.py",
            "domain/test_ledger.py",
            "domain/billing/test_invoice.py",
        )

        assert read_from(context, ENTITIES_PATH) == [
            ("domain/models/invoice.py", "domain/models")
        ]

    def test_a_file_that_is_not_python_is_left_out(self, tmp_path: Path) -> None:
        context = a_context(tmp_path, "domain/notes.txt", "domain/billing/notes.txt")

        assert read_from(context, ENTITIES_PATH) == []


class TestTheKindOfAFile:
    @pytest.mark.parametrize(
        ("file", "kind"),
        [
            ("domain/repositories/invoice.py", "repositories"),
            ("domain/billing/repositories/invoice.py", "repositories"),
            ("domain/billing/refunds/oracles/rates.py", "oracles"),
            ("domain/models/repositories/oddly_placed.py", "models"),
            ("domain/models/errors.py", "models"),
            ("domain/repositories.py", "repositories"),
            ("domain/billing/errors.py", "errors"),
            ("domain/billing/invoice.py", None),
            ("domain/ledger.py", None),
            ("infrastructure/repositories/invoice.py", None),
            ("usecases/bill.py", None),
            ("repositories.py", None),
        ],
    )
    def test_it_is_the_first_kind_named_on_the_way_down(
        self, file: str, kind: str | None
    ) -> None:
        assert kind_of(file.split("/")) == kind


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
