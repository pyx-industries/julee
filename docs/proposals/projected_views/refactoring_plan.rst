Refactoring Plan: HCD + C4 → HCD, C4, and Code
==============================================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

This document outlines how to refactor the existing HCD and C4 accelerators
to extract a common ``julee.code`` accelerator, enabling both (and future
viewpoints) to project views onto any codebase that follows the coding
doctrine.

Goals
-----

1. **Extract introspection**: Move AST parsing and code analysis from HCD
   to a new ``julee.code`` accelerator.

2. **Explicit doctrine**: Model coding conventions as domain objects in
   ``julee.code``, implementing ADRs.

3. **Consistent viewpoints**: Both HCD and C4 consume ``julee.code`` and
   define projection rules.

4. **Enable UML**: Create a foundation that makes adding UML (or other
   viewpoints) straightforward.

5. **Solution independence**: Julee solutions follow doctrine without
   knowing about specific viewpoints.

Current State
-------------

What Exists Where
~~~~~~~~~~~~~~~~~

**In julee.hcd**:

- ``domain/models/code_info.py`` — ``BoundedContextInfo``, ``ClassInfo``, etc.
- ``parsers/ast.py`` — ``parse_bounded_context()`` AST analysis
- ``domain/repositories/code_info_repo.py`` — Repository for code info

**In julee.c4**:

- No code introspection
- Manual declaration via RST directives
- Independent identity (slugs not linked to code)

**Bridge**:

- ``apps/sphinx/hcd/directives/c4_bridge.py`` — HCD → C4 mapping

Phase 1: Create julee.code
--------------------------

Step 1.1: Scaffold the Accelerator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create the basic structure::

    src/julee/code/
    ├── __init__.py
    ├── domain/
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── bounded_context.py
    │   │   ├── code_structure.py
    │   │   └── doctrine.py
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   └── bounded_context_repo.py
    │   └── services/
    │       ├── __init__.py
    │       └── introspection.py
    ├── application/
    │   └── use_cases/
    │       ├── __init__.py
    │       └── analyze_bounded_context.py
    └── infrastructure/
        └── parsers/
            ├── __init__.py
            └── python_ast.py

Step 1.2: Define Core Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**bounded_context.py**::

    from pydantic import BaseModel

    class BoundedContext(BaseModel):
        """A bounded context discovered in the codebase."""
        name: str
        slug: str
        path: Path
        objective: str | None
        domain_layer: DomainLayer | None
        application_layer: ApplicationLayer | None
        infrastructure_layer: InfrastructureLayer | None

    class DomainLayer(BaseModel):
        entities: list[Entity]
        value_objects: list[ValueObject]
        use_cases: list[UseCase]
        repository_protocols: list[Protocol]
        service_protocols: list[Protocol]

**code_structure.py**::

    class CodeElement(BaseModel):
        """Base for all code elements."""
        name: str
        qualified_name: str
        docstring: str | None
        source_location: SourceLocation

    class Entity(CodeElement):
        properties: list[Property]
        methods: list[Method]

    class UseCase(CodeElement):
        request_type: str | None
        response_type: str | None
        methods: list[Method]

**doctrine.py**::

    class Doctrine(BaseModel):
        """Coding doctrine implementing ADRs."""
        layer_rules: list[LayerRule]
        location_rules: list[LocationRule]
        structure_rules: list[StructureRule]

    class LayerRule(BaseModel):
        layer: str
        path_pattern: str
        allowed_dependencies: list[str]

    class LocationRule(BaseModel):
        artifact_type: str
        path_pattern: str

Step 1.3: Move Introspection Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Move from ``julee.hcd.parsers.ast`` to ``julee.code.infrastructure.parsers``::

    # julee/code/infrastructure/parsers/python_ast.py

    def parse_bounded_context(path: Path, doctrine: Doctrine) -> BoundedContext:
        """
        Parse a bounded context directory according to doctrine rules.

        Args:
            path: Path to bounded context directory
            doctrine: Doctrine rules for interpretation

        Returns:
            BoundedContext model with discovered elements
        """
        # Existing logic from julee.hcd.parsers.ast
        # But parameterized by doctrine rules
        ...

Phase 2: Refactor HCD
---------------------

Step 2.1: Add Dependency on julee.code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Update imports and remove duplicated models::

    # julee/hcd/domain/models/__init__.py

    # Remove: BoundedContextInfo, ClassInfo (moved to julee.code)
    # Keep: Story, Journey, Persona, Epic, App, Accelerator (HCD concepts)

Step 2.2: Define HCD Projection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create explicit projection rules::

    # julee/hcd/domain/projections.py

    from julee.code.domain.models import BoundedContext, UseCase, Entity
    from julee.hcd.domain.models import Story, App

    class HCDProjection:
        """Rules for projecting code onto HCD concepts."""

        @staticmethod
        def bounded_context_to_app(bc: BoundedContext) -> App:
            return App(
                name=bc.name,
                slug=bc.slug,
                description=bc.objective,
                # ... other mappings
            )

        @staticmethod
        def use_case_to_story_candidate(uc: UseCase) -> StoryCandidate:
            return StoryCandidate(
                title=uc.name,
                description=uc.docstring,
                source=uc.source_location,
            )

