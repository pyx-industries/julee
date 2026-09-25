"""Driven port doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.
"""

from pathlib import Path

import pytest

from julee.core.doctrine.rules.port import (
    ROLES_BY_DIRECTORY,
    ports_bound_to_entities_they_should_not_be,
    ports_misnamed_for_their_directory,
    protocols_in,
)
from julee.core.parsers.ast import parse_bounded_context, parse_python_classes


def _ports_and_entities(contexts):
    """Every protocol under a named port directory, with its context's entities."""
    ports = []
    entity_names_by_context = {}
    for ctx in contexts:
        info = parse_bounded_context(Path(ctx.path))
        if info is None:
            continue
        entity_names_by_context[ctx.slug] = {e.name for e in info.entities}
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
    return ports, entity_names_by_context


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
        ports, _ = _ports_and_entities(await repo.list_all())

        violations = ports_misnamed_for_their_directory(ports)

        assert not violations, "Driven ports claiming no role:\n" + "\n".join(
            violations
        )


class TestDrivenPortBinding:
    """Doctrine about what a driven port is bound to."""

    @pytest.mark.asyncio
    async def test_an_oracle_or_witness_MUST_name_no_entity(self, repo):
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
        ports, entities = _ports_and_entities(await repo.list_all())

        violations = ports_bound_to_entities_they_should_not_be(ports, entities)

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
