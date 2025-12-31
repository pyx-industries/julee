"""Generic CRUD use cases for UNTP credentials.

Credentials are projected from core entities (OperationRecord, PipelineOutput),
not manually created. Therefore only Get and List operations are available.

Create, Update, Delete are handled by:
- ProjectExecutionUseCase (creates DTEs from operations)
- ProjectOutputUseCase (creates DPPs from outputs)
- EmitCredentialUseCase (signs and stores credentials)
"""

from julee.contrib.untp.entities.credential import (
    DigitalConformityCredential,
    DigitalProductPassport,
    DigitalTraceabilityEvent,
)
from julee.contrib.untp.repositories.credential import (
    ConformityCredentialRepository,
    ProductPassportRepository,
    TraceabilityEventRepository,
)
from julee.core.use_cases import generic_crud

# Generate Get/List only for DTE
generic_crud.generate(
    DigitalTraceabilityEvent,
    TraceabilityEventRepository,
    id_field="id",
    create=False,
    update=False,
    delete=False,
)

# Generate Get/List only for DPP
generic_crud.generate(
    DigitalProductPassport,
    ProductPassportRepository,
    id_field="id",
    create=False,
    update=False,
    delete=False,
)

# Generate Get/List only for DCC
generic_crud.generate(
    DigitalConformityCredential,
    ConformityCredentialRepository,
    id_field="id",
    create=False,
    update=False,
    delete=False,
)

# Exported classes (generated above):
# - GetDigitalTraceabilityEventUseCase
# - GetDigitalTraceabilityEventRequest
# - GetDigitalTraceabilityEventResponse
# - ListDigitalTraceabilityEventsUseCase
# - ListDigitalTraceabilityEventsRequest
# - ListDigitalTraceabilityEventsResponse
#
# - GetDigitalProductPassportUseCase
# - GetDigitalProductPassportRequest
# - GetDigitalProductPassportResponse
# - ListDigitalProductPassportsUseCase
# - ListDigitalProductPassportsRequest
# - ListDigitalProductPassportsResponse
#
# - GetDigitalConformityCredentialUseCase
# - GetDigitalConformityCredentialRequest
# - GetDigitalConformityCredentialResponse
# - ListDigitalConformityCredentialsUseCase
# - ListDigitalConformityCredentialsRequest
# - ListDigitalConformityCredentialsResponse
