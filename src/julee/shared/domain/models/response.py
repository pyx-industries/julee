"""Response model for Clean Architecture use case outputs."""

from julee.shared.domain.models.code_info import ClassInfo


class Response(ClassInfo):
    """The output boundary - data crossing out from the use case to the application.

    Responses are canonical models that carry the results of use case execution
    back across the boundary to the application layer. The application then
    serializes the Response for external consumption (JSON, terminal output,
    message payloads).

    The use case builds a Response containing exactly what the caller needs
    to know - no more, no less. A web controller serializes it to JSON. A
    CLI command formats it for terminal output. A message handler publishes
    it to a queue. Each adapts the same Response to their specific needs.

    Responses and Requests together form the "ports" in Ports and Adapters
    architecture. The use case defines these ports; the delivery mechanisms
    are adapters that plug into them. This inverts the typical dependency
    where business logic depends on web frameworks or ORMs.
    """

    pass  # Inherits all fields from ClassInfo
