# ADR 012: Separating the Framework from Domain Kits

## Status

Draft

## Date

2026-09-21

## Context

ADR 011 made `master` the canonical julee line. It left one question open: how to separate framework concerns, which every julee solution needs, from domain-specific concerns, which should be pluggable and may not belong in the framework at all.

Today that line is not drawn. On `master`:

- **Framework names hold CEAP code.** `julee.api`, `julee.repositories`, `julee.services` and `julee.util.repos` are CEAP's implementations under generic names. About 30 files in them import `julee.contrib.ceap` or the knowledge service.
- **Every install pulls in CEAP's stack.** The base dependencies include `anthropic`, `minio`, `python-magic`, `multihash`, `jsonschema` and `fastapi`, so a solution that uses none of CEAP still gets all of them.
- **CEAP demo data ships in the wheel.** `julee/fixtures/` (knowledge-service YAML and a sample spec sheet) is package data.
- **The kernel knows its plug-ins by name.** `VIEWPOINT_SLUGS = {"hcd", "c4"}` in `core/doctrine_constants.py` hard-codes two bounded contexts that are not part of the kernel.
- **The package describes itself by its first domain.** The description and keywords ("accountable and transparent digital supply chains", "document-processing", "ai") describe CEAP, not the framework.

The archived line (ADR 011) went further in the same direction. Its `core` held about 27 meta-model entities, and it added `hcd`, `c4`, `supply_chain` and `contrib/untp` to the framework package.

ADR 001 answered part of the question: contrib modules are self-contained julee solutions. But it kept them inside the `julee` distribution as `julee.contrib.*`, so they still share its version, its dependencies and its release. Django shows where that leads. `django.contrib` once included `comments`, `localflavor` and `formtools`, which later had to be spun out at the cost of a breaking change for their users. Removing something from a framework is expensive. Never adding it is free.

What we want is the other half of the Django model: a small core, enough batteries to get going quickly, and one showcase application that proves the plug-in model works. In Django that application is the admin. Anyone else can build and distribute pluggable apps against the same contract.

## Decision

### 1. Three rings

Julee code falls into three rings. The test for placing something is: *would a solution in an unrelated domain want this?*

| Ring | Answer to the test | Ships as |
|---|---|---|
| **Kernel** | Always | The `julee` distribution, with minimal dependencies |
| **Integrations** (the "batteries") | Often, but not always | Modules in the `julee` distribution, each behind a pip extra |
| **Kits** | Only if it works in that problem space | Separate distributions, one per kit |

A second test settles most borderline cases: code that refers to a specific business entity (a document, a credential, a persona) is not kernel code.

#### Kernel

The kernel contains the concepts every solution uses and nothing else:

- The base classes and conventions: `Entity`, `Acknowledgement`, UseCase/Request/Response, and the bases for repository and service protocols.
- Framework services: clock and execution.
- In-memory repository support, because every solution's tests need it.
- The build-time CRUD generator (ADR 008).
- Doctrine, policy and introspection (ADRs 002, 005), and the `julee` CLI that runs them.
- The kit contract (section 3).

Only `pydantic` is a runtime dependency of the kernel. Doctrine, introspection and the CLI need `griffe`, `click` and `pytest`, so they install with `julee[doctrine]`. Production images then don't carry development tooling.

Which parts of the archived line's meta-model belong in the kernel is decided one entity at a time, under ADR 011's port-or-drop process. The rule is that the kernel keeps only the concepts doctrine and the kit contract need. A concept used only to *describe* a solution (a persona, an epic, a C4 container) belongs in the viewpoints kit (section 4).

#### Integrations

Integrations connect julee to specific third-party technologies, with no domain concepts in them. Each lives in its own subpackage of `julee.integrations`, named after the technology, and has a matching extra:

| Module | Extra | Contents |
|---|---|---|
| `julee.integrations.temporal` | `julee[temporal]` | Pipeline decorators, the data converter, activity collection, the Temporal clock and execution services |
| `julee.integrations.fastapi` | `julee[fastapi]` | App-factory helpers, RFC 9457 problem details, security-headers middleware |
| `julee.integrations.minio` | `julee[minio]` | The object-storage client and repository base |
| `julee.integrations.sphinx` | `julee[sphinx]` | Directives that project kernel concepts (bounded contexts, use cases, entities, pipelines) into documentation |

Rules:

- The kernel never imports `julee.integrations`.
- An integration imports its third-party dependency only within its own subpackage. That keeps `import julee` working without any extras installed.
- An integration contains no domain concepts. If it needs an entity that the kernel doesn't define, it belongs in a kit.

#### Kits

A kit is a distribution that contains domain code: bounded contexts that solve problems in a particular area, together with their infrastructure and app contributions. The current candidates are:

