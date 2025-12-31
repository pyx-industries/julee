"""Supply Chain CRUD use cases.

Generated use cases for Accelerator entity following the generic CRUD pattern.

Import the generated classes directly::

    from julee.supply_chain.use_cases.crud import CreateAcceleratorUseCase
"""

from julee.core.use_cases import generic_crud
from julee.supply_chain.entities.accelerator import Accelerator
from julee.supply_chain.repositories.accelerator import AcceleratorRepository

# Generate Accelerator CRUD - injects into module namespace
generic_crud.generate(Accelerator, AcceleratorRepository, filters=["status"])
