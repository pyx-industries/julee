# Sphinx HCD Extensions

Sphinx extensions for documenting Julee-based solutions using Human-Centered Design patterns.

## Installation

```bash
pip install julee
```

Or for development:

```bash
pip install -e /path/to/julee
```

## Quick Start

Add to your `conf.py`:

```python
extensions = ["julee.docs.sphinx_hcd"]
```

The default configuration matches the standard Julee solution layout.

## Configuration

To customize, use the factory function and override specific values:

```python
from julee.docs.sphinx_hcd import config_factory

sphinx_hcd = config_factory()
sphinx_hcd['paths']['feature_files'] = 'tests/bdd/'
```

### Configuration Keys

**paths** - Filesystem locations relative to project root:

| Key | Default | Description |
|-----|---------|-------------|
| `feature_files` | `tests/e2e/` | Where `.feature` files live (`{app}/features/*.feature`) |
| `app_manifests` | `apps/` | Where `app.yaml` files live (`*/app.yaml`) |
| `integration_manifests` | `src/integrations/` | Where `integration.yaml` files live |
| `bounded_contexts` | `src/` | For accelerator source scanning |

**docs_structure** - RST file locations relative to docs root:

| Key | Default | Description |
|-----|---------|-------------|
| `applications` | `applications` | App documentation pages |
| `personas` | `users/personas` | Persona documentation pages |
| `journeys` | `users/journeys` | Journey documentation pages |
| `epics` | `users/epics` | Epic documentation pages |
| `accelerators` | `domain/accelerators` | Accelerator documentation pages |
| `integrations` | `integrations` | Integration documentation pages |
| `stories` | `users/stories` | Story index pages (per-app) |

## YAML Manifest Schemas

### app.yaml

Located at `apps/{app-slug}/app.yaml`:

```yaml
# Required
name: My Application           # Human-readable name

# Required - determines grouping in app-index
type: member-tool              # One of: staff, external, member-tool

# Optional
status: Active                 # Free-form status text
description: |                 # Rendered as intro paragraph
  Description of the application and its purpose.
accelerators:                  # List of accelerator slugs this app uses
  - some-accelerator
  - another-accelerator
```

### integration.yaml

Located at `src/integrations/{module}/integration.yaml`:

```yaml
# Optional - defaults to directory name with underscores replaced by hyphens
slug: external-api

# Optional - defaults to slug title-cased
name: External API Integration

# Optional
description: |
  Connects to external API for data exchange.

# Required - determines arrow direction in diagrams
direction: inbound             # One of: inbound, outbound, bidirectional

# Optional - external systems this integration depends on
depends_on:
  - name: External Service     # Required within each entry
    url: https://api.example.com  # Optional - makes name a link
    description: Data source   # Optional - shown in diagram
```

### Feature Files (.feature)

Located at `{feature_files}/{app-slug}/features/*.feature`:

```gherkin
Feature: Submit Order

  As a Customer
  I want to submit an order
  So that I can purchase products

  Scenario: Successful order submission
    Given I have items in my cart
    When I submit my order
    Then the order should be confirmed
```

The persona is extracted from the "As a ..." line. If missing, defaults to "unknown" and a warning is emitted. Stories with "unknown" persona still appear in all-story views but not in persona-filtered views.

## Directives Reference

### Stories

Stories are derived from Gherkin `.feature` files.

#### `.. story::`

Render a single story with full scenario details.

```rst
.. story:: my-app/Submit Order
```

#### `.. stories::`

List all stories for an app as a bullet list.

```rst
.. stories:: my-app
```

#### `.. story-index::`

Generate an index of all stories grouped by app.

```rst
.. story-index::
```

#### `.. story-list-for-persona::`

List stories for a specific persona.

```rst
.. story-list-for-persona:: Customer
```

#### `.. story-list-for-app::`

List stories for an app (alternative to `stories`).

```rst
.. story-list-for-app:: my-app
```

#### `.. story-app::`

