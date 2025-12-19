# sphinx_hcd Architecture Analysis

This document describes the architecture of the `sphinx_hcd` Sphinx extension, which encodes Human-Centered Design (HCD) semantics in documentation. Use this as a reference for implementing similar semantic domain tools.

---

## 1. Overview

`sphinx_hcd` is a Sphinx extension that:
- Defines domain-specific entities (Story, Epic, Journey, Persona, App, Accelerator, Integration)
- Extracts data from multiple sources (Gherkin files, YAML manifests, Python AST, RST directives)
- Renders cross-referenced documentation with relationship graphs
- Exposes the domain model via MCP for programmatic access

The system follows **clean architecture** with clear separation between domain, repositories, use cases, and presentation (Sphinx directives).

---

## 2. Package Structure

```
sphinx_hcd/
├── domain/
│   ├── models/           # Pure dataclasses for each entity
│   │   ├── story.py
│   │   ├── epic.py
│   │   ├── journey.py
│   │   ├── persona.py
│   │   ├── app.py
│   │   ├── accelerator.py
│   │   └── integration.py
│   ├── repositories/     # Abstract repository protocols
│   │   └── __init__.py   # Repository protocols per entity
│   └── use_cases/        # Business logic, queries, cross-referencing
│       ├── story/
│       ├── epic/
│       ├── journey/
│       ├── app/
│       ├── accelerator/
│       ├── integration/
│       └── queries/      # Cross-entity relationship queries
├── repositories/
│   ├── memory/           # In-memory repository implementations
│   └── file/             # File-based persistence (optional)
├── parsers/              # Data extraction from external sources
│   ├── gherkin.py        # Gherkin .feature files → Stories
│   ├── manifest.py       # YAML manifests → Apps, Integrations
│   └── bounded_context.py # Python AST → BoundedContextInfo
├── sphinx/
│   ├── directives/       # RST directive implementations
│   ├── events.py         # Sphinx event handlers
│   ├── config.py         # Extension configuration
│   └── context.py        # HCDContext (holds repositories + config)
├── serializers/          # JSON/YAML serialization
└── utils.py              # slugify(), normalize_name(), etc.
```

---

## 3. Domain Models

Each entity is a Python dataclass with:
- **Identity**: A `slug` (URL-safe identifier)
- **Core fields**: Domain-specific attributes
- **Normalization**: Methods for case-insensitive matching
- **Tracking**: `docname` for incremental build support

### Pattern: Entity Definition

```python
@dataclass
class Story:
    slug: str                    # Identity: "{app_slug}--{feature_slug}"
    feature_title: str           # Human-readable title
    persona: str                 # "Staff Member", "Admin", etc.
    i_want: str                  # Action/capability
    so_that: str                 # Benefit/value
    app_slug: str                # Parent app
    path: Path | None = None     # Source file location
    snippet: str = ""            # Raw Gherkin text

    @property
    def normalized_persona(self) -> str:
        return normalize_name(self.persona)

    @property
    def normalized_title(self) -> str:
        return normalize_name(self.feature_title)
```

### Key Entities and Relationships

```
┌─────────────┐      contains       ┌─────────────┐
│    Epic     │◄────────────────────│    Story    │
└─────────────┘                     └─────────────┘
                                          │
                                          │ persona
                                          ▼
┌─────────────┐      steps          ┌─────────────┐
│   Journey   │────────────────────►│   Persona   │◄──── derived from stories
└─────────────┘                     └─────────────┘
      │
      │ depends_on
      ▼
┌─────────────┐
│   Journey   │  (prerequisite)
└─────────────┘

┌─────────────┐    accelerators     ┌─────────────┐
│     App     │────────────────────►│ Accelerator │
└─────────────┘                     └─────────────┘
                                          │
                                          │ sources_from / publishes_to
                                          ▼
                                    ┌─────────────┐
                                    │ Integration │
                                    └─────────────┘
```

---

## 4. Repository Pattern

Repositories provide CRUD operations with a consistent interface.

