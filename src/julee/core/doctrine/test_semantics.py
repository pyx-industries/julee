"""Doctrine: what a solution holds true about its own words.

A kit publishes claims about how its terms line up with other kits'. A
solution reads them, accepts what it agrees with, and adds its own. These
rules check that the resulting set means something.

The decorators this replaces never checked anything: a relation was a
string argument nobody resolved, so one naming a class in a repository
the code could not even see survived for as long as nobody looked. The
point of moving claims into data is that data can be checked, and these
are the checks.

A claim's ends are dotted paths, deliberately. A near end is resolved by
reading the target's source, because the package publishing a claim is
in the tree doctrine was pointed at — so the answer is about that tree
and not about what happens to be installed where doctrine runs (#269).
A far end may name a kit this tree does not contain, so it falls back to
importing, and is only asked when its package is present.
"""

import importlib
from collections.abc import Mapping
from pathlib import Path

import pytest

from julee.core.doctrine.rules.semantics import (
    Resolver,
    claims_about_classes_not_owned,
    claims_about_missing_classes,
    claims_naming_missing_targets,
    claims_that_contradict,
    claims_that_do_not_resolve,
    claims_without_a_note,
)
from julee.core.entities.claim import Claim
from julee.core.semantics import (
    claim_packages,
    claims_from_toml,
    load_semantics,
    resolves_in,
    semantics_documents,
)


def _imports(dotted_path: str) -> bool:
    """Whether a dotted path names something importable from here.

    The fallback for an end whose package is not in the tree being
    checked — the kernel, or a kit the target depends on.

    Args:
        dotted_path: For example "julee.core.entities.claim.Claim"

    Returns:
        True if the module imports and holds that name
    """
    module_path, _, name = dotted_path.rpartition(".")
    if not module_path:
        return False
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return False
    return hasattr(module, name)


@pytest.fixture(scope="session")
def packages(project_root) -> Mapping[str, Path]:
    """Where each package publishing claims in this tree lives."""
    return claim_packages(project_root)


@pytest.fixture(scope="session")
def resolves(packages) -> Resolver:
    """Whether a dotted path names something, read from the target first.

    A package in the tree is answered for by its own source, which is
    the whole point: the same question gets the same answer whatever
    environment doctrine runs in. Anything else is asked of the
    interpreter, as before.
    """

    def resolve(dotted_path: str) -> bool:
        directory = packages.get(dotted_path.split(".")[0])
        if directory is not None:
            return resolves_in(dotted_path, directory)
        return _imports(dotted_path)

    return resolve


@pytest.fixture(scope="session")
def package_present(packages) -> Resolver:
    """Whether a path's package is somewhere this run can read it.

    In the tree, or installed. A far end in neither is the one case the
    rules deliberately let through.
    """

    def present(dotted_path: str) -> bool:
        root = dotted_path.split(".")[0]
        if root in packages:
            return True
        try:
            importlib.import_module(root)
        except ImportError:
            return False
        return True

    return present


@pytest.fixture(scope="session")
def claims(project_root, kits) -> tuple[Claim, ...]:
    """Everything the solution holds true, kit claims and its own."""
    return load_semantics(project_root, tuple(kits))


@pytest.fixture(scope="session")
def published(project_root) -> tuple[tuple[str, Claim], ...]:
    """What this codebase publishes, paired with the package publishing it.

    Found on disk rather than through the kit registry, because a kit is
    a julee solution in its own right and does not adopt itself. Reading
    only the adopted kits would mean a kit's own claims were checked by
    everyone except the kit that makes them.
    """
    found: list[tuple[str, Claim]] = []
    for document in semantics_documents(project_root):
        package = document.parent.name
        for claim in claims_from_toml(
            document.read_text(encoding="utf-8"), str(document)
        ):
            found.append((package, claim))
    return tuple(found)


class TestKitClaims:
    """Rules about what a kit may assert."""

    def test_a_kit_MUST_own_the_source_of_every_claim_it_makes(self, published) -> None:
        """A kit MUST only claim about classes it owns.

        A claim is a kit's view from where it stands. Claiming about two
        other kits' classes is speaking for people who did not ask, and
        the solution is the only thing entitled to do that.

        The far end is not checked here: naming a kit nobody has adopted
        is how a claim stays useful to solutions that adopt both.
        """
        trespass = claims_about_classes_not_owned(published)

        assert not trespass, (
            "Kits claiming about classes they do not own:\n"
            + "\n".join(f"  {t}" for t in trespass)
        )

    def test_a_kit_SHOULD_say_why_it_claims_what_it_does(self, published) -> None:
        """Every claim SHOULD carry a note.

        The note is the difference between documentation and
        configuration. A claim without one tells a reader that two
        classes are related but not why, which is the part they cannot
        work out for themselves.
        """
        silent = claims_without_a_note(published)

        assert not silent, "Claims with no note explaining them:\n" + "\n".join(
            f"  {s}" for s in silent
        )

    def test_a_kit_MUST_claim_about_classes_it_really_has(
        self, published, resolves
    ) -> None:
        """The source of every published claim MUST resolve.

        A kit checks its own near ends. The far end may well name a kit
        nobody here has installed, which is how a claim stays useful to
        solutions that adopt both, so only the near end is checked.

        Without this a kit's own claims would be checked by every
        solution that adopts it and by nobody in the kit itself, which
        is where a renamed class is actually noticed.
        """
        dangling = claims_about_missing_classes(published, resolves)

        assert not dangling, "Claims about classes that do not exist:\n" + "\n".join(
            f"  {d}" for d in dangling
        )

    def test_a_kit_MUST_name_a_target_correctly_when_it_can_be_checked(
        self, published, resolves, package_present
    ) -> None:
        """A far end MUST resolve when its package is installed here.

        Leaving every far end alone was too lenient. A claim about a kit
        nobody has installed cannot be checked, and that is the point of
        allowing it. But a claim about the kernel, or about a kit this
        one already depends on, is checkable — and a typo there is the
        very thing this design exists to catch.

        So the rule is what can be checked, is.
        """
        wrong = claims_naming_missing_targets(published, resolves, package_present)

        assert not wrong, (
            "Claims naming a class that does not exist, in a package that "
            "is installed:\n" + "\n".join(f"  {w}" for w in wrong)
        )


class TestSolutionSemantics:
    """Rules about what a solution holds true."""

    def test_every_claim_MUST_name_classes_that_exist(self, claims, resolves) -> None:
        """Both ends of every accepted claim MUST resolve.

        This is the check the decorators never had. A claim naming a
        class that has been renamed, moved or removed is worse than no
        claim: the documentation asserts a relationship to something that
        is not there.
        """
        dangling = claims_that_do_not_resolve(claims, resolves)

        assert not dangling, "Claims naming classes that do not exist:\n" + "\n".join(
            f"  {d}" for d in dangling
        )

    def test_claims_MUST_NOT_contradict_each_other(self, claims) -> None:
        """One pair of classes MUST NOT be claimed two ways.

        Two kits can each have a view of the same pair, and they may not
        agree. Resolving that is the solution's job, and it does so by
        declining one of them — not by holding both and letting whatever
        reads them last decide.
        """
        contradictions = claims_that_contradict(claims)

        assert not contradictions, (
            "The same pair of classes is claimed more than one way:\n"
            + "\n".join(f"  {c}" for c in contradictions)
        )