Embed all stories for an app inline (full details, not just links).

```rst
.. story-app:: my-app
```

#### Deprecated Aliases

The following aliases emit deprecation warnings:

| Old Directive | New Directive |
|---------------|---------------|
| `gherkin-story` | `story` |
| `gherkin-stories` | `stories` |
| `gherkin-stories-index` | `story-index` |
| `gherkin-stories-for-persona` | `story-list-for-persona` |
| `gherkin-stories-for-app` | `story-list-for-app` |
| `gherkin-app-stories` | `story-app` |

### Journeys

User journeys composed of stories, epics, and phases.

#### `.. define-journey::`

Define a journey with optional description.

```rst
.. define-journey:: onboarding

   The complete journey for a new user to get started.
```

#### `.. step-story::`

Add a story step to the current journey.

```rst
.. step-story:: Submit Order
```

#### `.. step-epic::`

Add an epic step to the current journey.

```rst
.. step-epic:: checkout-flow
```

#### `.. step-phase::`

Add a phase marker (non-linking step).

```rst
.. step-phase:: Implementation
```

#### `.. journey-index::`

Generate an index of all journeys.

```rst
.. journey-index::
```

#### `.. journey-dependency-graph::`

Render a PlantUML dependency graph for a journey.

```rst
.. journey-dependency-graph:: onboarding
```

#### `.. journeys-for-persona::`

List journeys available for a persona.

```rst
.. journeys-for-persona:: Customer
```

### Epics

Collections of related stories.

#### `.. define-epic::`

Define an epic with description.

```rst
.. define-epic:: checkout-flow

   Covers the complete checkout process from cart to confirmation.
```

#### `.. epic-story::`

Reference a story as part of the current epic.

```rst
.. epic-story:: Submit Order
.. epic-story:: Process Payment
```

#### `.. epic-index::`

Generate an index of all epics with unassigned stories.

```rst
.. epic-index::
```

#### `.. epics-for-persona::`

List epics for a persona (derived from stories).

```rst
.. epics-for-persona:: Customer
```

### Applications

Application documentation driven by `app.yaml` manifests.

#### `.. define-app::`

Render app info from manifest plus derived data (personas, journeys, epics).

```rst
.. define-app:: my-app
```

#### `.. app-index::`

Generate index tables grouped by app type.

```rst
.. app-index::
```

#### `.. apps-for-persona::`

List apps for a specific persona.

```rst
.. apps-for-persona:: Customer
```

### Accelerators

Domain accelerator documentation with bounded context scanning.

#### `.. define-accelerator::`

Define an accelerator with full metadata.

```rst
.. define-accelerator:: payments
   :name: Payments Accelerator
   :status: Active
   :apps: checkout-app, admin-portal
   :integrations: payment-gateway
```

#### `.. accelerator-index::`

Generate index of all accelerators.

```rst
.. accelerator-index::
```

#### `.. accelerator-status::`

Show accelerator implementation status.

```rst
.. accelerator-status:: payments
```

#### `.. accelerators-for-app::`

List accelerators used by an app.

```rst
.. accelerators-for-app:: checkout-app
```

#### `.. dependent-accelerators::`

List accelerators that depend on this one.

```rst
.. dependent-accelerators:: core-domain
```

#### `.. accelerator-dependency-diagram::`

Render PlantUML dependency diagram.

```rst
.. accelerator-dependency-diagram:: payments
```

#### `.. src-accelerator-backlinks::`

Show what references an accelerator in source code.

```rst
.. src-accelerator-backlinks:: payments
```

#### `.. src-app-backlinks::`

Show what accelerators an app uses based on source code.

```rst
.. src-app-backlinks:: checkout-app
```

### Integrations

External integration documentation driven by `integration.yaml` manifests.

#### `.. define-integration::`

Render integration info from YAML manifest.

```rst
.. define-integration:: payment-gateway
```

#### `.. integration-index::`

Generate integration index with architecture diagram.

