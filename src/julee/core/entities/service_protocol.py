"""ServiceProtocol model for Clean Architecture external service abstractions."""

from julee.core.entities.code_info import ClassInfo


class ServiceProtocol(ClassInfo):
    """A protocol bound to multiple entity types that performs transformation between them.

    Services and Repositories both use Dependency Inversion - the domain defines
    a protocol, infrastructure provides the implementation. But they differ in
    what they abstract:

        Repository: bound to ONE entity type → persistence operations
        Service:    bound to TWO+ entity types → transformation between them

    A repository knows how to persist a Journey. A service knows how to
    transform a PollingConfig into a PollingResult, or evaluate ClassInfo,
    MethodInfo, and FieldInfo to produce an EvaluationResult. The entity
    binding count is the defining distinction.

    This matters because it clarifies responsibility. If your "service" only
    touches one entity type, it's probably a repository in disguise. If your
    repository is juggling multiple entity types, it's doing too much and
    should be split or promoted to a service.

    Services may encapsulate external components (LLMs, APIs, third-party
    systems). When they do, the service represents a trust boundary - the
    use case delegates work to the external system and trusts the service
    to produce valid outputs. The service is accountable for the transformation:
    domain objects go in, domain objects come out. What happens inside -
    whether local computation or external API calls - is an implementation
    detail hidden behind the protocol.

    Service protocols live in the domain layer ({bc}/services/).
    Implementations live in infrastructure. The protocol declares WHAT
    transformation is needed; the implementation decides HOW.
    """

    pass  # Inherits all fields from ClassInfo
