"""Journey orchestration handler implementation.

Coarse-grained handler that wraps JourneyOrchestrationUseCase.
Translates domain objects to use case requests, executes the use case,
and delegates detected conditions to fine-grained handlers.
"""

import logging
from typing import TYPE_CHECKING

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.journey import Journey
from julee.hcd.use_cases.journey_orchestration import (
    JourneyOrchestrationRequest,
    JourneyOrchestrationUseCase,
)

if TYPE_CHECKING:
    from julee.hcd.services.journey_handlers import (
        EmptyJourneyHandler,
        UnknownJourneyEpicRefHandler,
        UnknownJourneyPersonaHandler,
        UnknownJourneyStoryRefHandler,
    )

logger = logging.getLogger(__name__)


class JourneyOrchestrationHandler:
    """Coarse-grained handler for journey orchestration.

    Wraps JourneyOrchestrationUseCase. Translates domain objects to requests,
    executes the use case, and delegates detected conditions to fine-grained
    handlers.
    """

    def __init__(
        self,
        orchestration_use_case: JourneyOrchestrationUseCase,
        unknown_persona_handler: "UnknownJourneyPersonaHandler",
        unknown_story_ref_handler: "UnknownJourneyStoryRefHandler",
        unknown_epic_ref_handler: "UnknownJourneyEpicRefHandler",
        empty_journey_handler: "EmptyJourneyHandler",
    ) -> None:
        """Initialize with internal use case and fine-grained handlers.

        Args:
            orchestration_use_case: Use case for condition detection
            unknown_persona_handler: Handler for unknown persona condition
            unknown_story_ref_handler: Handler for unknown story refs condition
            unknown_epic_ref_handler: Handler for unknown epic refs condition
            empty_journey_handler: Handler for empty journey condition
        """
        self._use_case = orchestration_use_case
        self._unknown_persona_handler = unknown_persona_handler
        self._unknown_story_ref_handler = unknown_story_ref_handler
        self._unknown_epic_ref_handler = unknown_epic_ref_handler
        self._empty_journey_handler = empty_journey_handler

    async def handle(self, journey: Journey) -> Acknowledgement:
        """Handle journey orchestration.

        Translates journey to request, executes use case, delegates conditions.

        Args:
            journey: The journey to orchestrate

        Returns:
            Acknowledgement with aggregated handler results
        """
        # Translate domain object to request
        request = JourneyOrchestrationRequest(journey=journey)

        # Execute internal use case
        response = await self._use_case.execute(request)

        # Process response - delegate to fine-grained handlers
        info: list[str] = []
        warnings: list[str] = []

        for condition in response.conditions:
            if condition.condition == "unknown_persona":
                logger.info(
                    "Delegating unknown persona condition",
                    extra={
                        "journey_slug": condition.journey_slug,
                        "persona": condition.details.get("persona_name"),
                    },
                )
                persona_name = condition.details.get("persona_name", "")
                ack = await self._unknown_persona_handler.handle(journey, persona_name)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

            elif condition.condition == "empty_journey":
                logger.info(
                    "Delegating empty journey condition",
                    extra={"journey_slug": condition.journey_slug},
                )
                ack = await self._empty_journey_handler.handle(journey)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

            elif condition.condition == "unknown_story_refs":
                logger.info(
                    "Delegating unknown story refs condition",
                    extra={
                        "journey_slug": condition.journey_slug,
                        "unknown_refs": condition.details.get("unknown_refs"),
                    },
                )
                unknown_refs = condition.details.get("unknown_refs", [])
                ack = await self._unknown_story_ref_handler.handle(journey, unknown_refs)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

            elif condition.condition == "unknown_epic_refs":
                logger.info(
                    "Delegating unknown epic refs condition",
                    extra={
                        "journey_slug": condition.journey_slug,
                        "unknown_refs": condition.details.get("unknown_refs"),
                    },
                )
                unknown_refs = condition.details.get("unknown_refs", [])
                ack = await self._unknown_epic_ref_handler.handle(journey, unknown_refs)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

        return Acknowledgement.wilco(warnings=warnings, info=info)
