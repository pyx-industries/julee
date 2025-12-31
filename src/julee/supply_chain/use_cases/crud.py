"""Supply Chain CRUD use cases.

Generated use cases for Accelerator entity following the generic CRUD pattern.
"""

from julee.core.use_cases import generic_crud
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.repositories.accelerator import AcceleratorRepository

# Generate Accelerator CRUD - injects into module namespace
generic_crud.generate(Accelerator, AcceleratorRepository)

# Re-export for explicit imports (classes are now in module namespace)
__all__ = [
    "CreateAcceleratorRequest",
    "CreateAcceleratorResponse",
    "CreateAcceleratorUseCase",
    "GetAcceleratorRequest",
    "GetAcceleratorResponse",
    "GetAcceleratorUseCase",
    "ListAcceleratorsRequest",
    "ListAcceleratorsResponse",
    "ListAcceleratorsUseCase",
    "UpdateAcceleratorRequest",
    "UpdateAcceleratorResponse",
    "UpdateAcceleratorUseCase",
    "DeleteAcceleratorRequest",
    "DeleteAcceleratorResponse",
    "DeleteAcceleratorUseCase",
]
