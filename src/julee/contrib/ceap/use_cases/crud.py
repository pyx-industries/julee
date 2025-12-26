"""CRUD use cases for CEAP entities.

Request/Response classes for CEAP CRUD operations. These are the canonical
definitions used by both the domain layer and API layer.

Validation logic is delegated to entity validators. ID generation is handled
by repository's generate_id() method.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from julee.contrib.ceap.entities.assembly_specification import (
    AssemblySpecification,
    AssemblySpecificationStatus,
)
from julee.contrib.ceap.entities.knowledge_service_config import (
    KnowledgeServiceConfig,
)
from julee.contrib.ceap.entities.knowledge_service_query import (
    KnowledgeServiceQuery,
)
from julee.contrib.ceap.repositories.assembly_specification import (
    AssemblySpecificationRepository,
)
from julee.contrib.ceap.repositories.knowledge_service_config import (
    KnowledgeServiceConfigRepository,
)
from julee.contrib.ceap.repositories.knowledge_service_query import (
    KnowledgeServiceQueryRepository,
)

# =============================================================================
# AssemblySpecification
# =============================================================================


class CreateAssemblySpecificationRequest(BaseModel):
    """Request for creating an assembly specification.

    Validation delegated to AssemblySpecification entity validators.
    ID generated server-side by repository.
    """

    name: str = Field(
        description=AssemblySpecification.model_fields["name"].description
    )
    applicability: str = Field(
        description=AssemblySpecification.model_fields["applicability"].description
    )
    jsonschema: dict[str, Any] = Field(
        description=AssemblySpecification.model_fields["jsonschema"].description
    )
    knowledge_service_queries: dict[str, str] = Field(
        default_factory=dict,
        description=AssemblySpecification.model_fields[
            "knowledge_service_queries"
        ].description,
    )
    version: str = Field(
        default=AssemblySpecification.model_fields["version"].default,
        description=AssemblySpecification.model_fields["version"].description,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Delegate to entity validator."""
        return AssemblySpecification.name_must_not_be_empty(v)

    @field_validator("applicability")
    @classmethod
    def validate_applicability(cls, v: str) -> str:
        """Delegate to entity validator."""
        return AssemblySpecification.applicability_must_not_be_empty(v)

    @field_validator("jsonschema")
    @classmethod
    def validate_jsonschema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Delegate to entity validator."""
        return AssemblySpecification.jsonschema_must_be_valid(v)

    @field_validator("knowledge_service_queries")
    @classmethod
    def validate_knowledge_service_queries(
        cls, v: dict[str, str], info: ValidationInfo
    ) -> dict[str, str]:
        """Delegate to entity validator."""
        return AssemblySpecification.knowledge_service_queries_must_be_valid(v, info)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Delegate to entity validator."""
        return AssemblySpecification.version_must_not_be_empty(v)


class CreateAssemblySpecificationResponse(BaseModel):
    """Response from creating an assembly specification."""

    entity: AssemblySpecification


class CreateAssemblySpecificationUseCase:
    """Create an assembly specification."""

    def __init__(self, repo: AssemblySpecificationRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateAssemblySpecificationRequest
    ) -> CreateAssemblySpecificationResponse:
        """Create and save a new assembly specification."""
        entity_id = await self.repo.generate_id()
        now = datetime.now(timezone.utc)

        entity = AssemblySpecification(
            assembly_specification_id=entity_id,
            name=request.name,
            applicability=request.applicability,
            jsonschema=request.jsonschema,
            knowledge_service_queries=request.knowledge_service_queries,
            version=request.version,
            status=AssemblySpecificationStatus.DRAFT,
            created_at=now,
            updated_at=now,
        )

        await self.repo.save(entity)
        return CreateAssemblySpecificationResponse(entity=entity)


class GetAssemblySpecificationRequest(BaseModel):
    """Request to get an assembly specification by ID."""

    assembly_specification_id: str


class GetAssemblySpecificationResponse(BaseModel):
    """Response from getting an assembly specification."""

    entity: AssemblySpecification | None = None


class GetAssemblySpecificationUseCase:
    """Get an assembly specification by ID."""

    def __init__(self, repo: AssemblySpecificationRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: GetAssemblySpecificationRequest
    ) -> GetAssemblySpecificationResponse:
        """Retrieve assembly specification by ID."""
        entity = await self.repo.get(request.assembly_specification_id)
        return GetAssemblySpecificationResponse(entity=entity)


class ListAssemblySpecificationsRequest(BaseModel):
    """Request to list all assembly specifications."""

    pass


class ListAssemblySpecificationsResponse(BaseModel):
    """Response from listing assembly specifications."""

    entities: list[AssemblySpecification] = []


class ListAssemblySpecificationsUseCase:
    """List all assembly specifications."""

    def __init__(self, repo: AssemblySpecificationRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: ListAssemblySpecificationsRequest
    ) -> ListAssemblySpecificationsResponse:
        """List all assembly specifications."""
        entities = await self.repo.list_all()
        return ListAssemblySpecificationsResponse(entities=entities)


# =============================================================================
# KnowledgeServiceQuery
# =============================================================================


