"""Doctrine about the identity of requests and responses."""

from julee.core.doctrine.rules.messages import ambiguous_message_names
from julee.core.infrastructure.repositories.introspection.census import take_census


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
