"""Doctrine: what a solution holds true about its own words.

A kit publishes claims about how its terms line up with other kits'. A
solution reads them, accepts what it agrees with, and adds its own. These
rules check that the resulting set means something.

The decorators this replaces never checked anything: a relation was a
string argument nobody resolved, so one naming a class in a repository
the code could not even see survived for as long as nobody looked. The
point of moving claims into data is that data can be checked, and these
are the checks.

A claim's ends are dotted paths, deliberately. Importing them here is
safe in a way that importing them at declaration time was not: doctrine
runs against an assembled solution where every adopted kit is installed,
which is exactly when the question "does this name anything?" has an
answer.
"""

import importlib

import pytest

from julee.core.entities.claim import Claim
from julee.core.semantics import kit_claims, load_semantics


def _resolves(dotted_path: str) -> bool:
    """Whether a dotted path names something that exists.

    Args:
        dotted_path: For example "julee_hcd.domain.models.story.Story"

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
def claims(project_root, kits) -> tuple[Claim, ...]:
    """Everything the solution holds true, kit claims and its own."""
    return load_semantics(project_root, tuple(kits))


class TestKitClaims:
    """Rules about what a kit may assert."""

    def test_a_kit_MUST_own_the_source_of_every_claim_it_makes(self, kits) -> None:
        """A kit MUST only claim about classes it owns.

        A claim is a kit's view from where it stands. Claiming about two
        other kits' classes is speaking for people who did not ask, and
        the solution is the only thing entitled to do that.

        The far end is not checked here: naming a kit nobody has adopted
        is how a claim stays useful to solutions that adopt both.
        """
        trespass = []
        for kit in kits:
            for claim in kit_claims(kit):
                if not claim.source.startswith(f"{kit.package}."):
                    trespass.append(
                        f"{kit.slug} claims {claim.id!r} about "
                        f"{claim.source}, which it does not own"
                    )

        assert (
            not trespass
        ), "Kits claiming about classes they do not own:\n" + "\n".join(
            f"  {t}" for t in trespass
        )

    def test_a_kit_SHOULD_say_why_it_claims_what_it_does(self, kits) -> None:
        """Every claim SHOULD carry a note.

        The note is the difference between documentation and
        configuration. A claim without one tells a reader that two
        classes are related but not why, which is the part they cannot
        work out for themselves.
        """
        silent = [
            f"{kit.slug}: {claim.id}"
            for kit in kits
            for claim in kit_claims(kit)
            if not claim.note.strip()
        ]

        assert not silent, "Claims with no note explaining them:\n" + "\n".join(
            f"  {s}" for s in silent
        )


class TestSolutionSemantics:
    """Rules about what a solution holds true."""

    def test_every_claim_MUST_name_classes_that_exist(self, claims) -> None:
        """Both ends of every accepted claim MUST resolve.

        This is the check the decorators never had. A claim naming a
        class that has been renamed, moved or removed is worse than no
        claim: the documentation asserts a relationship to something that
        is not there.
        """
        dangling = [
            f"{claim.id}: {end}"
            for claim in claims
            for end in (claim.source, claim.target)
            if not _resolves(end)
        ]

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
        kinds: dict[tuple[str, str], list[str]] = {}
        for claim in claims:
            kinds.setdefault((claim.source, claim.target), []).append(
                f"{claim.id} ({claim.kind})"
            )

        contradictions = [
            f"{source} -> {target}: {', '.join(found)}"
            for (source, target), found in kinds.items()
            if len({f.split("(")[1] for f in found}) > 1
        ]

        assert (
            not contradictions
        ), "The same pair of classes is claimed more than one way:\n" + "\n".join(
            f"  {c}" for c in contradictions
        )
