Entities
========

**Entities are domain objects.**

Entities represent core business concepts.
They contain business validation rules, domain logic, and calculations.

In Julee, entities are Pydantic models that live in the domain layer.
:doc:`Repositories <repositories>` store them;
:doc:`services` operate on them;
:doc:`use cases <use_cases>` orchestrate both.

Entities are more than dumb data containers.
They are rich objects with derivative methods that validate and calculate properties.
They have both data and behavior, encapsulating business rules.

CEAP Entities
-------------

The CEAP :doc:`repositories` store these entities:

- ``Document``
- ``Assembly``
- ``AssemblySpecification``
- ``KnowledgeServiceQuery``
- ``KnowledgeServiceConfig``
