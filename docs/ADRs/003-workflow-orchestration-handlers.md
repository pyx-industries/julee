# ADR 003: Workflow Orchestration via Handler Services

## Status

Draft

## Date

2025-12-28

## Context

Reusable modules like the Polling contrib need to trigger domain-specific workflows without knowing what those workflows are. For example, when the Polling module detects new data at an endpoint, it should trigger downstream processing - but the Polling module cannot know whether that processing is CEAP document capture, data transformation, or something else entirely.

This creates a cross-bounded-context orchestration problem:

1. **BC isolation**: Bounded contexts should not depend on each other's internals
2. **Reusability**: Contrib modules must work with any solution, not specific BCs
3. **Composition at deployment**: The "what happens next" decision belongs to the solution provider, not the reusable module

The question is: how does a use case hand off work to "whatever comes next" without knowing what that is?

One approach is a bridge pipeline - an intermediate workflow that understands both sides. The Polling app used this pattern with `PollingDataPreparationPipeline`, which understood polling results and how to trigger CEAP. This works but requires an extra pipeline for every integration point.

A cleaner approach is to inject the "what comes next" logic as a service dependency, letting the composition root wire up cross-BC coordination explicitly.

## Decision

Use cases SHALL hand off domain conditions to **handler services** rather than computing next actions themselves.

**Handlers are services.** They follow the same patterns as other services - a protocol in `services/`, implementations injected via DI. The term "handler" indicates a specific responsibility: accepting domain objects and deciding what to do with them. This is the "green-dotted-egg" principle: a use case recognizes a condition and hands off to a handler, without knowing what the handler does.

A handler has a **domain interface** - it accepts domain objects, not requests. What the handler does internally (call other use cases, queue work, send notifications, dispatch to Temporal) is the handler's business.

### The Pattern

```python
class CreateStoryUseCase:
    def __init__(
        self,
        repo: StoryRepository,
        orphan_story_handler: OrphanStoryHandler | None = None,  # optional for gradual adoption
    ):
        self.repo = repo
        self._orphan_story_handler = orphan_story_handler

    async def execute(self, request: CreateStoryRequest) -> CreateStoryResponse:
        story = Story(...)
        await self.repo.save(story)

        # Recognize domain condition, hand off to handler if configured
        if not story.epic_slug and self._orphan_story_handler is not None:
            await self._orphan_story_handler.handle(story)

        return CreateStoryResponse(story=story)
```

The use case's responsibility is:
1. Do its job (create the story)
2. Recognize domain conditions ("this story has no epic")
3. Hand off to the appropriate handler (if configured)
4. Done

The handler's responsibility is:
- Accept domain objects (or domain-relevant arguments)
- Do whatever it needs to do
- Return acknowledgement

### Principles

#### 1. Handlers Are Services

Handlers follow the same pattern as repositories - they have a domain-typed interface and are injected via dependency injection at construction time.

```python
class OrphanStoryHandler(Protocol):
    """Handler for stories created without an epic assignment."""

    async def handle(self, story: Story) -> Acknowledgement:
        """Handle an orphan story. Returns acknowledgement."""
        ...
```

The use case declares its handler dependencies. The DI container wires them up at composition time.

#### 2. Optional Handlers Enable Gradual Adoption

Handlers MAY be optional (`Handler | None = None`) to enable:
- Use cases that work standalone without orchestration
- Gradual migration from `next_action()` patterns
- Testing without handler configuration

```python
def __init__(
    self,
    repo: StoryRepository,
    orphan_handler: OrphanStoryHandler | None = None,  # optional
):
    self._orphan_handler = orphan_handler

async def execute(self, request):
    ...
    if condition and self._orphan_handler is not None:
        await self._orphan_handler.handle(entity)
```

When orchestration is required (not optional), omit the `| None`.

#### 3. Acknowledgement Semantics

Handlers return `Acknowledgement` using radio communication semantics:

- **Wilco** ("will comply"): Handler accepts and will process
- **Unable**: Handler cannot comply (resource constraints, invalid state, etc.)
- **Roger** ("received"): Handler acknowledges receipt but makes no commitment about whether it will act - the wilco/unable distinction is not provided

```python
class Acknowledgement(BaseModel):
    will_comply: bool | None = None  # None = roger (no commitment either way)
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []
    debug: list[str] = []

    @classmethod
    def wilco(cls, **messages) -> Acknowledgement:
        """Will comply - handler accepts and will process."""
        return cls(will_comply=True, **messages)

    @classmethod
    def unable(cls, **messages) -> Acknowledgement:
        """Unable to comply - handler cannot process."""
        return cls(will_comply=False, **messages)

    @classmethod
    def roger(cls, **messages) -> Acknowledgement:
        """Received - acknowledged, no commitment about action."""
        return cls(will_comply=None, **messages)
```