### Protocol Definition

```python
class StoryRepository(Protocol):
    def save(self, story: Story) -> None: ...
    def get(self, slug: str) -> Story | None: ...
    def get_all(self) -> list[Story]: ...
    def delete(self, slug: str) -> None: ...
    def clear_by_docname(self, docname: str) -> None: ...  # Incremental builds
```

### In-Memory Implementation

```python
class MemoryStoryRepository:
    def __init__(self):
        self._stories: dict[str, Story] = {}

    def save(self, story: Story) -> None:
        self._stories[story.slug] = story

    def get(self, slug: str) -> Story | None:
        return self._stories.get(slug)

    def get_all(self) -> list[Story]:
        return list(self._stories.values())
```

### Context Object

A central context holds all repositories and configuration:

```python
@dataclass
class HCDContext:
    config: HCDConfig
    story_repo: StoryRepository
    epic_repo: EpicRepository
    journey_repo: JourneyRepository
    persona_repo: PersonaRepository
    app_repo: AppRepository
    accelerator_repo: AcceleratorRepository
    integration_repo: IntegrationRepository
```

---

## 5. Use Cases Layer

Use cases encapsulate business logic and cross-entity queries.

### CRUD Use Cases

Each entity has standard use cases:

```python
# story/create.py
def create_story(repo: StoryRepository, story: Story) -> Story:
    repo.save(story)
    return story

# story/get.py
def get_story(repo: StoryRepository, slug: str) -> Story | None:
    return repo.get(slug)
```

### Cross-Reference Queries

The `queries/` module provides relationship traversal:

```python
# queries/story_queries.py
def get_epics_for_story(
    story: Story,
    epic_repo: EpicRepository
) -> list[Epic]:
    """Find all epics that reference this story."""
    epics = []
    for epic in epic_repo.get_all():
        if story.normalized_title in [
            normalize_name(ref) for ref in epic.story_refs
        ]:
            epics.append(epic)
    return epics

def get_stories_for_persona(
    persona_name: str,
    story_repo: StoryRepository
) -> list[Story]:
    """Find all stories for a persona."""
    normalized = normalize_name(persona_name)
    return [
        s for s in story_repo.get_all()
        if s.normalized_persona == normalized
    ]
```

### Derived Entities

Some entities are derived from others:

```python
def derive_personas(
    story_repo: StoryRepository,
    epic_repo: EpicRepository
) -> list[Persona]:
    """Derive personas from stories, enrich with app/epic associations."""
    persona_map: dict[str, Persona] = {}

    for story in story_repo.get_all():
        normalized = story.normalized_persona
        if normalized not in persona_map:
            persona_map[normalized] = Persona(
                name=story.persona,
                app_slugs=set(),
                epic_slugs=set()
            )
        persona_map[normalized].app_slugs.add(story.app_slug)

    # Enrich with epic associations
    for epic in epic_repo.get_all():
        for story in get_stories_for_epic(epic, story_repo):
            normalized = story.normalized_persona
            if normalized in persona_map:
                persona_map[normalized].epic_slugs.add(epic.slug)

    return list(persona_map.values())
```

---

## 6. Sphinx Directive Pattern

Directives use a **placeholder pattern** to handle cross-document references.

### The Problem

Sphinx processes documents independently. When directive A references entity B defined in another document, B may not exist yet.

### The Solution: Placeholder Nodes

```python
class StoryListPlaceholder(nodes.General, nodes.Element):
    """Placeholder replaced during doctree-resolved phase."""
    pass

class StoryListDirective(HCDDirective):
    def run(self):
        # Create placeholder with parameters
        node = StoryListPlaceholder()
        node['app_slug'] = self.arguments[0]
        return [node]
```

### Event-Driven Resolution