```rst
.. integration-index::
```

### Personas

Auto-generated PlantUML diagrams showing persona-epic-app relationships.

#### `.. persona-diagram::`

Generate a use case diagram for a single persona showing their epics and apps.

```rst
.. persona-diagram:: Underwater Basket Weaver
```

Generates a PlantUML diagram with:
- The persona as an actor
- Epics they participate in as use cases (derived from stories)
- Apps they interact with as components

#### `.. persona-index-diagram::`

Generate a use case diagram for a group of personas (staff or external).

```rst
.. persona-index-diagram:: staff
.. persona-index-diagram:: customers
.. persona-index-diagram:: vendors
```

Groups are determined by the `type` field from `app.yaml` manifests. Any value is accepted—the directive filters personas to those using apps with a matching type.

## Expected Directory Structure

```
project/
├── apps/
│   └── {app-slug}/
│       └── app.yaml
├── src/
│   ├── {bounded-context}/
│   │   └── ... (Python packages)
│   └── integrations/
│       └── {module}/
│           └── integration.yaml
├── tests/
│   └── e2e/
│       └── {app-slug}/
│           └── features/
│               └── *.feature
└── docs/
    ├── conf.py
    ├── applications/
    │   └── {app-slug}.rst
    ├── users/
    │   ├── personas/
    │   │   └── {persona-slug}.rst
    │   ├── journeys/
    │   │   └── {journey-slug}.rst
    │   ├── epics/
    │   │   └── {epic-slug}.rst
    │   └── stories/
    │       └── {app-slug}.rst
    ├── domain/
    │   └── accelerators/
    │       └── {accelerator-slug}.rst
    └── integrations/
        └── {integration-slug}.rst
```

## Dependencies

- `sphinx` >= 4.0
- `pyyaml`
- `sphinxcontrib-plantuml` (for diagrams)

## Build Warnings

The extension emits warnings during build for:

- Apps without documentation pages
- Apps without stories
- Documented apps without manifests
- Stories referencing unknown apps
- Stories with missing "As a..." persona (defaults to "unknown")
- Epic references to unknown stories
- Missing persona documentation

## Architecture (Developer Guide)

This module follows **julee clean architecture patterns**:

```
sphinx_hcd/
├── domain/                 # Domain layer (framework-agnostic)
│   ├── models/            # Pydantic entities
│   ├── repositories/      # Repository protocols (async)
│   └── use_cases/         # Business logic
├── repositories/          # Repository implementations
│   └── memory/           # In-memory implementations
├── parsers/              # Parsing logic
│   ├── gherkin.py       # Feature file parsing
│   ├── yaml.py          # Manifest parsing
│   └── ast.py           # Python introspection
├── sphinx/               # Application layer (Sphinx-specific)
│   ├── adapters.py      # Sync wrappers for async repos
│   ├── context.py       # HCDContext container
│   ├── directives/      # RST directives
│   └── event_handlers/  # Sphinx lifecycle handlers
└── tests/               # Test suite
```

### Async Repositories with Sync Adapters

Domain repositories are async (following julee patterns), but Sphinx directives
are synchronous. The `SyncRepositoryAdapter` bridges this gap:

```python
from julee.docs.sphinx_hcd.sphinx.adapters import SyncRepositoryAdapter
from julee.docs.sphinx_hcd.repositories.memory.story import MemoryStoryRepository

# Create async repo
async_repo = MemoryStoryRepository()

# Wrap for sync access in Sphinx directives
sync_repo = SyncRepositoryAdapter(async_repo)

# Use synchronously
story = sync_repo.get("my-story-slug")
all_stories = sync_repo.list_all()
```

### Running Tests

```bash
# Run all sphinx_hcd tests
pytest src/julee/docs/sphinx_hcd/tests/

# Run specific test category
pytest src/julee/docs/sphinx_hcd/tests/domain/ -v
pytest src/julee/docs/sphinx_hcd/tests/repositories/ -v
```
