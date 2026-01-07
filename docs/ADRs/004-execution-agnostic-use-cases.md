# ADR 004: Execution-Agnostic Use Cases

## Status

Draft

## Date

2025-12-28

## Context

Use cases in the CEAP bounded context have Temporal-specific coupling:

1. **Time handling**: `now_fn: Callable[[], datetime]` parameters with names like "now_fn" that reveal awareness of execution context
2. **Execution identity**: `workflow_id: str` in requests and entities - a Temporal-specific concept leaked into the domain

Examples:

```python
# In extract_assemble_data.py
class ExtractAssembleDataRequest(BaseModel):
    workflow_id: str  # Temporal concept in domain

class ExtractAssembleDataUseCase:
    def __init__(
        self,
        ...,
        now_fn: Callable[[], datetime] = None,  # Temporal-aware naming
    ):
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
```

```python
# In assembly.py entity
class Assembly(BaseModel):
    workflow_id: str  # Temporal concept in domain entity
```

This coupling is problematic because:

1. **Testing complexity**: Tests need to provide mock functions for time
2. **Framework lock-in**: Domain code reveals awareness of Temporal concepts
3. **Reusability**: Use cases can't be easily used in Prefect, Dagster, or simple async contexts
4. **Mixed concerns**: Execution traceability (workflow_id) is conflated with domain identity

The goal is for use cases to be completely agnostic about their execution context. A use case should work identically whether running:
- Directly in tests or CLI
- In Temporal workflows
- In Prefect/Dagster pipelines
- Via message queues

## Decision

Use cases SHALL receive time and execution identity through **service protocols** injected at construction time, following the established pattern where DI containers inject only repositories and services.

### ClockService Protocol

A `ClockService` provides time abstraction:

```python
class ClockService(Protocol):
    """Service protocol for obtaining current time.

    Use cases inject ClockService to avoid direct datetime.now() calls,
    enabling deterministic testing and execution-context-agnostic code.
    """

    def now(self) -> datetime:
        """Return current time as timezone-aware datetime (UTC)."""
        ...
```

Standard implementation for non-workflow contexts:

```python
class SystemClockService:
    """ClockService implementation using system time."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

Temporal implementation (in infrastructure layer):

```python
class TemporalClockService:
    """ClockService implementation for Temporal workflows.

    Wraps temporal.workflow.now() for deterministic replay.
    """

    def now(self) -> datetime:
        from temporalio import workflow
        return workflow.now()
```

### ExecutionService Protocol

An `ExecutionService` provides execution identity:

```python
class ExecutionService(Protocol):
    """Service protocol for execution-level context.

    Provides traceability information without coupling to specific
    execution frameworks like Temporal.
    """

    def get_execution_id(self) -> str:
        """Return unique identifier for this execution.

        In Temporal: workflow_id
        In Prefect: flow_run_id
        In tests: deterministic UUID
        In simple async: generated UUID
        """
        ...
```

Standard implementation:

```python
class DefaultExecutionService:
    """Default execution service generating UUIDs."""

    def __init__(self, execution_id: str | None = None):
        self._execution_id = execution_id or str(uuid.uuid4())

    def get_execution_id(self) -> str:
        return self._execution_id
```

Temporal implementation:

```python
class TemporalExecutionService:
    """Execution service for Temporal workflows."""

    def get_execution_id(self) -> str:
        from temporalio import workflow
        return workflow.info().workflow_id
```

### Use Case Pattern

Use cases receive these services like any other service dependency:

```python
class ExtractAssembleDataUseCase:
    def __init__(
        self,
        assembly_repo: AssemblyRepository,
        knowledge_service: KnowledgeService,
        clock_service: ClockService,
        execution_service: ExecutionService,
    ):
        self._assembly_repo = assembly_repo
        self._knowledge_service = knowledge_service
        self._clock_service = clock_service
        self._execution_service = execution_service

    async def execute(self, request: ExtractAssembleDataRequest) -> ExtractAssembleDataResponse:
        assembly = Assembly(
            execution_id=self._execution_service.get_execution_id(),
            created_at=self._clock_service.now(),
            ...
        )