class CreateKnowledgeServiceQueryRequest(BaseModel):
    """Request for creating a knowledge service query.

    Validation delegated to KnowledgeServiceQuery entity validators.
    ID generated server-side by repository.
    """

    name: str = Field(
        description=KnowledgeServiceQuery.model_fields["name"].description
    )
    knowledge_service_id: str = Field(
        description=KnowledgeServiceQuery.model_fields[
            "knowledge_service_id"
        ].description
    )
    prompt: str = Field(
        description=KnowledgeServiceQuery.model_fields["prompt"].description
    )
    query_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=KnowledgeServiceQuery.model_fields["query_metadata"].description,
    )
    assistant_prompt: str | None = Field(
        default=KnowledgeServiceQuery.model_fields["assistant_prompt"].default,
        description=KnowledgeServiceQuery.model_fields["assistant_prompt"].description,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Delegate to entity validator."""
        return KnowledgeServiceQuery.name_must_not_be_empty(v)

    @field_validator("knowledge_service_id")
    @classmethod
    def validate_knowledge_service_id(cls, v: str) -> str:
        """Delegate to entity validator."""
        return KnowledgeServiceQuery.knowledge_service_id_must_not_be_empty(v)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Delegate to entity validator."""
        return KnowledgeServiceQuery.prompt_must_not_be_empty(v)


class CreateKnowledgeServiceQueryResponse(BaseModel):
    """Response from creating a knowledge service query."""

    entity: KnowledgeServiceQuery


class CreateKnowledgeServiceQueryUseCase:
    """Create a knowledge service query."""

    def __init__(self, repo: KnowledgeServiceQueryRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: CreateKnowledgeServiceQueryRequest
    ) -> CreateKnowledgeServiceQueryResponse:
        """Create and save a new knowledge service query."""
        query_id = await self.repo.generate_id()
        now = datetime.now(timezone.utc)

        entity = KnowledgeServiceQuery(
            query_id=query_id,
            name=request.name,
            knowledge_service_id=request.knowledge_service_id,
            prompt=request.prompt,
            query_metadata=request.query_metadata,
            assistant_prompt=request.assistant_prompt,
            created_at=now,
            updated_at=now,
        )

        await self.repo.save(entity)
        return CreateKnowledgeServiceQueryResponse(entity=entity)


class GetKnowledgeServiceQueryRequest(BaseModel):
    """Request to get a knowledge service query by ID."""

    query_id: str


class GetKnowledgeServiceQueryResponse(BaseModel):
    """Response from getting a knowledge service query."""

    entity: KnowledgeServiceQuery | None = None


class GetKnowledgeServiceQueryUseCase:
    """Get a knowledge service query by ID."""

    def __init__(self, repo: KnowledgeServiceQueryRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: GetKnowledgeServiceQueryRequest
    ) -> GetKnowledgeServiceQueryResponse:
        """Retrieve knowledge service query by ID."""
        entity = await self.repo.get(request.query_id)
        return GetKnowledgeServiceQueryResponse(entity=entity)


class ListKnowledgeServiceQueriesRequest(BaseModel):
    """Request to list all knowledge service queries."""

    pass


class ListKnowledgeServiceQueriesResponse(BaseModel):
    """Response from listing knowledge service queries."""

    entities: list[KnowledgeServiceQuery] = []


class ListKnowledgeServiceQueriesUseCase:
    """List all knowledge service queries."""

    def __init__(self, repo: KnowledgeServiceQueryRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: ListKnowledgeServiceQueriesRequest
    ) -> ListKnowledgeServiceQueriesResponse:
        """List all knowledge service queries."""
        entities = await self.repo.list_all()
        return ListKnowledgeServiceQueriesResponse(entities=entities)


# =============================================================================
# KnowledgeServiceConfig
# =============================================================================


class GetKnowledgeServiceConfigRequest(BaseModel):
    """Request to get a knowledge service config by ID."""

    config_id: str


class GetKnowledgeServiceConfigResponse(BaseModel):
    """Response from getting a knowledge service config."""

    entity: KnowledgeServiceConfig | None = None


class GetKnowledgeServiceConfigUseCase:
    """Get a knowledge service config by ID."""

    def __init__(self, repo: KnowledgeServiceConfigRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: GetKnowledgeServiceConfigRequest
    ) -> GetKnowledgeServiceConfigResponse:
        """Retrieve knowledge service config by ID."""
        entity = await self.repo.get(request.config_id)
        return GetKnowledgeServiceConfigResponse(entity=entity)


class ListKnowledgeServiceConfigsRequest(BaseModel):
    """Request to list all knowledge service configs."""

    pass


class ListKnowledgeServiceConfigsResponse(BaseModel):
    """Response from listing knowledge service configs."""

    entities: list[KnowledgeServiceConfig] = []


class ListKnowledgeServiceConfigsUseCase:
    """List all knowledge service configs."""

    def __init__(self, repo: KnowledgeServiceConfigRepository) -> None:
        self.repo = repo

    async def execute(
        self, request: ListKnowledgeServiceConfigsRequest
    ) -> ListKnowledgeServiceConfigsResponse:
        """List all knowledge service configs."""
        entities = await self.repo.list_all()
        return ListKnowledgeServiceConfigsResponse(entities=entities)
