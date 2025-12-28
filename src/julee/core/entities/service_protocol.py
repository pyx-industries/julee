"""ServiceProtocol model for Clean Architecture external service abstractions."""

from julee.core.entities.code_info import ClassInfo


class ServiceProtocol(ClassInfo):
    """A protocol bound to multiple entity types that performs transformation between them.

    Services do things. Not to be confused with repositories, which store things.

    Logically, a service might be a shim that delegates to an external actor in
    the digital supply chain - an LLM, a third-party API, a message broker. The
    use case delegates work to the service and trusts it to produce valid domain
    outputs. What happens inside - whether local computation or external API
    calls - is an implementation detail hidden behind the protocol. The result
    of the service's work is attributable to the service, making it a vertex in
    the trust graph.

    Entity Binding Doctrine
    -----------------------
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

    Interface Typing Doctrine
    -------------------------
    Service and repository protocols only deal in entities and simple primitives.
    No framework types, no infrastructure concerns - just domain language.

    Intra-BC services (bound to concepts within a single bounded context) tend
    to operate on domain entities directly. Cross-BC bridge services may decompose
    to primitives if that simplifies the mapping between contexts.

    Examples from the julee codebase:

    Intra-BC services (domain entities)::

        # PollerService: PollingConfig → PollingResult
        # Both entities from julee.contrib.polling.entities
        class PollerService(Protocol):
            async def poll_endpoint(self, config: PollingConfig) -> PollingResult: ...

        # SemanticEvaluationService: ClassInfo → EvaluationResult
        # Both entities from julee.core.entities
        class SemanticEvaluationService(Protocol):
            async def evaluate_class_docstring(self, class_info: ClassInfo) -> EvaluationResult: ...

    Bridge service (cross-BC, primitives)::

        # NewDataHandler bridges polling BC → CEAP BC
        # Uses primitives because polling doesn't know about CEAP entities
        class NewDataHandler(Protocol):
            async def handle(
                self,
                endpoint_id: str,
                content: bytes,
                content_hash: str,
            ) -> Acknowledgement: ...

    Service protocols live in the domain layer ({bc}/services/).
    Implementations live in infrastructure ({bc}/infrastructure/services/).
    The protocol declares WHAT transformation is needed; the implementation
    decides HOW.
    """

    pass  # Inherits all fields from ClassInfo
