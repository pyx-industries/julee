"""ProjectOutputUseCase - project PipelineOutput to Digital Product Passport.

Maps a PipelineOutput (artifact produced by pipeline execution) to a
Digital Product Passport (DPP), linking to all traceability events
from the executions that produced the output.
"""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel

from julee.core.decorators import use_case
from julee.core.entities.pipeline_output import PipelineOutput

from julee.contrib.untp.entities.core import Identifier, Organization, SecureLink
from julee.contrib.untp.entities.credential import (
    DigitalProductPassport,
    DPPSubject,
)


class ProjectOutputRequest(BaseModel):
    """Request to project a pipeline output to a DPP."""

    output: PipelineOutput
    issuer: Organization
    manufacturer: Organization | None = None
    product_name: str | None = None
    credential_base_uri: str = "https://credentials.example.com"
    traceability_event_uris: list[str] = []


class ProjectOutputResponse(BaseModel):
    """Response containing the projected DPP."""

    passport: DigitalProductPassport
    output_id: str


@use_case
class ProjectOutputUseCase:
    """Project a PipelineOutput to a Digital Product Passport.

    Creates a DPP representing the output artifact, with links to
    the traceability events that document its provenance.
    """

    def __init__(self) -> None:
        pass  # No dependencies needed for projection

    async def execute(self, request: ProjectOutputRequest) -> ProjectOutputResponse:
        """Project a pipeline output to a DPP.

        Args:
            request: Contains the PipelineOutput and metadata

        Returns:
            Response with the projected DPP
        """
        output = request.output
        credential_id = f"{request.credential_base_uri}/dpp/{uuid4()}"

        # Build traceability event links
        traceability_events = [
            SecureLink(target=uri, link_type="traceability-event")
            for uri in request.traceability_event_uris
        ]

        # Create the DPP subject
        subject = DPPSubject(
            id=Identifier(scheme="output", value=output.output_id),
            name=request.product_name or output.name,
            manufacturer=request.manufacturer or request.issuer,
            traceability_events=traceability_events,
        )

        # Create the DPP
        passport = DigitalProductPassport(
            id=credential_id,
            credential_type=["VerifiableCredential", "DigitalProductPassport"],
            issuer=request.issuer,
            valid_from=output.created_at,
            credential_subject=subject,
        )

        return ProjectOutputResponse(
            passport=passport,
            output_id=output.output_id,
        )
