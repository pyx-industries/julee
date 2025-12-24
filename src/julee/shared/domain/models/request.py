"""Request model for Clean Architecture use case inputs."""

from julee.shared.domain.models.code_info import ClassInfo


class Request(ClassInfo):
    """The input boundary - data crossing into the application from outside.

    Requests carry input across the boundary from the outer world into your
    use cases. They are the firewall between messy external data and your
    pristine domain.

    A web controller receives JSON, parses it, and creates a Request. A CLI
    command gathers arguments and creates a Request. A message handler
    deserializes a payload and creates a Request. The use case doesn't know
    or care which one - it just receives a validated, typed Request object.

    This is Dependency Inversion at work. The outer layers (web, CLI) depend
    on the Request format defined by the inner layers (use cases), not the
    other way around. Your domain dictates what data it needs; the delivery
    mechanisms figure out how to provide it.
    """

    pass  # Inherits all fields from ClassInfo
