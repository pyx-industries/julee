"""Boundary doctrine.

ADR 012 §3 says who may reach across the kit boundary, and for a long
time said it only in prose. These are those rules.

They read a solution's own source. Which is a departure: most doctrine
asks a repository what classes a codebase has, and this asks what its
files import, because an import is not a class and does not appear in
ClassInfo.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.boundary import (
    imports_of_unadopted_kits,
    imports_reaching_into_a_kit,
    within_a_composition_root,
)
from julee.core.infrastructure.repositories.file.solution_config import (
    FileSolutionConfigRepository,
)
from julee.core.kits import adopted_kits, installed_kits, own_packages
from julee.core.parsers.imports import imports_under


class TestKitAdoptionIsHonoured:
    """Rules about depending on what the solution declared."""

    def test_a_solution_MUST_NOT_import_an_unadopted_kit(
        self, project_root, search_root
    ) -> None:
        """A solution MUST NOT import a kit it has not adopted.

        Adoption is what makes a kit part of a solution. One that
        happens to be installed, pulled in by something else, is not:
        importing it anyway means depending on something the solution
        never declared and nothing will keep installing for it.
        """
        source = project_root / search_root
        adopted = {kit.slug for kit in adopted_kits(project_root)}
        unadopted = {
            kit.package: kit.slug
            for kit in installed_kits()
            if kit.slug not in adopted and kit.package not in own_packages(project_root)
        }
        if not unadopted:
            pytest.skip("Every installed kit is adopted — nothing to check")

        violations = imports_of_unadopted_kits(imports_under(source), unadopted)

        assert not violations, "Imports of unadopted kits:\n" + "\n".join(
            f"  {v}" for v in violations
        )


class TestKitInternalsAreTheKitsOwn:
    """Rules about how far into a kit a solution may reach."""

    def test_only_a_composition_root_MAY_import_a_kit_s_internals(
        self, project_root, search_root
    ) -> None:
        """A bounded context MUST NOT import a kit's infrastructure or apps.

        A kit's entities, use cases and protocols are what it offers.
        How it stores things and how it is served are its own business,
        and a bounded context reaching for either couples itself to
        decisions the kit is entitled to change.

        A composition root may: wiring a repository implementation in is
        what a composition root is for. Which directories hold one is
        declared in [tool.julee] composition_roots, defaulting to apps/,
        because the role is not always held by a directory of that name.
        """
        packages = [kit.package for kit in adopted_kits(project_root)]
        if not packages:
            pytest.skip("Solution adopts no kits — nothing to reach into")

        roots = (
            FileSolutionConfigRepository()
            .get_policy_config_sync(project_root)
            .composition_roots
        )
        source = project_root / search_root
        outside = [
            info
            for info in imports_under(source)
            if not within_a_composition_root(
                Path(info.file).relative_to(source).parts, roots
            )
        ]

        violations = imports_reaching_into_a_kit(outside, packages)

        assert (
            not violations
        ), "Bounded contexts reaching into a kit's internals:\n" + "\n".join(
            f"  {v}" for v in violations
        )