| Kit | Distribution | Import package |
|---|---|---|
| CEAP (capture, extract, assemble, publish) | `julee-ceap` | `julee_ceap` |
| Polling | `julee-polling` | `julee_polling` |
| UNTP | `julee-untp` | `julee_untp` |
| Supply chain | `julee-supply-chain` | `julee_supply_chain` |
| Ontology mapper | `julee-onto-mapper` | `julee_onto_mapper` |

Each kit is a julee solution in its own right, as ADR 001 already requires. It has its own `[tool.julee]` configuration, its own doctrine run in CI, and its own dependencies. For example, `julee-ceap` is the only kit that depends on `anthropic`.

Kits use flat top-level import packages (`julee_ceap`), not `julee.contrib.ceap`. Installing files from one distribution into another distribution's package is fragile, and a flat name lets a kit move between repositories without changing its import path.

### 2. Two repositories

| Repository | Workspace members |
|---|---|
| `julee` | `julee` (kernel and integrations) |
| `julee-kits` | One member per kit, including the viewpoints kit |

Both are uv workspaces, with one `pyproject.toml` per distribution.

- The viewpoints kit lived with the kernel at first, so that a change to the kit contract had to update it in the same pull request. It moved to julee-kits in September 2026: the rule "the framework and its showcase share a repository, domain kits do not" could not be guessed from the names, and misdirected three of the four PyPI publishers. Every kit now lives in julee-kits, and a kit's repository is the one its name implies.
- Domain kits share one repository while they share maintainers and a release rhythm. A kit that gets its own maintainers or cadence can move to its own repository, and its imports don't change.

### 3. The kit contract

The kit contract is the kernel's public interface for plug-ins. It plays the role Django's `INSTALLED_APPS` and `AppConfig` play for Django apps. It is public API under semantic versioning: a breaking change to it requires a major version of `julee`.

#### Declaration

A kit declares itself with a `Kit` manifest (a frozen kernel entity) and registers it through a Python entry point:

```toml
# julee-kits/ceap/pyproject.toml
[project.entry-points."julee.kits"]
ceap = "julee_ceap:kit"
```

```python
# julee_ceap/__init__.py
from julee.core.entities.kit import Kit

kit = Kit(
    slug="ceap",
    name="Capture, Extract, Assemble, Publish",
    package="julee_ceap",
    requires=(),
    contributes={
        "fastapi.routers": "julee_ceap.apps.api:router",
        "temporal.pipelines": "julee_ceap.apps.worker.pipelines",
        "temporal.activities": "julee_ceap.apps.worker.activities",
        "sphinx.extension": "julee_ceap.apps.sphinx",
    },
    policies=(),
)
```

- `slug` is unique among installed kits, and must not collide with a bounded context of the adopting solution.
- `package` is the import root. Doctrine discovers the kit's bounded contexts by introspecting it, so the manifest doesn't list them.
- `requires` names other kits this kit builds on. Distribution metadata must also declare them as dependencies.
- `contributes` maps a contribution point to a *dotted path*, not an imported object. The kernel therefore never imports FastAPI, Temporal or Sphinx to read a manifest. Integrations define the contribution points and resolve the paths.
- `viewpoint` (default `False`) marks a kit whose bounded contexts describe a solution rather than implement a domain. It replaces the hard-coded `VIEWPOINT_SLUGS`.
- `policies` lists any policies (ADR 005) the kit contributes, which solutions can then adopt.

#### Adoption

Installing a kit does not activate it. A solution adopts kits explicitly:

```toml
[tool.julee]
search_root = "src/my_solution"
kits = ["ceap", "viewpoints"]
```

This is explicit for the same reason `INSTALLED_APPS` is. A kit that arrives as a transitive dependency must not change a solution's behaviour, and doctrine needs to know exactly which bounded contexts are in play.

#### Composition

Kits never wire themselves in. There are no import-time side effects and no global registries. The solution's apps remain the composition roots (ADR 010) and decide what to mount:

```python
# my_solution/apps/api/app.py
from fastapi import FastAPI
from julee.integrations.fastapi import include_kit_routers

app = FastAPI()
include_kit_routers(app)  # mounts contributions from the kits in [tool.julee] kits
```

Integrations provide these helpers (`include_kit_routers`, `collect_kit_activities`, the Sphinx equivalent). A solution can always ignore them and import a kit's router or pipelines directly, as ADR 001 shows.

#### Doctrine

When doctrine runs against a solution:

1. The solution's own bounded contexts are verified in full, as today.
2. Adopted kits' bounded contexts are treated as imported. They take part in the dependency-rule and composition checks, but their internals are not re-verified, because the kit's own CI does that.
3. It is a doctrine violation to import a kit that is not listed in `[tool.julee] kits`.
4. Solution bounded contexts may import a kit's entities, use cases and protocols. Only the solution's apps (the composition roots) may import a kit's `infrastructure` or `apps` modules. This is the dependency rule applied across the kit boundary.
5. A kit slug that collides with a solution bounded context is an error.

