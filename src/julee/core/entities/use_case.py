"""UseCase model for Clean Architecture application layer."""

from julee.core.entities.code_info import ClassInfo


class UseCase(ClassInfo):
    """Application-specific business rules that orchestrate the flow of data.

    Use cases capture the business rules that are specific to your application.
    They tell the story of what the system does: "Create a Journey", "List
    Personas", "Validate a Document". Each use case is a complete, independent
    operation that could be triggered from any delivery mechanism.

    A use case knows about entities and calls them to do the real work. It
    coordinates the dance: fetch this, validate that, transform here, persist
    there. But it never knows HOW things are persisted or WHERE data comes
    from - it only knows WHAT needs to happen.

    The execute() method is the single entry point. It takes a Request (input)
    and returns a Response (output). This uniformity means any delivery
    mechanism - web controller, CLI command, message handler - can invoke
    any use case the same way. The use case is the API to your business logic.
    """

    pass  # Inherits all fields from ClassInfo
