"""Doctrine about messages: what dtos/ holds, and how a message is named."""

from pathlib import Path

from julee.core.doctrine.resolution import message_verdicts
from julee.core.doctrine.rules.messages import (
    ambiguous_message_names,
    classes_in_dtos_that_are_not_messages,
)
from julee.core.infrastructure.repositories.introspection.census import take_census
from julee.core.parsers.ast import parse_bounded_context


class TestWhatDtosHolds:
    """Doctrine about the classes in a bounded context's dtos/."""

    def test_every_class_in_dtos_MUST_be_a_pydantic_model_or_an_enum(
        self, repo
    ) -> None:
        """A class in dtos/ MUST be a pydantic model, or an enum.

        dtos/ holds the messages at the driving port, and is the one
        package of a bounded context where pydantic lives (ADR 001). A
        class there is a message, found by where it sits (ADR 022), and
        a message is validated on the way in and serialised on the way
        out, so it is a pydantic BaseModel.

        An enum is allowed beside them. One that types a field of a
        message is part of what the message says, and has no better
        home.

        This reaches every class in the directory. A request no use case
        imports yet is held to it, and so is a message that is neither a
        request nor a response, which no other rule reads.
        """
        verdicts = []
        for context in repo.discover_all():
            info = parse_bounded_context(Path(context.path))
            if info is None:
                continue
            verdicts.extend(
                message_verdicts(
                    context.slug,
                    Path(context.path),
                    [(found.file, found.name) for found in info.dtos],
                )
            )

        violations = classes_in_dtos_that_are_not_messages(verdicts)

        assert not violations, "\n".join(violations)


class TestMessageIdentity:
    """Doctrine about names used to match messages to use cases."""

    def test_request_and_response_names_MUST_be_unambiguous(
        self, project_root, search_root, repo
    ) -> None:
        """A request or response name MUST identify one declaration per context.

        Doctrine matches messages by name. Two declarations of a message
        name in one bounded context cannot be distinguished by those
        checks, even when each use case imports the intended one.
        Repeated imports or re-exports of one declaration are allowed,
        as is the same message name in different bounded contexts.
        """
        census = take_census(project_root, search_root, repo)
        violations = ambiguous_message_names(census.contexts)

        assert not violations, "\n".join(violations)
