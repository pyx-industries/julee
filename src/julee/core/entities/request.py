"""Request model for Clean Architecture use case inputs."""

from julee.core.entities.code_info import ClassInfo


class Request(ClassInfo):
    """The input contract that Applications must serialize into to invoke a use case.

    A Request defines what data a use case needs to do its job. Applications -
    whether API endpoints, CLI commands, or workflow triggers - receive external
    input in various formats (JSON, arguments, message payloads) and serialize
    it into the Request. The use case receives a validated, typed object and
    doesn't know or care which Application sent it.

    This is Dependency Inversion at work. Applications depend on the Request
    format defined by use cases, not the other way around. The domain dictates
    what data it needs; Applications figure out how to provide it. When you
    add a new Application (say, a GraphQL endpoint), you write code that
    constructs the existing Request - you don't change the use case.

    Requests may reference entities but are not themselves entities. They are
    data transfer objects optimized for the boundary crossing, carrying exactly
    what the use case needs to begin its work.
    """

    pass  # Inherits all fields from ClassInfo
