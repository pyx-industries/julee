# Refactoring Plan: C4 Diagram Use Cases

## Goal

Bring C4 diagram use cases into compliance with Clean Architecture doctrine:
- Use cases accept Request objects
- Use cases return Response objects
- Diagram models live in `domain/models/`
- Proper separation of concerns

## Current State

```
src/julee/c4/domain/
├── models/
│   ├── component.py
│   ├── container.py
│   ├── deployment_node.py
│   ├── dynamic_step.py
│   ├── relationship.py
│   └── software_system.py
├── use_cases/
│   ├── requests.py          # Has GetComponentDiagramRequest etc (unused by use cases)
│   ├── responses.py         # Has DiagramResponse (for serialized output)
│   └── diagrams/
│       ├── component_diagram.py    # ComponentDiagramData + GetComponentDiagramUseCase
│       ├── container_diagram.py    # ContainerDiagramData + GetContainerDiagramUseCase
│       ├── deployment_diagram.py   # DeploymentDiagramData + GetDeploymentDiagramUseCase
│       ├── dynamic_diagram.py      # DynamicDiagramData + GetDynamicDiagramUseCase
│       ├── system_context.py       # PersonInfo + SystemContextDiagramData + GetSystemContextDiagramUseCase
│       └── system_landscape.py     # SystemLandscapeDiagramData + GetSystemLandscapeDiagramUseCase
└── serializers/
    ├── plantuml.py
    └── structurizr.py
```

### Problems

1. `*DiagramData` classes are co-located with use cases instead of in `domain/models/`
2. Use cases take primitive `slug: str` instead of Request objects
3. Use cases return `*DiagramData | None` instead of Response objects
4. `PersonInfo` is a mini-entity defined in use case file
5. Request objects in `requests.py` are orphaned (not used by use cases)

---

## Target State

```
src/julee/c4/domain/
├── models/
│   ├── component.py
│   ├── container.py
│   ├── deployment_node.py
│   ├── dynamic_step.py
│   ├── relationship.py
│   ├── software_system.py
│   ├── person.py                   # NEW: Person entity (if needed)
│   └── diagrams.py                 # NEW: All diagram domain models
├── use_cases/
│   ├── requests.py                 # Existing + verify diagram requests
│   ├── responses.py                # Add GetComponentDiagramResponse etc
│   └── diagrams/
│       ├── component_diagram.py    # Just GetComponentDiagramUseCase
│       ├── container_diagram.py
│       ├── deployment_diagram.py
│       ├── dynamic_diagram.py
│       ├── system_context.py
│       └── system_landscape.py
```

---

## Phase 1: Create Diagram Domain Models

### Step 1.1: Create `domain/models/diagrams.py`

Move and rename diagram data classes:

| Current | New Name | New Location |
|---------|----------|--------------|
| `ComponentDiagramData` | `ComponentDiagram` | `domain/models/diagrams.py` |
| `ContainerDiagramData` | `ContainerDiagram` | `domain/models/diagrams.py` |
| `DeploymentDiagramData` | `DeploymentDiagram` | `domain/models/diagrams.py` |
| `DynamicDiagramData` | `DynamicDiagram` | `domain/models/diagrams.py` |
| `SystemContextDiagramData` | `SystemContextDiagram` | `domain/models/diagrams.py` |
| `SystemLandscapeDiagramData` | `SystemLandscapeDiagram` | `domain/models/diagrams.py` |
| `PersonInfo` | `PersonInfo` | `domain/models/diagrams.py` (or promote to `Person` entity) |

```python
# domain/models/diagrams.py
"""C4 Diagram domain models.

These models represent the computed data for various C4 diagram types.
They are domain objects that can be serialized to different output formats
(PlantUML, Structurizr DSL, etc.) by serializers.
"""

from pydantic import BaseModel, Field

from .component import Component
from .container import Container
from .deployment_node import DeploymentNode
from .dynamic_step import DynamicStep
from .relationship import Relationship
from .software_system import SoftwareSystem


class PersonInfo(BaseModel):
    """Minimal person info for diagrams.

    Represents a user/actor in C4 diagrams. This is a lightweight
    representation used when full Person entities aren't needed.
    """
    slug: str
    name: str
    description: str = ""


class SystemLandscapeDiagram(BaseModel):
    """Domain model for a C4 System Landscape diagram.

    Shows all software systems and their relationships at the highest level.
    """
    systems: list[SoftwareSystem] = Field(default_factory=list)
    persons: list[PersonInfo] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class SystemContextDiagram(BaseModel):
    """Domain model for a C4 System Context diagram.

    Shows a single system in context with its users and external systems.
    """
    system: SoftwareSystem
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    persons: list[PersonInfo] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class ContainerDiagram(BaseModel):
    """Domain model for a C4 Container diagram.

    Shows the containers within a software system.
    """
    system: SoftwareSystem
    containers: list[Container] = Field(default_factory=list)
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    persons: list[PersonInfo] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class ComponentDiagram(BaseModel):
    """Domain model for a C4 Component diagram.

    Shows the components within a container.
    """
    system: SoftwareSystem
    container: Container
    components: list[Component] = Field(default_factory=list)
    external_containers: list[Container] = Field(default_factory=list)
    external_systems: list[SoftwareSystem] = Field(default_factory=list)
    persons: list[PersonInfo] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class DeploymentDiagram(BaseModel):
    """Domain model for a C4 Deployment diagram.

    Shows the deployment infrastructure for an environment.
    """
    environment: str
    deployment_nodes: list[DeploymentNode] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class DynamicDiagram(BaseModel):
    """Domain model for a C4 Dynamic diagram.

    Shows a sequence of interactions for a specific scenario.
    """
    sequence_name: str
    steps: list[DynamicStep] = Field(default_factory=list)
```

