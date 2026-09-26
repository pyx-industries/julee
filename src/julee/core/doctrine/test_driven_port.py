"""Driven port doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.port import (
    ROLES_BY_DIRECTORY,
    port_implementations_outside_infrastructure,
    ports_bound_to_entities_they_should_not_be,
    ports_misnamed_for_their_directory,
    protocols_in,
)
from julee.core.parsers.ast import parse_bounded_context, parse_python_classes


def _ports(contexts):
    """Every protocol under a named port directory, with where it was found."""
    ports = []
    for ctx in contexts:
        info = parse_bounded_context(Path(ctx.path))
        if info is None:
            continue
        # Handlers are read from wherever they sit, so pair each with the
        # directory it was actually found in: one in domain/services/ is a
        # placement objection, not a naming one.
        handlers_dir = Path(ctx.path) / "domain" / "handlers"
        in_own_directory = {cls.name for cls in parse_python_classes(handlers_dir)}
        found = {
            "services": list(info.service_protocols)
            + [h for h in info.handler_protocols if h.name not in in_own_directory],
            "handlers": [
                h for h in info.handler_protocols if h.name in in_own_directory
            ],
            "oracles": info.oracle_protocols,
            "calculators": info.calculator_protocols,
            "witnesses": info.witness_protocols,
        }
        for directory, classes in found.items():
            ports.extend(protocols_in(directory, classes, ctx.slug))
    return ports


class TestDrivenPortNaming:
    """Doctrine about what a driven port calls itself."""

    @pytest.mark.asyncio
    async def test_a_port_MUST_claim_a_role_its_directory_offers(self, repo):
        """A protocol under a port directory MUST be named for that port.

        ADR 016 names six driven ports on two axes: how many entities a
        port is bound to, and whether a workflow must reach it through an
        activity or may call it inline. The second axis is the one a
        reader cannot work out for themselves, and the name is where it
        is recorded.

        ``SchemaOracle`` says it must be reached through an activity.
        ``NewDataCalculator`` says it may be called from workflow code and
        will replay the same. ``ClockWitness`` says the runtime records
        what it said, so wrapping it in an activity would fetch something
        the history already holds.

        A repository is exempt from this rule and only this one: it
        declares itself by inheriting ``RepositoryOf[Entity]``, which mypy
        reads too, and the one-entity rule checks that instead.

        A handler found in domain/services/ is objected to for where it
        is rather than what it is called. It was the one port told apart
        by its name rather than its directory, which is the mechanism
        every other port stopped using in #175, and it has its own
        directory now (#256).
        """
        ports = _ports(await repo.list_all())

        violations = ports_misnamed_for_their_directory(ports)

        assert not violations, "Driven ports claiming no role:\n" + "\n".join(
            violations
        )


class TestDrivenPortBinding:
    """Doctrine about what a driven port is bound to."""

    @pytest.mark.asyncio
    async def test_an_oracle_or_witness_MUST_name_no_entity(
        self, repo, entity_names_by_context
    ):
        """Oracles and witnesses MUST NOT name an entity of their context.

        Both sit at arity zero on ADR 016's grid, for the same reason:
        what they deal in was never ours to model. An Oracle returns what
        the remote system said, in that system's currency; a Witness
        returns what the runtime recorded about the execution.

        A protocol here naming one of its own entities is something else
        wearing the wrong name. One entity is what a repository is bound
        to, and that is almost always the answer.

        Calculators are deliberately not checked. ADR 016 lets a
        calculator be bound to any number of entities, because what makes
        it one is that its answer follows from its arguments.
        """
        ports = _ports(await repo.list_all())

        violations = ports_bound_to_entities_they_should_not_be(
            ports, entity_names_by_context
        )

        assert not violations, "Ports bound to entities they should not be:\n" + (
            "\n".join(violations)
        )


class TestDrivenPortVisibility:
    """Doctrine about doctrine: that it can see the ports it checks."""

    @pytest.mark.asyncio
    async def test_a_port_package_MUST_yield_protocols_to_doctrine(self, repo):
        """A port directory with modules MUST parse to protocols.

        The canary, and the reason every port is found by its directory
        rather than by its name. A rule that finds nothing passes, and so
        does a rule finding nothing because it was looking in the wrong
        way: that is how twenty service protocols went unseen in #175,
        seven repository protocols in #231, and an entire entity package
        in #238. Each looked green.
        """
        objections = []
        for ctx in await repo.list_all():
            info = parse_bounded_context(Path(ctx.path))
            found = {
                "services": [] if info is None else info.service_protocols,
                "handlers": [] if info is None else info.handler_protocols,
                "oracles": [] if info is None else info.oracle_protocols,
                "calculators": [] if info is None else info.calculator_protocols,
                "witnesses": [] if info is None else info.witness_protocols,
            }
            handlers = found["handlers"]
            for directory in ROLES_BY_DIRECTORY:
                package = Path(ctx.path) / "domain" / directory
                modules = [
                    path for path in package.glob("*.py") if path.name != "__init__.py"
                ]
                if not modules:
                    continue
                read = len(found[directory])
                if directory == "services":
                    read += len(handlers)
                if read == 0:
                    objections.append(
                        f"{ctx.slug}: domain/{directory}/ holds "
                        f"{len(modules)} modules and doctrine read no "
                        f"protocol out of any of them"
                    )

        assert not objections, "Port packages doctrine cannot read:\n" + "\n".join(
            objections
        )


PORT_SUFFIXES = tuple(
    suffix for suffixes in ROLES_BY_DIRECTORY.values() for suffix in suffixes
)
"""Every name that claims one of ADR 016's five named roles."""


async def _classes_of_every_context(repo):
    """Every class of every bounded context, with its slug.

    Each class carries a path relative to its own context root, which is
    what the placement rule reads.
    """
    return [
        (ctx.slug, cls)
        for ctx in await repo.list_all()
        for cls in parse_python_classes(Path(ctx.path))
    ]


class TestDrivenPortPlacement:
    """Doctrine about what layer a driven port may be written in."""

    @pytest.mark.asyncio
    async def test_a_port_MUST_be_declared_or_implemented_nowhere_else(self, repo):
        """A class claiming a port role MUST sit in domain/ or infrastructure/.

        ADR 002 has said since it was written that a driven port lives in
        its own directory under ``domain/`` and its implementations in
        ``infrastructure/``. The naming rules above made the first half a
        claim doctrine checks. This is the second half, which was stated
        and never tested (#236).

        The suffix is a claim about reachability: ``*Oracle`` says a
        workflow must go through an activity, ``*Calculator`` says it need
        not. A class making that claim from ``usecases/`` or an ``apps/``
        layer is telling a reader it is a port while the layout says it is
        something else, and there is no way to tell which half is wrong by
        looking.

        Repositories are exempt, as they are from the naming rules: a
        repository declares itself by inheriting ``RepositoryOf[Entity]``,
        so its name claims nothing.
        """
        found = await _classes_of_every_context(repo)
        if not found:
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        violations = port_implementations_outside_infrastructure(found)

        assert not violations, (
            "Driven ports outside domain/ and infrastructure/:\n"
            + "\n".join(violations)
        )

    @pytest.mark.asyncio
    async def test_the_placement_rule_MUST_be_able_to_see_the_layout(self, repo):
        """The rule above MUST read paths it can recognise a layer from.

        A rule that finds nothing passes, and reads exactly like a rule
        over a codebase that complies. This one decides by the first
        components of each class's path, so it rests entirely on those
        paths being relative to the context root. If they ever stop
        being — absolute, or rooted somewhere else — every class would
        look like it sits in neither layer, and the rule would go from
        checking placement to asserting the parser's output shape.

        Reading no port-named class at all is not what this asks about:
        a kit of pure structure has no service and no oracle, and that
        is a fact about the kit rather than a broken walk.

        A codebase with no bounded contexts skips instead, which is how
        julee itself reports that its port rules have no subject (#240).
        """
        found = await _classes_of_every_context(repo)
        if not found:
            pytest.skip("No bounded contexts in target codebase — nothing to check")

        placed = [
            f"{slug}.{cls.name}"
            for slug, cls in found
            if cls.file.startswith(("domain/", "infrastructure/"))
        ]

        assert placed, (
            "The placement rule read no class under domain/ or "
            "infrastructure/, so it cannot tell a layer from a path and "
            "would pass whatever the codebase did"
        )
