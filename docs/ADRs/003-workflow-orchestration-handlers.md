# ADR 003: Workflow Orchestration via Handler Services

## Status

Draft

## Date

2025-12-28

## Context

Use cases in the Julee framework currently have a `next_action()` method pattern that suggests follow-up operations after a use case completes. For example, after creating a story without an epic, the use case might suggest "assign to epic" as a next action.

This approach has problems:

1. **Mixed concerns**: Use cases know too much about workflow orchestration - which other use cases exist, how to construct their requests, and the business rules for when they're appropriate.

2. **Wrong interface**: The `next_action()` pattern returns request/response objects (use case DTOs), but workflow decisions should be expressed in terms of domain objects.

3. **Inverted responsibility**: Services translate between domain objects and use case requests. Use cases translate requests into domain operations. If "what comes next" is a domain-level decision, it belongs where domain context is understood.

The current pattern:

```python
class CreateStoryUseCase:
    def next_actions(self, response) -> list[SuggestedRequest]:
        # Use case knows about other use cases and their requests
        if not response.story.epic_slug:
            return [AssignToEpicRequest(story_slug=response.story.slug)]
        return []
```

This couples the use case to knowledge it shouldn't have.

## Decision

Use cases SHALL hand off domain conditions to **handler services** rather than computing next actions themselves.

A handler is a service with a **domain interface** - it accepts domain objects, not requests. What the handler does internally (call other use cases, queue work, send notifications, dispatch to Temporal) is the handler's business.

### The Pattern

```python
class CreateStoryUseCase:
    def __init__(
        self,
        repo: StoryRepository,
        orphan_story_handler: OrphanStoryHandler,  # service, injected via DI
    ):
        self.repo = repo
        self.orphan_story_handler = orphan_story_handler

    async def execute(self, request: CreateStoryRequest) -> CreateStoryResponse:
        story = Story(...)
        await self.repo.save(story)

        # Recognize domain condition, hand off to handler
        if not story.epic_slug:
            await self.orphan_story_handler.handle(story)

        return CreateStoryResponse(story=story)
```

The use case's responsibility is:
1. Do its job (create the story)
2. Recognize domain conditions ("this story has no epic")
3. Hand off to the appropriate handler
4. Done

The handler's responsibility is:
- Accept domain objects
- Do whatever it needs to do
- Return acknowledgement (or richer response if needed)

### Principles

#### 1. Handlers Are Services

Handlers follow the same pattern as repositories - they have a domain-typed interface and are injected via dependency injection at construction time.

```python
class OrphanStoryHandler(Protocol):
    """Handler for stories created without an epic assignment."""

    async def handle(self, story: Story) -> Acknowledgement:
        """Handle an orphan story. Returns acknowledgement of receipt."""
        ...
```

The use case declares its handler dependencies. The DI container wires them up at composition time.

#### 2. Handlers Return Something

Handler calls are blocking - the use case needs to know the handoff succeeded. At minimum, handlers return `Acknowledgement` ("received, thanks"). If the use case needs more information, the handler returns a richer response.

```python
# Minimal: just acknowledge receipt
ack = await self.orphan_story_handler.handle(story)

# Richer: handler returns useful information
result = await self.validation_handler.handle(document)
if result.requires_transformation:
    ...
```

What happens after acknowledgement is the handler's business. It might:
- Process immediately
- Queue for later processing
- Dispatch to Temporal
- Send to a message broker
- Do nothing (null handler for testing)

The use case doesn't know or care.

#### 3. Granularity Is a Business Decision

The framework supports both fine-grained and coarse-grained handlers:

```python
# Fine-grained: one handler per condition
orphan_story_handler: OrphanStoryHandler
unknown_persona_handler: UnknownPersonaHandler

# Coarse-grained: one handler decides internally
story_post_create_handler: StoryPostCreateHandler
```

This is a domain modelling decision, not an architectural constraint.

#### 4. Cross-BC Coordination Is Composition

When work in one bounded context should trigger work in another (e.g., Polling detects new data that should trigger CEAP document capture), this is wired at composition time by the solution provider.

The Polling module doesn't know CEAP exists. It's injected with a handler:

```python
class NewDataDetectionUseCase:
    def __init__(
        self,
        new_data_handler: NewDataHandler,  # provided by solution
    ):
        ...
```

The solution provider creates a handler implementation that calls CEAP:

```python
class CeapDocumentCaptureHandler(NewDataHandler):
    """Solution-specific handler that bridges Polling to CEAP."""

    def __init__(self, capture_use_case: CaptureDocumentUseCase):
        self.capture_use_case = capture_use_case

    async def handle(self, endpoint: Endpoint, content: bytes) -> Acknowledgement:
        request = CaptureDocumentRequest(...)
        await self.capture_use_case.execute(request)
        return Acknowledgement(received=True)
```

Cross-BC coordination is explicit and visible in the solution's composition root.

#### 5. Use Case Responsibility Is Limited

The use case knows:
- "If the egg has a green dot, I give it to the green-dotted-egg-handler"
- "My job is done after the handoff"

The use case does NOT know:
- What the handler does with the egg
- Which other use cases might be involved
- How to construct requests for those use cases
- The business rules for complex workflows

This is the "green-dotted-egg-handler" principle.

## Consequences

### Positive

1. **Single responsibility**: Use cases do one thing - their primary job plus condition recognition
2. **Domain-level interfaces**: Handlers speak domain language, not use case DTOs
3. **Testable in isolation**: Use cases can be tested with stub handlers
4. **Explicit composition**: Cross-BC workflows are visible in the composition root
5. **Flexible orchestration**: Handlers can implement any pattern (immediate, queued, Temporal, etc.)
6. **Reusable modules**: Contrib modules like Polling don't need to know about specific solutions

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

## References

- [ADR 001: Contrib Module Layout](./001-contrib-layout.md)
- Analysis of use cases across core, HCD, CEAP, and Polling bounded contexts
