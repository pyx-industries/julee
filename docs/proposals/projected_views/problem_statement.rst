Problem Statement
=================

.. contents:: Contents
   :local:
   :depth: 2

The Core Problem
----------------

Julee's viewpoint accelerators (HCD, C4) have **inconsistent and incompatible
approaches** to binding their ontologies to code structure. This creates:

1. Duplicated introspection logic
2. Inconsistent user experience
3. Barriers to adding new viewpoints (e.g., UML)
4. Inability to project views onto arbitrary codebases

Current State Analysis
----------------------

HCD: Implicit Binding via Convention
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

HCD discovers code structure through:

- **Directory convention**: ``domain/models/``, ``domain/use_cases/``, etc.
- **AST parsing**: Extracts ``ClassInfo``, ``FunctionInfo`` from Python files
- **Docstring extraction**: ``__init__.py`` docstrings become objectives
- **Slug matching**: Accelerator slug must match directory name in ``src/``

**Strengths**:

- Automatic discovery—less manual declaration
- Stays synchronized with code changes
- Rich introspection of code structure

**Weaknesses**:

- Binding rules are implicit (buried in ``ast.py``)
- Coupled to HCD—other viewpoints can't reuse it
- Assumes specific directory structure without explicit doctrine

C4: Fully Manual Declaration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

C4 requires explicit declaration via RST directives:

- ``.. define-software-system::``
- ``.. define-container::``
- ``.. define-component::``

**Strengths**:

- Full control over architectural representation
- Not coupled to code structure
- Can describe systems that don't exist as code

**Weaknesses**:

- No code awareness—can't auto-discover components
- Drifts from reality as code changes
- Duplicates information already present in code
- Users must manually maintain synchronization

The Bridge Gap
~~~~~~~~~~~~~~

A thin bridge exists (``c4_bridge.py``) that maps HCD concepts to C4 diagrams:

- **Unidirectional**: HCD → C4 only
- **Limited scope**: Only handles Apps and Accelerators
- **Coupling**: HCD models carry C4-specific fields (``interface``, ``technology``)

This bridge is a symptom of the problem, not a solution. It creates tight
coupling between viewpoints that should be independent.

Specific Inconsistencies
------------------------

+-------------------+----------------------------------+----------------------------------+
| Aspect            | HCD                              | C4                               |
+===================+==================================+==================================+
| Code Binding      | Implicit via directory + AST     | None—fully manual                |
+-------------------+----------------------------------+----------------------------------+
| Discovery         | Auto-scans ``src/``              | User declares everything         |
+-------------------+----------------------------------+----------------------------------+
| Metadata Source   | Docstrings, class names          | Directive options only           |
+-------------------+----------------------------------+----------------------------------+
| Identity          | Slug must match directory        | Independent slugs                |
+-------------------+----------------------------------+----------------------------------+
| Repository Queries| Code-aware (``has_entities``)    | Metadata-only (``by_owner``)     |
+-------------------+----------------------------------+----------------------------------+

Why This Matters
----------------

Adding a UML Viewpoint
~~~~~~~~~~~~~~~~~~~~~~

If we want to add UML as a viewpoint accelerator, we face a choice:

1. **Copy HCD's approach**: Duplicate AST parsing logic, create UML-specific
   introspection, resulting in three independent code analyzers.

2. **Copy C4's approach**: Require manual UML declarations, losing the benefit
   of automatic discovery.

3. **Build on HCD**: Make UML depend on HCD's introspection, creating an
   inappropriate coupling between viewpoints.

None of these options is satisfactory.

Julee Solutions
~~~~~~~~~~~~~~~

When a Julee solution creates its own accelerators for its bounded contexts,
it should be able to:

1. Follow a documented doctrine (coding conventions)
2. Get HCD, C4, UML views automatically by virtue of following the doctrine
3. Not know or care about the internal details of each viewpoint

Currently, this is impossible because:

- There's no explicit doctrine to follow
- C4 requires manual declaration regardless of code structure
- HCD's introspection is coupled to HCD concepts

Framework Self-Description
~~~~~~~~~~~~~~~~~~~~~~~~~~

Julee should describe itself using its own viewpoints. But:

- HCD views of Julee require HCD-specific setup
- C4 views of Julee require manual C4 declarations
- There's no unified way to say "show me Julee from perspective X"

The Root Cause
--------------

The fundamental issue is **misplaced responsibility**:

- **Introspection** (understanding code structure) is owned by HCD
- **Doctrine** (rules for code structure) is implicit, not modeled
- **Viewpoints** are conflated with code binding

The solution requires separating these concerns:

1. **Doctrine**: Explicit rules for how code should be structured
2. **Introspection**: Analysis of code against the doctrine
3. **Viewpoints**: Projections of introspected code into domain-specific views

These should be three separate concerns, with viewpoints depending on
introspection, and introspection depending on doctrine.
