# Use Case DTO Patterns in Julee Architecture

A research report on doctrine and practice for Data Transfer Objects (DTOs) in use case request/response handling across the julee and rba codebases.

---

## Executive Summary

Clean Architecture prescribes that use cases should operate through Request and Response DTOs that form a boundary between the application layer and external concerns. This report examines the doctrine behind this pattern and catalogues the different approaches taken across the julee ecosystem:

1. **MCP Services (sphinx_hcd, sphinx_c4)**: Full DTO implementation with dedicated Request/Response classes
2. **Core Julee Domain**: Primitive parameters with direct domain model returns
3. **RBA Codebase**: Parameterless execution with void returns

The MCP services represent the canonical implementation of clean architecture DTO patterns, while other parts of the codebase use simplified patterns appropriate to their contexts.

---

## 1. Clean Architecture DTO Doctrine

### 1.1 Core Principles

In Clean Architecture, Request and Response models form the **boundary layer** between use cases and the outside world. They serve as "layers of abstraction that separate your business logic from the outside world."

**Key doctrine points:**

| Principle | Description |
|-----------|-------------|
| **Unique DTOs Per Use Case** | Each use case should have its own Request/Response pair. "Duplication is not a problem. Eventual similarities are only illusions as use cases will grow in different directions." |
| **DTO In, DTO Out** | Controllers work with DTOs; entities stay hidden from external layers |
| **Domain Models Stay Internal** | "At no point is a domain entity exposed" directly to external layers |
| **Request Models Carry Intent** | Request objects "signal user intent" (e.g., `CreateUserCommand`) |
| **Response Models Shape Output** | Prefer whitelisting properties over blacklisting to prevent data leakage |

### 1.2 The Request Handler Pattern

Use cases implement a request handler interface:

```python
class UseCase:
    async def execute(self, request: RequestModel) -> ResponseModel:
        # All application-specific logic goes here
        ...
```

This pattern:
- Takes a request object as its lone parameter
- Returns a response message
- Contains all application-specific logic
- Works in a loosely coupled fashion via the mediator pattern

### 1.3 Conversion Responsibilities

| Layer | Responsibility |
|-------|---------------|
| Controller/Adapter | Convert external input → Request DTO |
| Use Case | Convert Request DTO → Domain Model operations |
| Use Case | Convert Domain Model results → Response DTO |
| Presenter/Adapter | Convert Response DTO → external output format |

---

## 2. MCP Services DTO Catalogue

The sphinx_hcd and sphinx_c4 modules implement the full DTO pattern. DTOs are defined in centralized `requests.py` and `responses.py` files within the `*_api` packages.

### 2.1 HCD API Request DTOs

Location: `src/julee/docs/hcd_api/requests.py`

#### Story DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateStoryRequest` | Create new story | `feature_title`, `persona`, `app_slug`, `i_want`, `so_that` |
| `GetStoryRequest` | Retrieve by slug | `slug` |
| `ListStoriesRequest` | List all stories | (empty - extensible for filtering) |
| `UpdateStoryRequest` | Partial update | `slug` + optional fields |
| `DeleteStoryRequest` | Delete by slug | `slug` |

#### Epic DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateEpicRequest` | Create new epic | `slug`, `description`, `story_refs` |
| `GetEpicRequest` | Retrieve by slug | `slug` |
| `ListEpicsRequest` | List all epics | (empty) |
| `UpdateEpicRequest` | Partial update | `slug`, optional `description`, `story_refs` |
| `DeleteEpicRequest` | Delete by slug | `slug` |

#### Journey DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateJourneyRequest` | Create journey | `slug`, `persona`, `intent`, `outcome`, `goal`, `depends_on`, `steps` |
| `GetJourneyRequest` | Retrieve by slug | `slug` |
| `ListJourneysRequest` | List all | (empty) |
| `UpdateJourneyRequest` | Partial update | `slug` + optional fields |
| `DeleteJourneyRequest` | Delete by slug | `slug` |
| `JourneyStepInput` | Nested step data | `step_type`, `ref`, `description` |

#### Accelerator DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateAcceleratorRequest` | Create accelerator | `slug`, `status`, `milestone`, `acceptance`, `objective`, `sources_from`, `feeds_into`, `publishes_to`, `depends_on` |
| `GetAcceleratorRequest` | Retrieve by slug | `slug` |
| `ListAcceleratorsRequest` | List all | (empty) |
| `UpdateAcceleratorRequest` | Partial update | `slug` + optional fields |
| `DeleteAcceleratorRequest` | Delete by slug | `slug` |
| `IntegrationReferenceInput` | Nested reference | `slug`, `description` |

