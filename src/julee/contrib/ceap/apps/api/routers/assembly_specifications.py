"""Assembly Specifications API router.

Routes for assembly specification CRUD operations.
Imports Request/Response from use_cases (canonical location).
"""

import logging
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi_pagination import Page, paginate

from julee.contrib.ceap.apps.api.dependencies import (
    get_assembly_specification_repository,
)
from julee.contrib.ceap.entities import AssemblySpecification
from julee.contrib.ceap.repositories.assembly_specification import (
    AssemblySpecificationRepository,
)
from julee.contrib.ceap.use_cases.crud import (
    CreateAssemblySpecificationRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=Page[AssemblySpecification])
async def list_assembly_specifications(
    repository: AssemblySpecificationRepository = Depends(
        get_assembly_specification_repository
    ),
) -> Page[AssemblySpecification]:
    """Get paginated list of assembly specifications."""
    specifications = await repository.list_all()
    return cast(Page[AssemblySpecification], paginate(specifications))


@router.get("/{assembly_specification_id}", response_model=AssemblySpecification)
async def get_assembly_specification(
    assembly_specification_id: str = Path(
        description="The ID of the assembly specification to retrieve"
    ),
    repository: AssemblySpecificationRepository = Depends(
        get_assembly_specification_repository
    ),
) -> AssemblySpecification:
    """Get a specific assembly specification by ID."""
    specification = await repository.get(assembly_specification_id)
    if specification is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assembly specification '{assembly_specification_id}' not found.",
        )
    return specification


@router.post("/", response_model=AssemblySpecification)
async def create_assembly_specification(
    request: CreateAssemblySpecificationRequest,
    repository: AssemblySpecificationRepository = Depends(
        get_assembly_specification_repository
    ),
) -> AssemblySpecification:
    """Create a new assembly specification."""
    from julee.contrib.ceap.use_cases.crud import CreateAssemblySpecificationUseCase

    use_case = CreateAssemblySpecificationUseCase(repository)
    response = await use_case.execute(request)
    return response.entity
