Projected Views: A Common Introspection Layer for Julee
=======================================================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

This proposal describes an architectural evolution for Julee's viewpoint
accelerators (HCD, C4, and potentially UML). The core insight is that
**viewpoints should project onto code structure**, not define it.

Currently, HCD and C4 have inconsistent approaches to code binding:

- **HCD** implicitly discovers code structure via AST parsing and directory conventions
- **C4** requires fully manual declaration with no code awareness

This proposal introduces a **code accelerator** that owns both:

1. **Doctrine**: The rules for how code should be structured (implementing ADRs)
2. **Introspection**: The capability to analyze code against that doctrine

All viewpoint accelerators (HCD, C4, UML, and future ones) would depend on
the code accelerator, enabling them to project their views onto any codebase
that follows the doctrine—including Julee itself.

Documents in This Proposal
--------------------------

.. toctree::
   :maxdepth: 1

   problem_statement
   proposed_solution
   uml_ontology
   refactoring_plan

Key Principles
--------------

1. **Accelerators are parallel ontologies**: Each defines its own bounded context
   with its own domain language. Solutions create their own accelerators for
   their own domains.

2. **Viewpoints are cross-cutting lenses**: C4, HCD, UML are analytical
   perspectives that can be applied to any accelerator's domain, not foundations
   that other accelerators inherit from.

3. **Doctrine and introspection are coupled**: The rules for creating code
   and the rules for interpreting code are two sides of the same coin.
   They must be owned by the same bounded context.

4. **ADRs justify doctrine**: Architectural Decision Records explain *why*
   the doctrine exists. The doctrine in ``julee.code`` is the executable
   implementation of those decisions.

5. **Reflexive self-description**: The framework uses its own viewpoints
   to describe itself, enabling documentation that stays synchronized with
   the codebase.

Dependency Tree
---------------

The proposed dependency structure::

                    julee.code
                    (doctrine + introspection)
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
       julee.hcd       julee.c4       julee.uml
       (viewpoint)     (viewpoint)    (viewpoint)
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    julee.{framework}
                    (composed accelerators)
                           │
                           ▼
                    julee solutions
                    (customer applications)

Status
------

**Proposal** - Under discussion, not yet approved for implementation.