#### Dependency direction

```
solution  →  kits  →  integrations  →  kernel
```

- Kits may depend on other kits, but only on those declared in `requires`, and without cycles.
- The julee repository enforces with import-linter that no module in `julee` imports a kit package.
- The julee-kits repository enforces that no kit imports another kit it has not declared.

### 4. The viewpoints kit

The first-party showcase application is code-outward documentation (ADR 006). It projects a solution's bounded contexts, use cases, entities, pipelines and design artefacts into Sphinx, from the code. The human-centred-design and C4 viewpoints that currently live in `julee.docs.sphinx_hcd` (and, on the archived line, in the `hcd` and `c4` bounded contexts) become one kit, `julee-viewpoints` (import package `julee_viewpoints`), declared with `viewpoint=True`.

The viewpoints kit may use only the public kit contract and public kernel and integration APIs. It is how the contract is tested: if the viewpoints kit needs something the contract doesn't offer, the contract is extended for everyone, not bypassed for one kit.

The distribution name `julee-viewpoints` is provisional.

### 5. Relationship to earlier ADRs

- **ADR 001** is superseded where it places contrib modules inside the `julee` distribution as `julee.contrib.*`, and where it calls them accelerators. Its principles about the internal structure of a module (self-contained solution, co-located tests, public API at the package root, `apps/` integration points, optional standalone `deploy/`) now apply to kits.
- **ADR 013** is superseded where it places the HCD documentation code in the framework as `julee.docs.sphinx_hcd`. Its reasoning, documentation derived from the artefacts that drive build and test outcomes and organised by HCD concepts, stands, and ADR 006 carries it forward.
- **ADR 010** is amended. Once the julee package no longer contains `contrib/`, `contrib` stops being a reserved word, and julee itself is no longer an example of a nested solution. Nested solutions remain available to solutions that want them.

## Consequences

### Positive

- `pip install julee` gives a small framework with no CEAP, AI or storage dependencies. A solution adds integrations by extra and kits by name.
- The kernel stops knowing about specific plug-ins. Viewpoints are declared, not hard-coded.
- Third parties can publish kits on equal terms with first-party ones, because first-party kits use the same contract.
- Kits release on their own schedule and with their own dependencies, so domain work no longer forces a framework release.
- The kit/kernel boundary is enforced mechanically (import-linter and doctrine), not by convention.

### Negative

- There are more distributions to version, publish and keep compatible. Every kit declares a compatible `julee` range (`julee>=X.Y,<X+1`).
- The kit contract becomes a public API that must be designed carefully and kept stable.
- Two repositories mean kernel changes that affect kits land in two places. The viewpoints kit, which lives with the kernel, catches most contract breaks before they reach julee-kits.
- Existing imports move. Solutions and the julee test suite need an import map and a deprecation period.

### Migration

Each step is a separate change and leaves `master` releasable.

1. **Split dependencies.** Move `anthropic`, `minio`, `python-magic`, `multihash`, `jsonschema` and `fastapi` out of the base dependencies, into extras or into CEAP. Stop shipping `julee/fixtures/` as package data. Rewrite the package description and keywords.
2. **Introduce `julee.integrations`.** Move the domain-free Temporal, FastAPI, MinIO and Sphinx code there from `julee.util`, `julee.core.infrastructure`, `julee.repositories.minio` and `julee.docs`, leaving deprecation re-exports behind.
3. **Gather CEAP.** Move the CEAP code in `julee.api`, `julee.repositories`, `julee.services`, `julee.util.repos` and `julee.fixtures` under `julee.contrib.ceap`, so every domain line lives under `contrib/` before anything leaves the repository.
4. **Add the kit contract.** Add the `Kit` entity, entry-point discovery, `[tool.julee] kits`, the doctrine rules in section 3, and the composition helpers in `julee.integrations`. Replace `VIEWPOINT_SLUGS` with the `viewpoint` flag. Add the import-linter contract.
5. **Create `julee-viewpoints`.** Make the julee repository a uv workspace and move the HCD and C4 documentation code into the viewpoints kit.
6. **Create `julee-kits`.** Move `ceap` and `polling` out of `julee.contrib`, one kit at a time, each with its own doctrine run in CI. Then `untp`, `supply_chain` and `onto_mapper` are ported from the archived line (ADR 011) directly into julee-kits, not into julee.
7. **Retire `julee.contrib`.** Remove the deprecation re-exports and the `contrib` reserved word in a major release.

All seven steps are done as of julee 0.3.0. The `contrib` reserved word
went with the last of them, along with `BoundedContext.is_contrib`, which
is now `is_nested`: what it always measured was whether a context was
found inside a container, not whether that container was called contrib.
