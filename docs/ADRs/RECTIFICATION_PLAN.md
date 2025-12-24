# ADR/Doctrine Rectification Plan

## Overview

This plan addresses inconsistencies between ADRs and implemented doctrine, adds missing doctrine, and discovers new domain entities needed for complete coverage.

---

## Part 1: ADR Consistency Review

### 1.1 ADR-001 (contrib-layout.md) vs Implementation

**ADR States:**
- Contrib modules under `src/julee/contrib/`
- Three-layer Temporal pattern: Layer 1 (pure), Layer 2 (activity), Layer 3 (proxy)
- Pipelines are use cases with Temporal treatment

**Implementation Status:**
- Contrib discovery: IMPLEMENTED (test_bounded_context_doctrine.py)
- Three-layer Temporal: NOT IMPLEMENTED as doctrine
- Pipeline doctrine: NOT IMPLEMENTED

**Action Required:**
1. Add Temporal layer constants to `doctrine_constants.py`
2. Create `test_temporal_doctrine.py` for Temporal pattern enforcement
3. Create `test_pipeline_doctrine.py` for pipeline compliance

### 1.2 ADR-002 (doctrine-test-architecture.md) vs Implementation

**ADR States:**
- Tests ARE doctrine (docstrings = rules)
- RFC 2119 language (MUST, SHOULD, MAY)
- Two categories: Definition tests (synthetic) + Compliance tests (real code)

**Implementation Status:**
- Pattern IMPLEMENTED in test_bounded_context_doctrine.py and test_doctrine_compliance.py
- Well structured with clear separation

**Action Required:**
- No changes needed - implementation matches ADR

### 1.3 ADR-003 (sphinx-hcd.rst) vs Implementation

**ADR States:**
- HCD entities: Persona, Journey, Epic, Story, Accelerator, Application, Integration
- Bounded context at `src/julee/hcd/`
- Clean Architecture domain structure

**Implementation Status:**
- HCD bounded context EXISTS and is discovered
- Entities are implemented
- Compliance tests validate naming

**Action Required:**
- Verify all HCD entity types have complete doctrine coverage

### 1.4 RBA ADRs vs Julee Implementation

**RBA ADR-001 (code-organisation.rst):**
- Mentions `apps/` directory for FastAPI + MCP servers
- Describes deployment structure

**RBA ADR-002 (documentation-organisation.rst):**
- Literate documentation approach
- Sphinx-based doc generation

**Action Required:**
1. Add `Apps` layer doctrine constants (already in doctrine_constants.py)
2. Create `test_apps_doctrine.py` for apps layer compliance
3. Verify deployment layer is excluded from bounded context discovery

---

## Part 2: Missing Doctrine Implementation

### 2.1 Temporal Layer Doctrine (NEW)

**File:** `src/julee/shared/domain/doctrine_constants.py`

Add constants:
```python
# =============================================================================
# TEMPORAL LAYER PATTERN
# =============================================================================
# Three-layer pattern for Temporal workflow integration.

TEMPORAL_LAYER_1: Final[str] = "layer1_pure"
"""Layer 1: Pure business logic.

Contains: Domain-only code with no Temporal dependencies
Can import: models only
Testable: Direct unit tests
"""

TEMPORAL_LAYER_2: Final[str] = "layer2_activity"
"""Layer 2: Temporal activities.

Contains: @activity decorated functions wrapping Layer 1
Can import: Layer 1, Temporal SDK
Testable: Activity test environment
"""

TEMPORAL_LAYER_3: Final[str] = "layer3_proxy"
"""Layer 3: Workflow proxies.

Contains: @workflow decorated classes orchestrating activities
Can import: Layer 2 (via execute_activity), Temporal SDK
Testable: Workflow test environment
"""

TEMPORAL_LAYER_SUFFIXES: Final[dict[str, str]] = {
    "workflow": "Workflow",
    "activity": "Activity",
}
```

### 2.2 Pipeline Doctrine (NEW)

**File:** `src/julee/shared/tests/domain/use_cases/test_pipeline_doctrine.py`

```python
class TestPipelineNaming:
    """Doctrine about pipeline naming conventions."""

    def test_pipeline_MUST_end_with_Pipeline(self):
        """All pipeline class names MUST end with 'Pipeline'."""

    def test_pipeline_MUST_have_execute_method(self):
        """All pipelines MUST have an execute() method."""

    def test_pipeline_MUST_have_steps_attribute(self):
        """All pipelines MUST define their steps as a sequence."""
```