Usage:
```python
# Handler accepts and will process
return Acknowledgement.wilco()

# Handler accepts with warnings
return Acknowledgement.wilco(warnings=["Deprecated field used"])

# Handler cannot comply
return Acknowledgement.unable(errors=["Queue full, try again later"])

# Handler acknowledges receipt, makes no commitment
return Acknowledgement.roger(info=["Logged orphan story"])
```

What happens after acknowledgement is the handler's business. It might:
- Process immediately
- Queue for later processing
- Dispatch to Temporal
- Send to a message broker
- Do nothing (null handler for testing)

The use case doesn't know or care about how the handoff is handled, only whether it is handled.

#### 4. Handler Signatures Vary

Handler protocols are not limited to single-entity signatures. The signature should match the domain context:

```python
# Single entity
class OrphanStoryHandler(Protocol):
    async def handle(self, story: Story) -> Acknowledgement: ...

# Entity plus context
class UnknownPersonaHandler(Protocol):
    async def handle(self, story: Story, persona_name: str) -> Acknowledgement: ...

# Cross-BC with primitives (no shared domain types)
class NewDataHandler(Protocol):
    async def handle(
        self,
        endpoint_id: str,
        content: bytes,
        content_hash: str,
    ) -> Acknowledgement: ...
```

Cross-BC handlers use primitives because bounded contexts don't share domain types.

#### 5. Fine-Grained vs Coarse-Grained Handlers

Handlers come in two architectural patterns:

**Fine-grained handlers** have no internal use case. They interact directly with technology (logging, notifications, queues) without business logic:

```python
class LoggingOrphanStoryHandler:
    """Fine-grained: no internal use case, direct technology interaction."""

    async def handle(self, story: Story) -> Acknowledgement:
        logger.warning("Orphan story", extra={"slug": story.slug})
        return Acknowledgement.wilco(warnings=["Story not in any epic"])
```

**Coarse-grained handlers** trigger use cases. To avoid circular dependencies (handlers need use cases, use cases need handlers), use a **HandlerDispatcher** pattern with factories:

```python
# Core infrastructure - generic OrchestrationHandler
class OrchestrationHandler:
    """Routes handler invocations to use cases via factories."""

    def __init__(
        self,
        routes: list[tuple[
            Callable[[], UseCase],   # use case factory (lazy)
            Callable[..., Request],  # request builder
        ]],
    ):
        self._routes = routes

    async def handle(self, *args, **kwargs) -> Acknowledgement:
        for get_use_case, build_request in self._routes:
            use_case = get_use_case()  # lazy instantiation
            request = build_request(*args, **kwargs)
            await use_case.execute(request)
        return Acknowledgement.wilco()
```

The composition root wires factories, not instances:

```python
# dependencies.py - composition root
def get_handler_dispatcher() -> HandlerDispatcher:
    dispatcher = HandlerDispatcher()

    # Fine-grained handler (no use case dependency)
    dispatcher.register(OrphanStoryHandler, get_logging_orphan_handler())

    # Coarse-grained handler (routes to use cases via factories)
    dispatcher.register(
        OrphanStoryHandler,
        OrchestrationHandler(
            routes=[
                (get_assign_to_epic_use_case, lambda story: AssignToEpicRequest(story_slug=story.slug)),
                (get_notify_team_use_case, lambda story: NotifyRequest(message=f"Orphan: {story.slug}")),
            ]
        ),
    )
    return dispatcher

# Use case receives proxy from dispatcher
def get_create_story_use_case() -> CreateStoryUseCase:
    return CreateStoryUseCase(
        get_story_repository(),
        post_create_handler=get_handler_dispatcher().proxy_for(OrphanStoryHandler),
    )
```

This solves two problems:
1. **No circular dependencies** — factories are callables, not instances
2. **Lazy instantiation** — use cases are created at `handle()` time, eliminating bootstrapping order constraints

Which to use is a domain modelling decision:
- Simple actions (log, notify) → fine-grained handler
- Orchestration that triggers use cases → coarse-grained handler via dispatcher

#### 6. Handler Protocol Placement: With the Entity

When a handler protocol accepts an entity defined in a different BC than the use case that hands off to it, the protocol lives **with the entity's BC**, not the use case's BC.

For example, if `CreateStoryUseCase` lives in BC-X but `Story` is defined in BC-Y, `OrphanStoryHandler` lives in BC-Y (with `Story`).

