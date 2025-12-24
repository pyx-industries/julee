"""Request model for Clean Architecture use case inputs."""

from julee.shared.entities.code_info import ClassInfo


class Request(ClassInfo):
    """The input boundary - data crossing into the use case from the application.

    Requests are canonical models that carry validated input across the boundary
    from the application layer into use cases. The application receives external
    data (JSON, CLI args, message payloads), deserializes it into a Request, and
    passes that Request to the use case.

    A web controller receives JSON and deserializes it into a Request. A CLI
    command gathers arguments and creates a Request. A message handler
    deserializes a payload into a Request. The use case doesn't know or care
    which one - it just receives a validated, typed Request object.

    This is Dependency Inversion at work. The outer layers (web, CLI) depend
    on the Request format defined by the inner layers (use cases), not the
    other way around. Your domain dictates what data it needs; the delivery
    mechanisms figure out how to provide it.
    """

    pass  # Inherits all fields from ClassInfo