**Add to doctrine_constants.py:**
```python
PIPELINE_SUFFIX: Final[str] = "Pipeline"
"""Suffix for pipeline orchestration classes.

Pipelines are use cases that orchestrate multi-step workflows.
They may be executed directly or wrapped by Temporal Layer 2.
"""
```

### 2.3 Apps Layer Doctrine (NEW)

**File:** `src/julee/shared/tests/domain/use_cases/test_apps_doctrine.py`

```python
class TestAppsStructure:
    """Doctrine about apps layer structure."""

    def test_app_MUST_be_under_apps_directory(self):
        """All application entry points MUST be under apps/."""

    def test_app_MUST_NOT_contain_business_logic(self):
        """Apps MUST delegate to use cases, not implement business logic."""

    def test_router_MUST_end_with_router_suffix(self):
        """FastAPI routers MUST end with '_router' or 'Router'."""

class TestMCPServerCompliance:
    """Doctrine about MCP server implementations."""

    def test_mcp_server_MUST_end_with_Server(self):
        """MCP server classes MUST end with 'Server'."""

    def test_mcp_tool_MUST_have_docstring(self):
        """MCP tool methods MUST have docstrings (they become tool descriptions)."""
```

**Add to doctrine_constants.py:**
```python
# =============================================================================
# APPS LAYER ARTIFACTS
# =============================================================================

ROUTER_SUFFIXES: Final[tuple[str, ...]] = ("_router", "Router")
"""Suffixes for FastAPI router modules/classes."""

MCP_SERVER_SUFFIX: Final[str] = "Server"
"""Suffix for MCP server classes."""

CLI_GROUP_NAMES: Final[frozenset[str]] = frozenset({
    "admin",
    "cli",
})
"""Standard CLI application group names."""
```

### 2.4 Infrastructure Implementation Doctrine (NEW)

**File:** `src/julee/shared/tests/domain/use_cases/test_infrastructure_doctrine.py`

```python
class TestInfrastructureNaming:
    """Doctrine about infrastructure implementations."""

    def test_repository_impl_MUST_contain_Repository_in_name(self):
        """Repository implementations MUST contain 'Repository' in their name."""

    def test_service_impl_MUST_contain_Service_in_name(self):
        """Service implementations MUST contain 'Service' in their name."""

    def test_infrastructure_MUST_implement_protocol(self):
        """Infrastructure classes MUST implement a domain protocol."""

class TestInfrastructureDependencies:
    """Doctrine about infrastructure dependencies."""

    def test_infrastructure_MAY_import_from_domain(self):
        """Infrastructure MAY import from domain layers."""

    def test_infrastructure_MUST_NOT_be_imported_by_domain(self):
        """Infrastructure MUST NOT be imported by domain code."""
```

---

## Part 3: Domain Discovery

### 3.1 Analyze Existing Entities

**Action:** Scan all bounded contexts to catalog existing entities.

```bash
julee-admin introspect entities --all
```

Expected discoveries:
- HCD: Persona, Journey, Epic, Story, Accelerator, Application, Integration
- C4: Container, Component, Relationship, DeploymentNode
- Shared: BoundedContext, ClassInfo, MethodInfo, FieldInfo
- Contrib: Polling workflow entities, Badge entities

### 3.2 Analyze Existing Use Cases

**Action:** Scan all bounded contexts to catalog use cases.

```bash
julee-admin introspect use-cases --all
```

Validate:
- Each entity has CRUD use cases (or justification for missing)
- Each use case has matching Request
- Each use case has matching Response (SHOULD)

### 3.3 New Domain Entities to Create

Based on ADR analysis, these entities need formalization:

| Entity | Bounded Context | Purpose |
|--------|----------------|---------|
| `ImportInfo` | shared | Import statement representation (for dependency rule) |
| `EvaluationResult` | shared | Semantic evaluation output |
| `TemporalWorkflow` | contrib.polling | Workflow metadata |
| `PipelineStep` | shared | Pipeline step definition |

---

## Part 4: Constants Centralization

### 4.1 Current State

`doctrine_constants.py` contains:
- Artifact suffixes (UseCase, Request, Response, etc.)
- Layer definitions (models, use_cases, repositories, etc.)
- Reserved words
- Viewpoint slugs

### 4.2 Required Additions

Add to `doctrine_constants.py`:

