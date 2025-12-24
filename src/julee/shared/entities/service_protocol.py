"""ServiceProtocol model for Clean Architecture external service abstractions."""

from julee.shared.domain.models.code_info import ClassInfo


class ServiceProtocol(ClassInfo):
    """An abstraction that isolates the domain from external services.

    Your business logic needs to call an LLM, validate against an API, or
    send a notification. But if it calls OpenAI directly, you've coupled
    your domain to a vendor. When OpenAI changes their API - or you switch
    to Anthropic - your business logic breaks. This is backwards.

    Service protocols flip this dependency. The domain declares what it
    needs: "I need something that can generate embeddings." The protocol
    defines that interface. The infrastructure provides an implementation
    that happens to use OpenAI today, maybe Anthropic tomorrow.

    This is the same Dependency Inversion as repositories, applied to
    external services. The domain owns the interface. External services
    are mere plugins that can be swapped without touching business logic.

    Like repositories, service protocols live in the domain layer
    ({bc}/domain/services/). Implementations that talk to real services
    live in infrastructure ({bc}/services/). The boundary is sacred.
    """

    pass  # Inherits all fields from ClassInfo
