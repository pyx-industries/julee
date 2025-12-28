"""List doctrine rules use case.

Extracts and returns doctrine rules from test files. The tests ARE the
doctrine - this use case provides a structured view of those rules.
"""

from pydantic import BaseModel, Field

from julee.core.decorators import use_case
from julee.core.entities.doctrine import DoctrineArea, DoctrineRule
from julee.core.repositories.doctrine import DoctrineRepository


class ListDoctrineRulesRequest(BaseModel):
    """Request for listing doctrine rules."""

    area: str | None = Field(
        default=None,
        description="Optional area slug to filter by (e.g., 'bounded_context')",
    )


class ListDoctrineRulesResponse(BaseModel):
    """Response containing doctrine rules."""

    rules: list[DoctrineRule] = Field(default_factory=list)
    total_count: int = Field(description="Total number of rules returned")

    model_config = {"arbitrary_types_allowed": True}


@use_case
class ListDoctrineRulesUseCase:
    """List all doctrine rules, optionally filtered by area.

    This use case extracts rules from doctrine test files. The test
    docstrings ARE the rules - we just read and structure them.
    """

    def __init__(self, doctrine_repository: DoctrineRepository) -> None:
        """Initialize with doctrine repository.

        Args:
            doctrine_repository: Repository for extracting doctrine rules
        """
        self.doctrine_repo = doctrine_repository

    async def execute(
        self, request: ListDoctrineRulesRequest
    ) -> ListDoctrineRulesResponse:
        """Execute the use case.

        Args:
            request: Request with optional area filter

        Returns:
            Response containing matching doctrine rules
        """
        rules = await self.doctrine_repo.list_rules(area=request.area)
        return ListDoctrineRulesResponse(rules=rules, total_count=len(rules))


class ListDoctrineAreasRequest(BaseModel):
    """Request for listing doctrine areas."""

    pass


class ListDoctrineAreasResponse(BaseModel):
    """Response containing doctrine areas."""

    areas: list[DoctrineArea] = Field(default_factory=list)
    total_rules: int = Field(description="Total number of rules across all areas")


@use_case
class ListDoctrineAreasUseCase:
    """List all doctrine areas with their rules.

    Each area corresponds to an entity type in julee.core.entities.
    The entity docstring provides the definition; test docstrings
    provide the rules.
    """

    def __init__(self, doctrine_repository: DoctrineRepository) -> None:
        """Initialize with doctrine repository.

        Args:
            doctrine_repository: Repository for extracting doctrine
        """
        self.doctrine_repo = doctrine_repository

    async def execute(
        self, request: ListDoctrineAreasRequest | None = None
    ) -> ListDoctrineAreasResponse:
        """Execute the use case.

        Args:
            request: Request (currently no parameters)

        Returns:
            Response containing all doctrine areas
        """
        areas = await self.doctrine_repo.list_areas()
        total_rules = sum(area.rule_count for area in areas)
        return ListDoctrineAreasResponse(areas=areas, total_rules=total_rules)
