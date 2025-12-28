"""Handler service pattern for workflow orchestration.

Handlers are a service pattern for "domain condition detected, hand off to
someone else." Handlers are how use cases are orchestrated. The handler
implementation knows what other actions are required; use cases know nothing
about orchestration.


What Handlers Are
-----------------

A handler is a service that accepts domain objects and returns an
Acknowledgement. Use cases recognize domain conditions (e.g., "this story
has no epic") and hand off to the appropriate handler. The use case's job
is done after the handoff.

All handlers are services. Not all services are handlers. The handler pattern
is specifically for "condition detected, hand off" - the handoff pattern.
Regular services may compute, transform, or validate. Handlers hand off.


The Green-Dotted-Egg-Handler Principle
--------------------------------------

A use case knows: "If the egg has a green dot, I give it to the
green-dotted-egg-handler."

A use case does NOT know:
- What the handler does with the egg
- Which other use cases might be involved
- How to construct requests for those use cases
- The business rules for complex workflows

The handler knows all of that. The use case doesn't need to.


Handler Interface Contract
--------------------------

The core Handler protocol is generic - it accepts any domain object and
returns Acknowledgement. Bounded contexts define their own handler protocols
typed to specific domain entities:

    class OrphanStoryHandler(Protocol):
        async def handle(self, story: Story) -> Acknowledgement:
            ...

    class NewDataHandler(Protocol):
        async def handle(self, endpoint: Endpoint, content: bytes) -> Acknowledgement:
            ...

After handing off, the use case may inspect the Acknowledgement for errors
or notes - but it doesn't know or care how the entity was handled:

- Call other use cases
- Queue work for later processing
- Dispatch to Temporal workflows
- Send to a message broker
- Do nothing (null handler for testing)


Handler Granularity
-------------------

The framework supports both fine-grained and coarse-grained handlers:

Fine-grained: one handler per domain condition
    orphan_story_handler: OrphanStoryHandler
    unknown_persona_handler: UnknownPersonaHandler

Coarse-grained: one handler decides internally
    story_post_create_handler: StoryPostCreateHandler

This is a domain modelling decision, not an architectural constraint.


Cross-BC Coordination
---------------------

When work in one bounded context should trigger work in another, the
coordination is wired at composition time by the solution provider.

The source BC doesn't know about the target BC. It's injected with a handler
whose implementation bridges the two:

    class CeapDocumentCaptureHandler(NewDataHandler):
        '''Solution-specific handler that bridges Polling to CEAP.'''

        def __init__(self, capture_use_case: CaptureDocumentUseCase):
            self.capture_use_case = capture_use_case

        async def handle(self, endpoint, content) -> Acknowledgement:
            request = CaptureDocumentRequest(...)
            await self.capture_use_case.execute(request)
            return Acknowledgement.accepted()

Cross-BC coordination is explicit and visible in the solution's composition
root.


Null Handler Pattern
--------------------

For testing and development, null handlers acknowledge without action:

    class NullOrphanStoryHandler(OrphanStoryHandler):
        async def handle(self, story: Story) -> Acknowledgement:
            return Acknowledgement.accepted()

This allows use cases to be tested in isolation.
"""

from typing import Protocol, TypeVar

from julee.core.entities.acknowledgement import Acknowledgement

T = TypeVar("T")


class Handler(Protocol[T]):
    """Generic handler protocol.

    Bounded contexts define their own handler protocols typed to specific
    domain entities. This generic protocol exists for type-system completeness.
    """

    async def handle(self, entity: T) -> Acknowledgement:
        """Handle a domain entity.

        Args:
            entity: The domain entity to handle.

        Returns:
            Acknowledgement indicating whether the handoff was accepted.
        """
        ...


__all__ = ["Handler", "Acknowledgement"]
