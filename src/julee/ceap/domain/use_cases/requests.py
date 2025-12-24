"""Request objects for CEAP use cases.

Request objects encapsulate the input parameters for use cases,
following Clean Architecture principles.
"""

from pydantic import BaseModel, Field


class ExtractAssembleDataRequest(BaseModel):
    """Request for extracting and assembling document data.

    Used by ExtractAssembleDataUseCase to assemble a document according
    to its specification.
    """

    document_id: str = Field(description="ID of the document to assemble")
    assembly_specification_id: str = Field(
        description="ID of the specification defining how to assemble"
    )
    workflow_id: str = Field(
        description="Temporal workflow ID that creates this assembly"
    )


class ValidateDocumentRequest(BaseModel):
    """Request for validating a document against a policy.

    Used by ValidateDocumentUseCase to validate document content
    against policy rules.
    """

    document_id: str = Field(description="ID of the document to validate")
    policy_id: str = Field(description="ID of the policy to validate against")


class InitializeSystemDataRequest(BaseModel):
    """Request for initializing system data.

    Used by InitializeSystemDataUseCase to bootstrap required
    system configurations. Currently has no parameters as the
    use case loads from fixtures.
    """

    pass