Rationale:
- Handler signatures like `handle(story: Story)` are semantically bound to `Story`
- Multiple use cases may hand off to the same handler (e.g., `CreateStory` and `ImportStory` both produce orphan stories)
- The dependency graph stays clean: the use case BC already depends on the entity BC, so no new edges are introduced

#### 7. Cross-BC Coordination Is Composition

When work in one bounded context should trigger work in another (e.g., Polling detects new data that should trigger CEAP document capture), this is wired at composition time by the solution provider.

The Polling module doesn't know CEAP exists. It's injected with a handler:

```python
class NewDataDetectionUseCase:
    def __init__(
        self,
        poller_service: PollerService,
        new_data_handler: NewDataHandler | None = None,  # provided by solution
    ):
        ...
```

The solution provider creates a handler implementation that calls CEAP:

```python
class CeapDocumentCaptureHandler(NewDataHandler):
    """Solution-specific handler that bridges Polling to CEAP."""

    def __init__(self, capture_use_case: CaptureDocumentUseCase):
        self.capture_use_case = capture_use_case

    async def handle(self, endpoint_id, content, content_hash) -> Acknowledgement:
        request = CaptureDocumentRequest(...)
        await self.capture_use_case.execute(request)
        return Acknowledgement.wilco()
```

Cross-BC coordination is explicit and visible in the solution's composition root.

#### 8. Use Case Responsibility Is Limited

The use case knows:
- "If the egg has a green dot, I give it to the green-dotted-egg-handler"
- "My job is done after the handoff"

The use case does NOT know:
- What the handler does with the egg
- Which other use cases might be involved
- How to construct requests for those use cases
- The business rules for complex workflows

This is the "green-dotted-egg-handler" principle.

### Directory Conventions

Handler protocols and implementations follow consistent placement:

```
{bounded_context}/
├── services/
│   └── {entity}_handlers.py      # Handler protocols (e.g., story_handlers.py)
└── infrastructure/
    └── handlers/
        ├── __init__.py
        └── null_handlers.py      # Null implementations for testing
```

Example from HCD:
```
hcd/
├── services/
│   └── story_handlers.py         # OrphanStoryHandler, UnknownPersonaHandler protocols
└── infrastructure/
    └── handlers/
        └── null_handlers.py      # NullOrphanStoryHandler, etc.
```

## Consequences

### Positive

1. **Single responsibility**: Use cases do one thing - their primary job plus condition recognition
2. **Domain-level interfaces**: Handlers speak domain language, not use case DTOs
3. **Testable in isolation**: Use cases can be tested with null handlers
4. **Explicit composition**: Cross-BC workflows are visible in the composition root
5. **Flexible orchestration**: Handlers can implement any pattern (immediate, queued, Temporal, etc.)
6. **Reusable modules**: Contrib modules like Polling don't need to know about specific solutions
7. **Gradual adoption**: Optional handlers allow incremental migration

### Negative

1. **More interfaces**: Each orchestration point needs a handler protocol
2. **Migration effort**: Existing `next_action()` patterns need refactoring
3. **Composition complexity**: Solution providers must wire up handlers

### Neutral

1. **Handler implementations vary**: Some handlers are trivial, others complex - this is expected

## Alternatives Considered

### 1. Keep next_action() Pattern

Continue having use cases return suggested next actions.

**Rejected**: Mixes concerns. Use cases shouldn't know about other use cases or how to construct their requests.

### 2. Event-Based Orchestration

Use cases emit domain events, subscribers react.

**Rejected for now**: Adds infrastructure complexity (event bus). The handler pattern achieves the same decoupling with simpler mechanics. Events can be introduced later if needed.

### 3. Orchestration Service Layer

A dedicated orchestration layer that wraps use cases and decides what comes next.

**Rejected**: Creates a parallel hierarchy. The handler pattern achieves orchestration without a separate layer - handlers ARE the orchestration, injected where needed.

### 4. Saga Pattern

Implement distributed sagas for cross-BC workflows.

**Rejected for now**: Overkill for current needs. Handlers can implement saga-like patterns internally if needed. The framework doesn't need to mandate saga infrastructure.

## Implementation

Reference implementation exists in:

- `julee/core/entities/acknowledgement.py` - Acknowledgement entity
- `julee/core/services/handler.py` - Generic Handler protocol and documentation
- `julee/hcd/services/story_handlers.py` - HCD handler protocols
- `julee/hcd/infrastructure/handlers/null_handlers.py` - Null implementations
- `julee/contrib/polling/services/new_data_handler.py` - Cross-BC handler protocol
- `julee/contrib/polling/use_cases/new_data_detection.py` - Use case with optional handler

## References

- [ADR 001: Contrib Module Layout](./001-contrib-layout.md)
- Analysis of use cases across core, HCD, CEAP, and Polling bounded contexts