Step 2.3: Update Repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HCD repositories no longer own code introspection::

    # julee/hcd/domain/repositories/app_repo.py

    class AppRepository(BaseRepository[App]):
        # Remove: code-specific queries
        # Keep: HCD-specific queries (by_persona, by_journey, etc.)
        ...

Phase 3: Refactor C4
--------------------

Step 3.1: Add Dependency on julee.code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

C4 gains code awareness::

    # julee/c4/__init__.py

    from julee.code.domain.models import BoundedContext
    # C4 can now discover containers from bounded contexts

Step 3.2: Define C4 Projection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # julee/c4/domain/projections.py

    from julee.code.domain.models import BoundedContext, Entity
    from julee.c4.domain.models import Container, Component

    class C4Projection:
        """Rules for projecting code onto C4 concepts."""

        @staticmethod
        def bounded_context_to_container(
            bc: BoundedContext,
            technology: str = "Python",
        ) -> Container:
            return Container(
                name=bc.name,
                description=bc.objective,
                technology=technology,
            )

        @staticmethod
        def entity_to_component(entity: Entity) -> Component:
            return Component(
                name=entity.name,
                description=entity.docstring,
                technology="Pydantic Model",
            )

Step 3.3: Enable Auto-Discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

C4 can now auto-discover from code while still allowing manual override::

    # In Sphinx directive handling

    def get_containers(self) -> list[Container]:
        # First: auto-discover from code
        code_repo = self.context.code_repo
        auto_containers = [
            C4Projection.bounded_context_to_container(bc)
            for bc in code_repo.get_all()
        ]

        # Then: merge with manually declared containers
        manual_containers = self.context.container_repo.get_all()

        # Manual declarations override auto-discovered
        return merge_by_slug(auto_containers, manual_containers)

Phase 4: Remove Bridge
----------------------

The ``c4_bridge.py`` becomes unnecessary because:

1. Both HCD and C4 consume the same ``julee.code`` foundation
2. Projections are explicit in each viewpoint
3. No direct HCD → C4 coupling needed

The bridge can be removed or simplified to a thin coordination layer.

Phase 5: Enable UML Viewpoint
-----------------------------

With the foundation in place, adding UML is straightforward::

    src/julee/uml/
    ├── domain/
    │   ├── models/
    │   │   ├── classifier.py      # Class, Interface, etc.
    │   │   ├── relationship.py    # Association, Generalization, etc.
    │   │   └── diagram.py         # ClassDiagram, SequenceDiagram, etc.
    │   ├── projections.py         # Code → UML rules
    │   └── repositories/
    └── infrastructure/
        └── serializers/
            ├── plantuml.py
            └── mermaid.py

The projection rules map ``julee.code`` concepts to UML::

    class UMLProjection:
        @staticmethod
        def entity_to_class(entity: Entity) -> UMLClass:
            return UMLClass(
                name=entity.name,
                stereotype="entity",
                attributes=[
                    UMLAttribute(p.name, p.type_annotation)
                    for p in entity.properties
                ],
                operations=[
                    UMLOperation(m.name, m.parameters, m.return_type)
                    for m in entity.methods
                ],
            )

Migration Strategy
------------------

Incremental Approach
~~~~~~~~~~~~~~~~~~~~

1. **Create julee.code** alongside existing code (no breakage)
2. **Dual-source HCD** temporarily reads from both old and new
3. **Validate equivalence** ensure new introspection matches old
4. **Switch HCD** to consume only julee.code
5. **Add C4 projection** enable auto-discovery
6. **Remove old code** delete duplicated models and parsers
7. **Add UML** new viewpoint using the foundation

Backwards Compatibility
~~~~~~~~~~~~~~~~~~~~~~~

- Existing RST directives continue to work
- Manual C4 declarations still supported
- HCD concepts unchanged (Story, Persona, etc.)
- Only internal structure changes

Testing Strategy
~~~~~~~~~~~~~~~~

1. **Unit tests for julee.code** doctrine validation, introspection
2. **Projection tests** verify correct mapping from code to views
3. **Integration tests** Sphinx builds produce same output
4. **Self-description test** julee describes itself correctly

Success Criteria
----------------

The refactoring is complete when:

1. ``julee.code`` owns all introspection logic
2. HCD and C4 depend on ``julee.code``, not each other
3. Both viewpoints define explicit projection rules
4. C4 auto-discovers from code (with manual override)
5. Adding a new viewpoint requires only projection rules
6. Julee documents itself through all viewpoints
7. Julee solutions get viewpoints by following doctrine

Open Questions
--------------

1. **Doctrine source**: Should doctrine be loaded from a config file,
   or hardcoded based on ADRs?

2. **Projection customization**: Can solutions customize projection rules,
   or are they fixed by the framework?

3. **Cross-viewpoint references**: Can an HCD Story link to a UML diagram
   of its implementing use case?

4. **Incremental introspection**: How do we handle partial rebuilds when
   only some files change?

5. **Non-Python code**: How do we handle bounded contexts with non-Python
   components (TypeScript frontends, etc.)?