```python
def setup(app: Sphinx):
    app.connect('builder-inited', on_builder_inited)
    app.connect('doctree-read', on_doctree_read)
    app.connect('doctree-resolved', on_doctree_resolved)
    app.connect('env-purge-doc', on_env_purge_doc)

def on_builder_inited(app: Sphinx):
    """Initialize context, load static data (features, manifests)."""
    context = HCDContext(...)
    load_stories_from_features(context)
    load_apps_from_manifests(context)
    app.env.hcd_context = context

def on_doctree_read(app: Sphinx, doctree: nodes.document):
    """Resolve within-document placeholders."""
    for node in doctree.findall(SomeLocalPlaceholder):
        replacement = render_local_content(node, app.env.hcd_context)
        node.replace_self(replacement)

def on_doctree_resolved(app: Sphinx, doctree: nodes.document, docname: str):
    """Resolve cross-document placeholders (all documents parsed)."""
    context = app.env.hcd_context

    for node in doctree.findall(StoryListPlaceholder):
        app_slug = node['app_slug']
        stories = get_stories_for_app(app_slug, context.story_repo)
        replacement = render_story_list(stories, docname, context)
        node.replace_self(replacement)

def on_env_purge_doc(app: Sphinx, env, docname: str):
    """Clear entities defined in this document (incremental builds)."""
    context = env.hcd_context
    context.journey_repo.clear_by_docname(docname)
    context.epic_repo.clear_by_docname(docname)
```

### Base Directive Class

```python
class HCDDirective(SphinxDirective):
    """Base class with common utilities."""

    @property
    def context(self) -> HCDContext:
        return self.env.hcd_context

    def make_app_link(self, app_slug: str) -> str:
        """Build relative link to app page."""
        depth = self.env.docname.count('/')
        prefix = '../' * depth
        return f"{prefix}applications/{app_slug}.html"

    def make_story_link(self, story: Story) -> str:
        """Link to story anchor on app page."""
        depth = self.env.docname.count('/')
        prefix = '../' * depth
        return f"{prefix}stories/{story.app_slug}.html#{story.slug}"
```

---

## 7. Data Loading Pipeline

Data flows from multiple sources into the domain model:

```
┌──────────────────┐     GherkinParser      ┌─────────────────┐
│  .feature files  │───────────────────────►│  StoryRepository│
└──────────────────┘                        └─────────────────┘

┌──────────────────┐     ManifestParser     ┌─────────────────┐
│   app.yaml       │───────────────────────►│   AppRepository │
└──────────────────┘                        └─────────────────┘

┌──────────────────┐     ManifestParser     ┌─────────────────┐
│ integration.yaml │───────────────────────►│IntegrationRepo  │
└──────────────────┘                        └─────────────────┘

┌──────────────────┐    BoundedContextParser┌─────────────────┐
│  Python source   │───────────────────────►│BoundedContextInfo│
└──────────────────┘    (AST introspection) └─────────────────┘

┌──────────────────┐                        ┌─────────────────┐
│  RST directives  │───────────────────────►│ Journey/Epic/   │
│  (define-*)      │    Directive.run()     │ Accelerator Repo│
└──────────────────┘                        └─────────────────┘
```

### Parser Example

```python
def parse_gherkin_story(path: Path, app_slug: str) -> Story | None:
    """Extract story from Gherkin feature file."""
    content = path.read_text()

    # Match: As a <persona>, I want to <action> so that <benefit>
    match = re.search(
        r'As an?\s+(.+?),\s+I want to?\s+(.+?)\s+so that\s+(.+)',
        content,
        re.IGNORECASE
    )
    if not match:
        return None

    feature_title = extract_feature_title(content)
    return Story(
        slug=f"{app_slug}--{slugify(feature_title)}",
        feature_title=feature_title,
        persona=match.group(1).strip(),
        i_want=match.group(2).strip(),
        so_that=match.group(3).strip(),
        app_slug=app_slug,
        path=path,
        snippet=content
    )
```

---

## 8. Normalization Strategy

Consistent matching across the system uses normalization:

```python
def normalize_name(name: str) -> str:
    """Normalize for case-insensitive, format-independent matching."""
    return name.lower().replace('-', ' ').replace('_', ' ').strip()

def slugify(text: str) -> str:
    """Create URL-safe slug from text."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')
```