```python
# =============================================================================
# PIPELINE PATTERN
# =============================================================================

PIPELINE_SUFFIX: Final[str] = "Pipeline"
PIPELINE_STEP_SUFFIX: Final[str] = "Step"

# =============================================================================
# TEMPORAL PATTERN
# =============================================================================

WORKFLOW_SUFFIX: Final[str] = "Workflow"
ACTIVITY_SUFFIX: Final[str] = "Activity"

TEMPORAL_LAYERS: Final[tuple[str, ...]] = (
    "layer1_pure",
    "layer2_activity",
    "layer3_proxy",
)

# =============================================================================
# APPS LAYER ARTIFACTS
# =============================================================================

ROUTER_SUFFIXES: Final[tuple[str, ...]] = ("_router", "Router")
MCP_SERVER_SUFFIX: Final[str] = "Server"
CLI_GROUP_SUFFIX: Final[str] = "_group"

# =============================================================================
# INFRASTRUCTURE LAYER
# =============================================================================

# Infrastructure implementations MAY use these prefixes to indicate
# the technology/framework being adapted
INFRASTRUCTURE_PREFIXES: Final[tuple[str, ...]] = (
    "Filesystem",
    "Memory",
    "Postgres",
    "Redis",
    "Http",
    "Temporal",
)
```

---

## Part 5: Implementation Order

### Phase 1: Constants & Models (Foundation)

1. Add new constants to `doctrine_constants.py`
2. Create `ImportInfo` model in `shared/domain/models/`
3. Create `EvaluationResult` model in `shared/domain/models/`
4. Update exports in `__init__.py` files

### Phase 2: Structural Doctrine Tests

1. Verify `test_dependency_rule_doctrine.py` exists and is complete
2. Create `test_pipeline_doctrine.py`
3. Create `test_temporal_doctrine.py`
4. Create `test_apps_doctrine.py`
5. Create `test_infrastructure_doctrine.py`

### Phase 3: Compliance Tests

1. Add `TestPipelineCompliance` to test_doctrine_compliance.py
2. Add `TestTemporalCompliance` to test_doctrine_compliance.py
3. Add `TestAppsCompliance` to test_doctrine_compliance.py
4. Add `TestInfrastructureCompliance` to test_doctrine_compliance.py

### Phase 4: Domain Discovery & Validation

1. Run `julee-admin introspect` commands to catalog all artifacts
2. Identify gaps (missing use cases, requests, responses)
3. Create missing artifacts or document why they're intentionally absent
4. Update ADRs to reflect actual implementation

### Phase 5: ADR Updates

1. Update ADR-001 to reference implemented doctrine constants
2. Create ADR for Temporal pattern (if not exists)
3. Create ADR for Pipeline pattern (if not exists)
4. Add cross-references between ADRs and doctrine tests

---

## Part 6: Success Criteria

### Measurable Outcomes

1. `julee-admin doctrine list` shows all doctrine areas:
   - Entity Compliance
   - Use Case Compliance
   - Request Compliance
   - Response Compliance
   - Repository Protocol Compliance
   - Service Protocol Compliance
   - Dependency Rule Compliance
   - Pipeline Compliance (NEW)
   - Temporal Compliance (NEW)
   - Apps Compliance (NEW)
   - Infrastructure Compliance (NEW)

2. `julee-admin doctrine verify` passes with no violations

3. All constants used in tests are defined in `doctrine_constants.py`

4. ADRs reference `doctrine_constants.py` for authoritative values

5. New bounded contexts automatically validated against all doctrine

### Documentation Outcomes

1. `julee-admin doctrine show --verbose` generates complete doctrine reference
2. Doctrine tests serve as executable specification
3. ADRs provide rationale; tests provide enforcement

---

## Appendix: File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `test_pipeline_doctrine.py` | Pipeline pattern doctrine tests |
| `test_temporal_doctrine.py` | Temporal layer doctrine tests |
| `test_apps_doctrine.py` | Apps layer doctrine tests |
| `test_infrastructure_doctrine.py` | Infrastructure implementation doctrine tests |
| `shared/domain/models/import_info.py` | ImportInfo model |
| `shared/domain/models/evaluation.py` | EvaluationResult model |

### Modified Files

| File | Changes |
|------|---------|
| `doctrine_constants.py` | Add Pipeline, Temporal, Apps, Infrastructure constants |
| `test_doctrine_compliance.py` | Add compliance test classes for new doctrine areas |
| `shared/domain/models/__init__.py` | Export new models |
| `docs/ADRs/001-contrib-layout.md` | Reference doctrine constants |

---

## Notes

- This plan does NOT include implementation of SemanticEvaluationService (protocol only)
- Temporal doctrine is optional if no Temporal workflows exist in codebase
- Apps doctrine may need adjustment based on actual apps/ structure
- Infrastructure doctrine should be permissive to allow technology flexibility