### Step 1.2: Export from `domain/models/__init__.py`

Add exports for all diagram models.

---

## Phase 2: Add Response Models

### Step 2.1: Add to `domain/use_cases/responses.py`

```python
# Add to responses.py

from ..models.diagrams import (
    ComponentDiagram,
    ContainerDiagram,
    DeploymentDiagram,
    DynamicDiagram,
    SystemContextDiagram,
    SystemLandscapeDiagram,
)


class GetSystemLandscapeDiagramResponse(BaseModel):
    """Response from computing a system landscape diagram."""
    diagram: SystemLandscapeDiagram | None


class GetSystemContextDiagramResponse(BaseModel):
    """Response from computing a system context diagram."""
    diagram: SystemContextDiagram | None


class GetContainerDiagramResponse(BaseModel):
    """Response from computing a container diagram."""
    diagram: ContainerDiagram | None


class GetComponentDiagramResponse(BaseModel):
    """Response from computing a component diagram."""
    diagram: ComponentDiagram | None


class GetDeploymentDiagramResponse(BaseModel):
    """Response from computing a deployment diagram."""
    diagram: DeploymentDiagram | None


class GetDynamicDiagramResponse(BaseModel):
    """Response from computing a dynamic diagram."""
    diagram: DynamicDiagram | None
```

---

## Phase 3: Refactor Use Cases

### Step 3.1: Update Each Use Case

For each diagram use case, change:

**Before:**
```python
from dataclasses import dataclass, field

@dataclass
class ComponentDiagramData:
    ...

class GetComponentDiagramUseCase:
    async def execute(self, container_slug: str) -> ComponentDiagramData | None:
        ...
        return ComponentDiagramData(...)
```

**After:**
```python
from ..models.diagrams import ComponentDiagram
from .requests import GetComponentDiagramRequest
from .responses import GetComponentDiagramResponse

class GetComponentDiagramUseCase:
    async def execute(self, request: GetComponentDiagramRequest) -> GetComponentDiagramResponse:
        ...
        diagram = ComponentDiagram(...)
        return GetComponentDiagramResponse(diagram=diagram)
```

### Step 3.2: Update Request Models

Verify/update requests in `requests.py`:

```python
class GetComponentDiagramRequest(BaseModel):
    """Request for computing a component diagram."""
    container_slug: str = Field(description="Container to show components for")
    # Remove 'format' - that's a presentation concern, not domain
```

Note: The `format` field should move to the API/presentation layer, not be part of the domain request.

---

## Phase 4: Update Serializers

### Step 4.1: Update Import Paths

Change serializers to import from new location:

**Before:**
```python
from ..domain.use_cases.diagrams.component_diagram import ComponentDiagramData
```

**After:**
```python
from ..domain.models.diagrams import ComponentDiagram
```

### Step 4.2: Update Method Signatures

```python
def serialize_component_diagram(self, data: ComponentDiagram, title: str = "") -> str:
```

---

## Phase 5: Update Callers

### Step 5.1: Update Sphinx Directives

`apps/sphinx/c4/directives/diagrams.py` - update imports and instantiation.

### Step 5.2: Update API Layer (if exists)

Any API endpoints that call these use cases need to:
1. Construct Request objects
2. Handle Response objects

---

## Phase 6: Cleanup

### Step 6.1: Remove Old Code

- Delete `ComponentDiagramData`, `ContainerDiagramData`, etc. from use case files
- Delete `PersonInfo` from `system_context.py`

### Step 6.2: Add Backward Compatibility (Optional)

If external code depends on old names, add re-exports:

```python
# domain/use_cases/diagrams/component_diagram.py
# Backward compatibility
from ...models.diagrams import ComponentDiagram as ComponentDiagramData
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/julee/c4/domain/models/diagrams.py` | All diagram domain models |

## Files to Modify

| File | Change |
|------|--------|
| `src/julee/c4/domain/models/__init__.py` | Export diagram models |
| `src/julee/c4/domain/use_cases/responses.py` | Add diagram response models |
| `src/julee/c4/domain/use_cases/requests.py` | Remove `format` from diagram requests (move to API layer) |
| `src/julee/c4/domain/use_cases/diagrams/component_diagram.py` | Refactor to use Request/Response |
| `src/julee/c4/domain/use_cases/diagrams/container_diagram.py` | Refactor to use Request/Response |
| `src/julee/c4/domain/use_cases/diagrams/deployment_diagram.py` | Refactor to use Request/Response |
| `src/julee/c4/domain/use_cases/diagrams/dynamic_diagram.py` | Refactor to use Request/Response |
| `src/julee/c4/domain/use_cases/diagrams/system_context.py` | Refactor to use Request/Response |
| `src/julee/c4/domain/use_cases/diagrams/system_landscape.py` | Refactor to use Request/Response |
| `src/julee/c4/serializers/plantuml.py` | Update imports |
| `src/julee/c4/serializers/structurizr.py` | Update imports |
| `apps/sphinx/c4/directives/diagrams.py` | Update imports and usage |

---

## Success Criteria

1. All diagram models live in `domain/models/diagrams.py`
2. All diagram use cases accept `*Request` and return `*Response`
3. Serializers import from `domain/models/`
4. Doctrine compliance tests pass for C4 context
5. Existing functionality preserved (sphinx directives, serializers work)

---

## Estimated Impact

- **6 use cases** to refactor
- **6 diagram models** to move
- **2 serializer files** to update imports
- **1 sphinx directive file** to update
- **~20 test files** may need import updates

## Risk Assessment

- **Low risk:** Moving models is straightforward
- **Medium risk:** Changing use case signatures may break callers
- **Mitigation:** Add backward compatibility aliases temporarily