```

The request contains only business parameters:

```python
class ExtractAssembleDataRequest(BaseModel):
    document_id: str
    spec_id: str
    # No execution_id - comes from ExecutionService
```

### Service Scope: Use Cases Only

ClockService is injected into **use cases only**. Other service implementations (repositories, external service adapters) MAY use `datetime.now()` for operational timestamps.

The distinction:
- **Domain state timestamps** (entity `created_at`, `updated_at`) → Use case controls via ClockService
- **Operational timestamps** (when did external API call happen?) → Implementation detail

This keeps the abstraction where it matters (domain state) without over-engineering infrastructure code.

### Entity Naming: workflow_id → execution_id

Domain entities use the generic term `execution_id` instead of Temporal-specific `workflow_id`:

```python
# Before
class Assembly(BaseModel):
    workflow_id: str

# After
class Assembly(BaseModel):
    execution_id: str
```

This is a hard rename (no backward compatibility shim) because:
- The field is internal to the CEAP BC
- No external contracts depend on it
- Clean break is better than accumulating debt

## Consequences

### Positive

1. **Framework agnosticism**: Use cases work unchanged across Temporal, Prefect, Dagster, or direct execution
2. **Deterministic testing**: Inject FixedClockService and FixedExecutionService for reproducible tests
3. **Clear boundaries**: Execution context is infrastructure, not domain
4. **Consistent DI pattern**: Repositories and services only - no new categories
5. **Future-proof**: Adding new execution frameworks requires only new service implementations

### Negative

1. **More service dependencies**: Use cases using time/execution need these services injected
2. **Migration effort**: Existing CEAP code needs refactoring

### Neutral

1. **Not all use cases need these**: Only inject where actually used

## Implementation

### Phase 1: Core Service Protocols

Create in `julee/core/services/`:
- `clock.py` - ClockService protocol + SystemClockService
- `execution.py` - ExecutionService protocol + DefaultExecutionService

### Phase 2: Temporal Adapters

Create in `julee/core/infrastructure/temporal/`:
- `clock.py` - TemporalClockService
- `execution.py` - TemporalExecutionService

### Phase 3: CEAP Migration

Update:
- `julee/contrib/ceap/entities/assembly.py` - workflow_id → execution_id
- `julee/contrib/ceap/use_cases/extract_assemble_data.py` - ClockService, ExecutionService
- `julee/contrib/ceap/use_cases/validate_document.py` - ClockService
- All related tests

### Phase 4: Test Utilities

Create:
- `FixedClockService` - Returns predetermined time
- `FixedExecutionService` - Returns predetermined ID

## Alternatives Considered

### 1. Keep now_fn Callable Pattern

Continue using `now_fn: Callable[[], datetime]`.

**Rejected**: The naming reveals awareness of "why" time needs injection (workflow replay). Service-based abstraction is cleaner and doesn't leak implementation concerns.

### 2. execution_id in Request

Pass execution_id through the request object.

**Rejected**: Execution identity is infrastructure context, not business data. Requests should contain only business parameters.

### 3. New Protocol Category (Clock, ExecutionContext)

Create non-service protocols for these concerns.

**Rejected**: Breaks the established pattern where DI containers inject only repositories and services. These ARE services - they provide a capability to the use case.

### 4. Soft Migration with Backward Compatibility

Keep workflow_id alongside execution_id.

**Rejected**: Creates confusion and technical debt. Clean break is appropriate for internal field in single BC.

## References

- [ADR 003: Workflow Orchestration via Handler Services](./003-workflow-orchestration-handlers.md)
- Temporal SDK documentation on workflow.now() for deterministic replay
- Clean Architecture principles on infrastructure abstraction