#### Integration DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateIntegrationRequest` | Create integration | `slug`, `module`, `name`, `description`, `direction`, `depends_on` |
| `GetIntegrationRequest` | Retrieve by slug | `slug` |
| `ListIntegrationsRequest` | List all | (empty) |
| `UpdateIntegrationRequest` | Partial update | `slug` + optional fields |
| `DeleteIntegrationRequest` | Delete by slug | `slug` |
| `ExternalDependencyInput` | Nested dependency | `name`, `url`, `description` |

#### App DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateAppRequest` | Create app | `slug`, `name`, `app_type`, `status`, `description`, `accelerators` |
| `GetAppRequest` | Retrieve by slug | `slug` |
| `ListAppsRequest` | List all | (empty) |
| `UpdateAppRequest` | Partial update | `slug` + optional fields |
| `DeleteAppRequest` | Delete by slug | `slug` |

#### Persona DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreatePersonaRequest` | Create persona | `slug`, `name`, `goals`, `frustrations`, `jobs_to_be_done`, `context` |
| `GetPersonaRequest` | Retrieve by name | `name` |
| `ListPersonasRequest` | List all | (empty) |
| `UpdatePersonaRequest` | Partial update | `slug` + optional fields |
| `DeletePersonaRequest` | Delete by slug | `slug` |
| `DerivePersonasRequest` | Derive from stories | (empty) |

### 2.2 HCD API Response DTOs

Location: `src/julee/docs/hcd_api/responses.py`

**Pattern**: Responses wrap domain models rather than duplicating structure.

| Response Type | Pattern | Fields |
|--------------|---------|--------|
| `Create*Response` | Wrap created entity | `{entity}: DomainModel` |
| `Get*Response` | Wrap optional entity | `{entity}: DomainModel | None` |
| `List*Response` | Wrap entity list | `{entities}: list[DomainModel]` |
| `Update*Response` | Wrap with found flag | `{entity}: DomainModel | None`, `found: bool` |
| `Delete*Response` | Deletion status | `deleted: bool` |

### 2.3 C4 API Request DTOs

Location: `src/julee/docs/c4_api/requests.py`

#### Software System DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateSoftwareSystemRequest` | Create system | `slug`, `name`, `description`, `system_type`, `owner`, `technology`, `url`, `tags` |
| `GetSoftwareSystemRequest` | Retrieve by slug | `slug` |
| `ListSoftwareSystemsRequest` | List all | (empty) |
| `UpdateSoftwareSystemRequest` | Partial update | `slug` + optional fields |
| `DeleteSoftwareSystemRequest` | Delete by slug | `slug` |

#### Container DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateContainerRequest` | Create container | `slug`, `name`, `system_slug`, `description`, `container_type`, `technology`, `url`, `tags` |
| `GetContainerRequest` | Retrieve by slug | `slug` |
| `ListContainersRequest` | List all | (empty) |
| `UpdateContainerRequest` | Partial update | `slug` + optional fields |
| `DeleteContainerRequest` | Delete by slug | `slug` |

#### Component DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateComponentRequest` | Create component | `slug`, `name`, `container_slug`, `system_slug`, `description`, `technology`, `interface`, `code_path`, `url`, `tags` |
| `GetComponentRequest` | Retrieve by slug | `slug` |
| `ListComponentsRequest` | List all | (empty) |
| `UpdateComponentRequest` | Partial update | `slug` + optional fields |
| `DeleteComponentRequest` | Delete by slug | `slug` |

#### Relationship DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateRelationshipRequest` | Create relationship | `slug`, `source_type`, `source_slug`, `destination_type`, `destination_slug`, `description`, `technology`, `bidirectional`, `tags` |
| `GetRelationshipRequest` | Retrieve by slug | `slug` |
| `ListRelationshipsRequest` | List all | (empty) |
| `UpdateRelationshipRequest` | Partial update | `slug` + optional fields |
| `DeleteRelationshipRequest` | Delete by slug | `slug` |

