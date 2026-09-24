"""What the semantics rules object to.

Each function takes what a codebase publishes or holds true and returns
the objections, as sentences someone can act on. None of them touches a
filesystem or imports anything: whether a dotted path names something is
asked of a resolver passed in, so a test can answer that question itself
rather than arranging for classes to exist.
"""

from collections.abc import Callable, Iterable

from julee.core.entities.claim import Claim

__all__ = [
    "Resolver",
    "claims_about_classes_not_owned",
    "claims_about_missing_classes",
    "claims_naming_missing_targets",
    "claims_that_contradict",
    "claims_that_do_not_resolve",
    "claims_without_a_note",
]

Resolver = Callable[[str], bool]
"""Answers whether a dotted path names something that exists."""

Published = Iterable[tuple[str, Claim]]
"""Claims paired with the package publishing them."""


def claims_about_classes_not_owned(published: Published) -> list[str]:
    """Claims a package makes about classes belonging to somebody else.

    A claim is a kit's view from where it stands. Claiming about two
    other kits' classes is speaking for people who did not ask; the
    solution is the only thing entitled to do that.

    Args:
        published: Claims paired with the package publishing them

    Returns:
        One sentence per trespass
    """
    return [
        f"{package} claims {claim.id!r} about {claim.source}, which it does not own"
        for package, claim in published
        if not claim.source.startswith(f"{package}.")
    ]


def claims_without_a_note(published: Published) -> list[str]:
    """Claims that do not say why they are made.

    The note is the difference between documentation and configuration.
    Without it a reader learns that two classes are related but not why,
    which is the part they cannot work out for themselves.

    Args:
        published: Claims paired with the package publishing them

    Returns:
        One sentence per silent claim
    """
    return [
        f"{package}: {claim.id}"
        for package, claim in published
        if not claim.note.strip()
    ]


def claims_about_missing_classes(published: Published, resolves: Resolver) -> list[str]:
    """Claims whose own end does not name anything.

    A kit checks its near ends. The far end may name a kit nobody here
    has installed, which is how a claim stays useful to a solution that
    later adopts both, so it is left to another rule.

    Args:
        published: Claims paired with the package publishing them
        resolves: Answers whether a dotted path names something

    Returns:
        One sentence per claim about a class that is not there
    """
    return [
        f"{package}: {claim.id} claims about {claim.source}"
        for package, claim in published
        if not resolves(claim.source)
    ]


def claims_naming_missing_targets(
    published: Published,
    resolves: Resolver,
    package_present: Resolver,
) -> list[str]:
    """Claims whose far end is checkable and wrong.

    A claim about a kit nobody has installed cannot be checked, and
    allowing that is the point. A claim about the kernel, or about a kit
    this one already depends on, can be checked — so it is.

    Args:
        published: Claims paired with the package publishing them
        resolves: Answers whether a dotted path names something
        package_present: Answers whether a path's package is installed

    Returns:
        One sentence per far end that is present but wrong
    """
    return [
        f"{package}: {claim.id} names {claim.target}"
        for package, claim in published
        if package_present(claim.target) and not resolves(claim.target)
    ]


def claims_that_do_not_resolve(
    claims: Iterable[Claim], resolves: Resolver
) -> list[str]:
    """Accepted claims with an end that names nothing.

    What a solution holds true is checked at both ends, because by then
    every kit it names has been adopted and installed.

    Args:
        claims: What the solution holds true
        resolves: Answers whether a dotted path names something

    Returns:
        One sentence per end that is not there
    """
    return [
        f"{claim.id}: {end}"
        for claim in claims
        for end in (claim.source, claim.target)
        if not resolves(end)
    ]


def claims_that_contradict(claims: Iterable[Claim]) -> list[str]:
    """Pairs of classes claimed more than one way.

    Two kits can each have a view of the same pair and disagree.
    Resolving that is the solution's job, done by declining one — not by
    holding both and letting whatever reads them last decide.

    Args:
        claims: What the solution holds true

    Returns:
        One sentence per contradicted pair
    """
    kinds: dict[tuple[str, str], dict[str, list[str]]] = {}
    for claim in claims:
        by_kind = kinds.setdefault((claim.source, claim.target), {})
        by_kind.setdefault(str(claim.kind), []).append(claim.id)

    return [
        f"{source} -> {target}: "
        + ", ".join(
            f"{claim_id} ({kind})"
            for kind, ids in sorted(by_kind.items())
            for claim_id in ids
        )
        for (source, target), by_kind in kinds.items()
        if len(by_kind) > 1
    ]
