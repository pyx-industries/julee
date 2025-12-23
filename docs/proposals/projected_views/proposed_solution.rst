Proposed Solution: The Code Accelerator
=======================================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

Introduce a new bounded context—``julee.code``—that owns both the **doctrine**
(rules for how code should be structured) and **introspection** (analysis of
code against that doctrine).

All viewpoint accelerators (HCD, C4, UML, future viewpoints) depend on
``julee.code`` and define **projection rules** that map introspected code
concepts to their domain-specific views.

The Code Accelerator
--------------------

Responsibilities
~~~~~~~~~~~~~~~~

1. **Model the doctrine**: Explicit domain models for coding conventions,
   architectural layers, tactical patterns, and structure rules.

2. **Provide introspection**: Services and use cases for analyzing code
   against the doctrine.

3. **Expose repositories**: Access to introspected code models for
   viewpoint accelerators to consume.

Proposed Structure
~~~~~~~~~~~~~~~~~~

::

    src/julee/code/
    ├── domain/
    │   ├── models/
    │   │   ├── bounded_context.py      # What a bounded context IS
    │   │   ├── architectural_layer.py  # Domain, Application, Infrastructure
    │   │   ├── tactical_patterns.py    # Entity, ValueObject, Aggregate, UseCase
    │   │   ├── code_structure.py       # Module, Class, Function, Property
    │   │   └── doctrine.py             # Rules: LayerRule, LocationRule, etc.
    │   │
    │   ├── services/
    │   │   └── introspection.py        # Protocol for analyzing code
    │   │
    │   └── repositories/
    │       ├── bounded_context_repo.py
    │       └── doctrine_repo.py
    │
    ├── application/
    │   └── use_cases/
    │       ├── analyze_bounded_context.py
    │       └── validate_doctrine_compliance.py
    │
    └── infrastructure/
        └── parsers/
            └── python_ast.py           # Python-specific introspection

Domain Models
~~~~~~~~~~~~~

**Bounded Context** (what exists in code)::

    class BoundedContext:
        name: str
        slug: str
        objective: str | None           # From __init__.py docstring
        domain_layer: DomainLayer
        application_layer: ApplicationLayer | None
        infrastructure_layer: InfrastructureLayer | None

    class DomainLayer:
        entities: list[Entity]
        value_objects: list[ValueObject]
        aggregates: list[Aggregate]
        use_cases: list[UseCase]
        repository_protocols: list[RepositoryProtocol]
        service_protocols: list[ServiceProtocol]

**Doctrine** (the rules)::

    class Doctrine:
        layer_rules: list[LayerRule]
        location_rules: list[LocationRule]
        structure_rules: list[StructureRule]
        naming_rules: list[NamingRule]

    class LayerRule:
        """Which layers exist and dependency constraints."""
        layers: list[Layer]
        allowed_dependencies: dict[Layer, set[Layer]]

    class LocationRule:
        """Where code artifacts must live."""
        pattern: str              # e.g., "domain/use_cases/*.py"
        artifact_type: str        # e.g., "UseCase"

    class StructureRule:
        """How code artifacts must be structured."""
        artifact_type: str
        must_inherit: str | None
        required_attributes: list[str]

Relationship to ADRs
~~~~~~~~~~~~~~~~~~~~

ADRs (Architectural Decision Records) remain as documentation explaining
*why* the doctrine exists. The doctrine models are the *executable
implementation* of those decisions::

    ADR-001: Clean Architecture
        │
        │ "We decided to use clean architecture because..."
        │
        ▼ implements
    Doctrine (in julee.code)
        │
        │ LayerRule(layers=[domain, application, infrastructure])
        │ LocationRule(pattern="domain/models/*", artifact_type="Entity")
        │
        ▼ enforced by
    Introspection + Tests + Reviews

Viewpoint Projections
---------------------

The Projection Mechanism
~~~~~~~~~~~~~~~~~~~~~~~~

Each viewpoint accelerator defines **projection rules** that map
``julee.code`` concepts to its domain::

    # Hypothetical: julee.hcd projection
    class HCDProjection:
        rules = [
            ProjectionRule(
                source=UseCase,           # From julee.code
                target=Story,             # HCD concept
                transform=lambda uc: Story(
                    title=uc.name,
                    description=uc.docstring,
                )
            ),
            ProjectionRule(
                source=BoundedContext,
                target=App,
                transform=lambda bc: App(
                    name=bc.name,
                    description=bc.objective,
                )
            ),
        ]

    # Hypothetical: julee.c4 projection
    class C4Projection:
        rules = [
            ProjectionRule(
                source=BoundedContext,
                target=Container,
                transform=lambda bc: Container(
                    name=bc.name,
                    description=bc.objective,
                    technology="Python",
                )
            ),
            ProjectionRule(
                source=Entity,
                target=Component,
                transform=lambda e: Component(
                    name=e.name,
                    description=e.docstring,
                )
            ),
        ]

What This Enables
~~~~~~~~~~~~~~~~~

1. **Consistent binding**: All viewpoints use the same introspection layer.
   No more duplicated AST parsing.

2. **Explicit projection rules**: Clear, auditable mapping from code to views.
   No more implicit conventions buried in implementation.

3. **Automatic synchronization**: Views update when code changes because
   they're projections, not copies.

4. **New viewpoints are easy**: Adding UML just means defining UML projection
   rules. No new introspection logic needed.

5. **Solution independence**: Julee solutions only need to follow the doctrine.
   They get all viewpoints for free.

The Flow
--------

::

    ┌─────────────────────────────────────────────────────────────┐
    │                     Code (Python files)                      │
    └─────────────────────────────────────────────────────────────┘
                                  │
                                  │ parsed by
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                     julee.code                               │
    │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
    │  │  Doctrine   │    │Introspection│    │  Code Models    │  │
    │  │  (rules)    │───▶│  (parsing)  │───▶│(BoundedContext) │  │
    │  └─────────────┘    └─────────────┘    └─────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
                                  │
                                  │ consumed by
                   ┌──────────────┼──────────────┐
                   ▼              ▼              ▼
    ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
    │   julee.hcd    │ │   julee.c4     │ │   julee.uml    │
    │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │
    │  │Projection│  │ │  │Projection│  │ │  │Projection│  │
    │  │  Rules   │  │ │  │  Rules   │  │ │  │  Rules   │  │
    │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │
    │       │        │ │       │        │ │       │        │
    │       ▼        │ │       ▼        │ │       ▼        │
    │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │
    │  │   HCD    │  │ │  │    C4    │  │ │  │   UML    │  │
    │  │  Views   │  │ │  │  Views   │  │ │  │  Views   │  │
    │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │
    └────────────────┘ └────────────────┘ └────────────────┘

Benefits
--------

For Framework Development
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Single source of truth**: Code structure is introspected once
- **Consistent tooling**: All viewpoints use the same foundation
- **Easier maintenance**: Changes to doctrine propagate to all viewpoints
- **Self-documentation**: Framework describes itself through its own viewpoints

For Julee Solutions
~~~~~~~~~~~~~~~~~~~

- **Clear contract**: Follow the doctrine, get viewpoints for free
- **No viewpoint coupling**: Solutions don't know about HCD, C4, or UML
- **Automatic views**: Documentation generates from code structure
- **Compliance validation**: Check doctrine conformance programmatically

For Future Viewpoints
~~~~~~~~~~~~~~~~~~~~~

- **Low barrier**: Just define projection rules
- **No introspection work**: Reuse existing code analysis
- **Composable**: Viewpoints can reference each other's projections
