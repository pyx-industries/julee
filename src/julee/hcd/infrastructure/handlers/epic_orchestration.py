"""Epic orchestration handler implementation.

Coarse-grained handler that wraps EpicOrchestrationUseCase.
Translates domain objects to use case requests, executes the use case,
and delegates detected conditions to fine-grained handlers.
"""

import logging
from typing import TYPE_CHECKING

from julee.core.entities.acknowledgement import Acknowledgement
from julee.hcd.entities.epic import Epic
from julee.hcd.use_cases.epic_orchestration import (
    EpicOrchestrationRequest,
    EpicOrchestrationUseCase,
)

if TYPE_CHECKING:
    from julee.hcd.services.epic_handlers import (
        EmptyEpicHandler,
        UnknownStoryRefHandler,
    )

logger = logging.getLogger(__name__)


class EpicOrchestrationHandler:
    """Coarse-grained handler for epic orchestration.

    Wraps EpicOrchestrationUseCase. Translates domain objects to requests,
    executes the use case, and delegates detected conditions to fine-grained
    handlers.
    """

    def __init__(
        self,
        orchestration_use_case: EpicOrchestrationUseCase,
        empty_epic_handler: "EmptyEpicHandler",
        unknown_story_ref_handler: "UnknownStoryRefHandler",
    ) -> None:
        """Initialize with internal use case and fine-grained handlers.

        Args:
            orchestration_use_case: Use case for condition detection
            empty_epic_handler: Handler for empty epic condition
            unknown_story_ref_handler: Handler for unknown story refs condition
        """
        self._use_case = orchestration_use_case
        self._empty_epic_handler = empty_epic_handler
        self._unknown_story_ref_handler = unknown_story_ref_handler

    async def handle(self, epic: Epic) -> Acknowledgement:
        """Handle epic orchestration.

        Translates epic to request, executes use case, delegates conditions.

        Args:
            epic: The epic to orchestrate

        Returns:
            Acknowledgement with aggregated handler results
        """
        # Translate domain object to request
        request = EpicOrchestrationRequest(epic=epic)

        # Execute internal use case
        response = await self._use_case.execute(request)

        # Process response - delegate to fine-grained handlers
        info: list[str] = []
        warnings: list[str] = []

        for condition in response.conditions:
            if condition.condition == "empty_epic":
                logger.info(
                    "Delegating empty epic condition",
                    extra={"epic_slug": condition.epic_slug},
                )
                ack = await self._empty_epic_handler.handle(epic)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

            elif condition.condition == "unknown_story_refs":
                logger.info(
                    "Delegating unknown story refs condition",
                    extra={
                        "epic_slug": condition.epic_slug,
                        "unknown_refs": condition.details.get("unknown_refs"),
                    },
                )
                unknown_refs = condition.details.get("unknown_refs", [])
                ack = await self._unknown_story_ref_handler.handle(epic, unknown_refs)
                info.extend(ack.info)
                warnings.extend(ack.warnings)

        return Acknowledgement.wilco(warnings=warnings, info=info)
