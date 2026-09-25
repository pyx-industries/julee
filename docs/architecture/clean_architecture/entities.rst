Entities
========

**Entities are domain objects.**

Entities represent core business concepts.
They contain business validation rules, domain logic, and calculations.

In Julee, entities are Pydantic models that live in the domain layer.
:doc:`Repositories <repositories>` store them;
:doc:`services` transform between them;
:doc:`use cases <use_cases>` orchestrate the
:doc:`driven ports <protocols>` that do both.

Entities are more than dumb data containers.
They are rich objects with derivative methods that validate and calculate properties.
They have both data and behavior, encapsulating business rules.

Methods Or Calculators?
-----------------------

Once an entity calculates properties,
the question arises of which calculations belong on it.

**An intrinsic rule with one right answer is a method on the entity.**
Whether a date falls inside a range, whether required fields agree,
how a total derives from its parts—the concept carries these
wherever it goes.

**A rule that varies by adopter is a**
:doc:`calculator <calculators>`.
A kit ships ``Story``; the solution that adopts it
decides what "important" means.
The entity cannot carry every adopter's version of that rule,
and should not import what it would need to.

The test is who the answer belongs to: the concept, or the solution.

CEAP Entities
-------------

The CEAP :doc:`repositories` store these entities:

- ``Document``
- ``Assembly``
- ``AssemblySpecification``
- ``KnowledgeServiceQuery``
- ``KnowledgeServiceConfig``