#### Deployment Node DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateDeploymentNodeRequest` | Create node | `slug`, `name`, `environment`, `node_type`, `technology`, `description`, `parent_slug`, `container_instances`, `properties`, `tags` |
| `GetDeploymentNodeRequest` | Retrieve by slug | `slug` |
| `ListDeploymentNodesRequest` | List all | (empty) |
| `UpdateDeploymentNodeRequest` | Partial update | `slug` + optional fields |
| `DeleteDeploymentNodeRequest` | Delete by slug | `slug` |
| `ContainerInstanceInput` | Nested instance | `container_slug`, `instance_id`, `properties` |

#### Dynamic Step DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `CreateDynamicStepRequest` | Create step | `slug`, `sequence_name`, `step_number`, `source_type`, `source_slug`, `destination_type`, `destination_slug`, `description`, `technology`, `return_description`, `is_return` |
| `GetDynamicStepRequest` | Retrieve by slug | `slug` |
| `ListDynamicStepsRequest` | List all | (empty) |
| `UpdateDynamicStepRequest` | Partial update | `slug` + optional fields |
| `DeleteDynamicStepRequest` | Delete by slug | `slug` |

#### Diagram Request DTOs
| DTO | Purpose | Key Fields |
|-----|---------|------------|
| `GetSystemContextDiagramRequest` | Generate context diagram | `system_slug`, `format` |
| `GetContainerDiagramRequest` | Generate container diagram | `system_slug`, `format` |
| `GetComponentDiagramRequest` | Generate component diagram | `container_slug`, `format` |
| `GetSystemLandscapeDiagramRequest` | Generate landscape diagram | `format` |
| `GetDeploymentDiagramRequest` | Generate deployment diagram | `environment`, `format` |
| `GetDynamicDiagramRequest` | Generate dynamic diagram | `sequence_name`, `format` |

### 2.4 C4 API Response DTOs

Location: `src/julee/docs/c4_api/responses.py`

Same pattern as HCD:
- `Create*Response`: Wraps created entity
- `Get*Response`: Wraps optional entity
- `List*Response`: Wraps entity list
- `Update*Response`: Wraps with found flag
- `Delete*Response`: Deletion status
- `DiagramResponse`: `content`, `format`, `title`

---

## 3. DTO Implementation Patterns

### 3.1 Request DTO Features

The MCP services implement several sophisticated patterns:

#### Validation Delegation

Requests delegate validation to domain models:

```python
class CreateStoryRequest(BaseModel):
    feature_title: str

    @field_validator("feature_title")
    @classmethod
    def validate_feature_title(cls, v: str) -> str:
        return Story.validate_feature_title(v)  # Domain validates
```

#### Domain Model Conversion

Create requests include `to_domain_model()` methods:

```python
def to_domain_model(self) -> Story:
    return Story.from_feature_file(
        feature_title=self.feature_title,
        persona=self.persona,
        ...
    )
```

#### Update Application

Update requests include `apply_to()` methods for partial updates:

```python
def apply_to(self, existing: Story) -> Story:
    updates = {k: v for k, v in {...}.items() if v is not None}
    return existing.model_copy(update=updates) if updates else existing
```

#### Nested Input Models

Complex requests use nested input models for sub-structures:

```python
class JourneyStepInput(BaseModel):
    step_type: str
    ref: str
    description: str = ""

    def to_domain_model(self) -> JourneyStep:
        return JourneyStep(...)
```

### 3.2 Response DTO Features

#### Domain Model Wrapping

Responses wrap domain models directly (known anti-pattern for strict clean architecture, but pragmatic):

```python
class CreateStoryResponse(BaseModel):
    story: Story  # Domain model exposed in response
```

#### Metadata Fields

Update responses include success metadata:

```python
class UpdateStoryResponse(BaseModel):
    story: Story | None
    found: bool = True  # Indicates if entity existed
```

---

## 4. Alternative Patterns in Julee Core

### 4.1 Core Domain Use Cases

Location: `src/julee/domain/use_cases/`

The core julee domain uses a **simplified pattern** without explicit Request/Response DTOs:

```python
class ValidateDocumentUseCase:
    async def validate_document(
        self,
        document_id: str,  # Primitive parameter
        policy_id: str     # Primitive parameter
    ) -> DocumentPolicyValidation:  # Domain model return
```

**Characteristics:**
- Method parameters are primitives (strings, ints)
- Returns domain models directly
- No dedicated Request/Response classes
- Multiple repository dependencies injected via constructor

**When this pattern is appropriate:**
- Internal use cases not exposed to external APIs
- Workflow orchestration where inputs come from trusted sources
- Complex operations with many collaborating repositories

### 4.2 Comparison: MCP vs Core

