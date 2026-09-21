"""Doctrine: kits a solution adopts.

A kit plugs domain code into a solution (ADR 012). These rules check the
adoption itself: that every kit the solution names is really there, that
the kits agree with each other, and that a kit's contexts do not collide
with the solution's own.

A kit's internals are not checked here. Each kit is a julee solution in
its own right and runs its own doctrine.
"""

import pytest

from julee.core.kits import adopted_kits, installed_kits, unresolved_kit_slugs


class TestKitAdoption:
    """Rules about which kits a solution adopts."""

    def test_adopted_kits_MUST_be_installed(self, project_root) -> None:
        """Every slug in [tool.julee] kits MUST name an installed kit.

        A slug that resolves to nothing is a silent hole: the solution
        believes it has adopted a kit whose contexts, policies and
        contributions are simply absent.
        """
        missing = unresolved_kit_slugs(project_root)

        assert not missing, (
            "[tool.julee] kits names kits that are not installed: "
            f"{', '.join(missing)}. Install the distribution that provides "
            "each one, or remove the slug."
        )

    def test_kit_requirements_MUST_be_adopted(self, project_root) -> None:
        """A kit's `requires` MUST also be adopted by the solution.

        Adoption is explicit, so a kit cannot pull in another kit on the
        solution's behalf. If ceap requires polling, the solution says so.
        """
        adopted = adopted_kits(project_root)
        slugs = {kit.slug for kit in adopted}

        violations = [
            f"{kit.slug} requires {required}, which is not adopted"
            for kit in adopted
            for required in kit.requires
            if required not in slugs
        ]

        assert not violations, "Unmet kit requirements:\n" + "\n".join(violations)

    def test_kit_requirements_MUST_NOT_be_circular(self, project_root) -> None:
        """Kit requirements MUST form a directed acyclic graph."""
        requirements = {
            kit.slug: set(kit.requires) for kit in adopted_kits(project_root)
        }

        def reaches(start: str, target: str, seen: set[str]) -> bool:
            for nxt in requirements.get(start, set()):
                if nxt == target or (
                    nxt not in seen and reaches(nxt, target, seen | {nxt})
                ):
                    return True
            return False

        cycles = [slug for slug in requirements if reaches(slug, slug, {slug})]

        assert (
            not cycles
        ), f"Kit requirements form a cycle involving: {', '.join(cycles)}"


class TestKitBoundary:
    """Rules about kits not colliding with the solution."""

    def test_kit_slugs_MUST_be_unique(self) -> None:
        """Two installed kits MUST NOT share a slug.

        The slug addresses a kit in [tool.julee] kits, so a duplicate makes
        adoption ambiguous.
        """
        slugs = [kit.slug for kit in installed_kits()]
        duplicates = {slug for slug in slugs if slugs.count(slug) > 1}

        assert (
            not duplicates
        ), f"Installed kits share slugs: {', '.join(sorted(duplicates))}"

    def test_kit_slugs_MUST_NOT_collide_with_bounded_contexts(
        self, project_root, repo
    ) -> None:
        """A kit slug MUST NOT be the slug of the solution's own context.

        Both are names in the same namespace as far as a reader is
        concerned, and doctrine reports on both.
        """
        kit_slugs = {kit.slug for kit in adopted_kits(project_root)}
        context_slugs = {context.slug for context in repo.discover_all()}
        collisions = kit_slugs & context_slugs

        assert not collisions, (
            "Kit slugs collide with bounded context slugs: "
            f"{', '.join(sorted(collisions))}"
        )


class TestKitManifests:
    """Rules about what a manifest says."""

    def test_kit_packages_MUST_be_importable(self, project_root) -> None:
        """A kit's declared package MUST be importable.

        The package is how doctrine and the documentation find the kit's
        bounded contexts. A manifest naming a package that is not there
        describes a kit nobody can use.
        """
        import importlib.util

        adopted = adopted_kits(project_root)
        if not adopted:
            pytest.skip("Solution adopts no kits")

        violations = []
        for kit in adopted:
            try:
                spec = importlib.util.find_spec(kit.package)
            except (ImportError, ValueError):
                spec = None
            if spec is None:
                violations.append(f"{kit.slug} declares package {kit.package}")

        assert not violations, "Kit packages not importable:\n" + "\n".join(violations)

    def test_kit_contributions_MUST_name_a_module_and_attribute(
        self, project_root
    ) -> None:
        """A contribution MUST be a dotted path, optionally with `:attr`.

        Contributions are paths rather than objects so that reading a
        manifest imports nothing. The path is checked for shape here;
        resolving it is the job of whichever integration consumes it.
        """
        violations = [
            f"{kit.slug}: {point} = {path!r}"
            for kit in adopted_kits(project_root)
            for point, path in kit.contributes.items()
            if not path or path.count(":") > 1 or " " in path
        ]

        assert not violations, "Malformed kit contributions:\n" + "\n".join(violations)
