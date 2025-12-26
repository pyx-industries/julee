"""Response model for Clean Architecture use case outputs."""

from julee.core.entities.code_info import ClassInfo


class Response(ClassInfo):
    """The output contract that use cases return for Applications to serialize from.

    A Response defines what data a use case produces as its result. The use
    case constructs a Response containing exactly what callers need to know -
    no more, no less. Applications then serialize this Response for external
    consumption (JSON, terminal output, message payloads).

    This mirrors the Request pattern. Applications depend on the Response
    format defined by use cases, not the other way around. When you add a
    new Application, you write code that consumes the existing Response -
    you don't change the use case.

    Responses may reference entities but are not themselves entities. They
    are data transfer objects optimized for the boundary crossing, carrying
    exactly what the Application needs to present the result.
    """

    pass  # Inherits all fields from ClassInfo