This allows:
- "Staff Member" matches "staff-member" matches "staff_member"
- Story references in epics match regardless of case/formatting

---

## 9. MCP Integration

The domain model is exposed via MCP (Model Context Protocol) for programmatic access:

```python
# hcd_mcp/server.py
@server.tool()
def mcp_create_story(
    feature_title: str,
    persona: str,
    app_slug: str,
    i_want: str = "do something",
    so_that: str = "achieve a goal"
) -> dict:
    """Create a user story."""
    story = Story(
        slug=f"{app_slug}--{slugify(feature_title)}",
        feature_title=feature_title,
        persona=persona,
        i_want=i_want,
        so_that=so_that,
        app_slug=app_slug
    )
    context.story_repo.save(story)
    return asdict(story)

@server.tool()
def mcp_list_stories() -> list[dict]:
    """List all stories."""
    return [asdict(s) for s in context.story_repo.get_all()]
```

---

## 10. Key Design Decisions

### 1. Placeholder Pattern for Cross-References
- Directives return placeholder nodes during parsing
- Placeholders resolved after all documents parsed
- Enables forward references and cross-document links

### 2. Derived vs Defined Entities
- Personas derived automatically from stories
- Can be enriched with explicitly defined personas
- Flexible: works with minimal or maximal specification

### 3. Slug-Based Identity
- All entities have URL-safe slugs
- Slugs used for repository keys and HTML anchors
- Compound slugs avoid collisions (e.g., `{app}--{feature}`)

### 4. Normalized Matching
- Case-insensitive, format-independent matching
- Users write natural text; system handles normalization
- Reduces friction in RST authoring

### 5. Incremental Build Support
- Entities track source `docname`
- `clear_by_docname()` on repository for purging
- Sphinx's `env-purge-doc` event triggers cleanup

### 6. Clean Architecture Layers
- Domain models: Pure dataclasses, no dependencies
- Repositories: Storage abstraction
- Use cases: Business logic
- Sphinx directives: Presentation only

---

## 11. Implementing a Parallel Semantic Domain

To implement a similar tool for a different domain:

### Step 1: Define Domain Entities
- Identify core entities and relationships
- Create dataclasses with slug identity
- Add normalization for matching

### Step 2: Implement Repositories
- Create protocols for each entity
- Implement in-memory storage
- Add `clear_by_docname()` for incremental builds

### Step 3: Create Use Cases
- CRUD operations per entity
- Cross-reference queries
- Derived entity computation

### Step 4: Build Sphinx Directives
- Define placeholder nodes
- Implement directives that save to repositories
- Create base directive class with link builders

### Step 5: Wire Up Events
- `builder-inited`: Initialize context, load data
- `doctree-read`: Resolve local placeholders
- `doctree-resolved`: Resolve cross-document placeholders
- `env-purge-doc`: Clean up incremental builds

### Step 6: Add MCP Interface (Optional)
- Expose CRUD operations as MCP tools
- Enable programmatic access outside Sphinx

---

## 12. File Locations Reference

Key files in the sphinx_hcd implementation:

| Component | Location |
|-----------|----------|
| Domain models | `src/julee/docs/sphinx_hcd/domain/models/` |
| Repository protocols | `src/julee/docs/sphinx_hcd/domain/repositories/` |
| Memory repositories | `src/julee/docs/sphinx_hcd/repositories/memory/` |
| Use cases | `src/julee/docs/sphinx_hcd/domain/use_cases/` |
| Parsers | `src/julee/docs/sphinx_hcd/parsers/` |
| Sphinx directives | `src/julee/docs/sphinx_hcd/sphinx/directives/` |
| Event handlers | `src/julee/docs/sphinx_hcd/sphinx/events.py` |
| Context | `src/julee/docs/sphinx_hcd/sphinx/context.py` |
| MCP server | `src/julee/docs/hcd_mcp/` |
| Utilities | `src/julee/docs/sphinx_hcd/utils.py` |