| Aspect | MCP Services | Core Domain |
|--------|-------------|-------------|
| Input | Request DTO | Primitive parameters |
| Output | Response DTO wrapping domain | Domain model directly |
| Validation | In Request DTO | In use case method |
| Conversion | `to_domain_model()` | Direct instantiation |
| Update pattern | `apply_to()` method | Repository merge |

---

## 5. RBA Codebase Patterns

### 5.1 Initialize System Data Pattern

Location: `rba/src/credential/domain/use_cases/initialize_system_data.py`

RBA uses an even simpler pattern for initialization use cases:

```python
class InitializeSystemDataUseCase:
    async def execute(self) -> None:  # No parameters, void return
```

**Characteristics:**
- No input parameters
- Void return type
- Side-effect focused (creates data in repositories)
- Configuration loaded from external YAML files

### 5.2 Pattern Applicability

This pattern suits:
- System initialization scripts
- Background jobs/workers
- Operations with no user input
- Idempotent setup routines

---

## 6. Best Practices Synthesis

### 6.1 When to Use Full DTO Pattern

Use the MCP-style full DTO pattern when:
- Exposing use cases via APIs (REST, MCP, GraphQL)
- External clients need stable contracts
- Validation must happen at boundary
- Multiple adapters may invoke the same use case
- You need to version API contracts independently

### 6.2 When Simplified Patterns Suffice

Use primitive parameters when:
- Use case is internal to the application
- Called only from trusted code (workflows, other use cases)
- Input comes from already-validated sources
- Simplicity outweighs formality

### 6.3 Response Design Choices

**Wrapping domain models** (current practice):
- Simpler to implement
- Risks exposing internal structure
- Changes to domain affect API

**Dedicated response DTOs** (stricter):
- Better decoupling
- More boilerplate
- API changes don't require domain changes

### 6.4 Recommended Patterns by Context

| Context | Request Pattern | Response Pattern |
|---------|----------------|------------------|
| MCP/REST API | Full DTO with validation | DTO wrapping domain or dedicated |
| Internal Use Case | Primitives or domain models | Domain model |
| Workflow Step | Primitives | Domain model |
| Initialization | None | None/void |

---

## 7. DTO Count Summary

### HCD API (35 DTOs)
- **Requests**: 29 (Create/Get/List/Update/Delete × 6 entities + specialized + nested inputs)
- **Responses**: 6 patterns × 6 entities

### C4 API (41 DTOs)
- **Requests**: 35 (CRUD × 6 entities + 6 diagram requests + nested inputs)
- **Responses**: 6 patterns × 6 entities + DiagramResponse

### Core Julee
- **Requests**: 0 explicit DTOs
- **Responses**: 0 explicit DTOs (returns domain models)

### RBA
- **Requests**: 0 explicit DTOs
- **Responses**: 0 explicit DTOs

---

## References

### Clean Architecture Sources

1. [Implementing Clean Architecture - Of Controllers and Presenters](http://www.plainionist.net/Implementing-Clean-Architecture-Controller-Presenter/) - Request model flow through presenter pattern

2. [The Clean Architecture: An Introduction](https://rodschmidt.com/posts/the-clean-architecture-an-introduction/) - Request and response models as input/output of use cases

3. [Nuances in Clean Architecture](https://lukemorton.tech/articles/nuances-in-clean-architecture) - Use Case layer as boundary for domain model

4. [Domain-Driven Hexagon (GitHub)](https://github.com/Sairyss/domain-driven-hexagon) - DTOs, errors, and serializers kept with use cases

5. [The DTO Pattern (Baeldung)](https://www.baeldung.com/java-dto-pattern) - Core DTO pattern principles

6. [NewStore: Implementing Clean Architecture - Use Cases](https://www.newstore.com/articles/clean-architecture-code-hotspots/) - Request handler interface pattern

### Industry Practices

7. [SSW Rules for Clean Architecture](https://www.ssw.com.au/rules/rules-to-better-clean-architecture) - Unique DTOs per endpoint/use case

8. [Clean Architecture with DTOs (Medium)](https://medium.com/@matiesogeoffrey/clean-architecture-with-dtos-24f543f850fb) - DTO In, DTO Out pattern

9. [Clean Architecture: Where to Map DTO to Business Model](https://www.codestudy.net/blog/clean-architecture-where-does-mapping-of-dto-to-business-model-should-happen/) - Conversion responsibilities in use case layer

---

*Report compiled: December 2025*
