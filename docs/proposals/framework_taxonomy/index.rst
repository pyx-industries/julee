Framework Taxonomy: Structure and Conventions
=============================================

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

This proposal defines the structural taxonomy of the Julee framework—the
reserved words, directory conventions, and dependency rules that give the
framework its shape.

The core insight is that **the framework is self-hosting**: Julee has the
exact same structure as solutions built on it. The framework defines the
idioms and provides reusable viewpoints and contrib modules, while solutions
import these and add their own accelerators.

Key Principles
--------------

1. **Core idioms are the foundation**: Everything hangs on the Clean
   Architecture patterns defined in ``core/``—immutable entities, abstract
   repositories, use case classes, layered infrastructure. Viewpoints are
   ontologically bound to these idioms; contrib and solutions depend on them.

2. **Accelerators scream**: Bounded contexts live at the top level of a
   codebase, not nested under a parent directory. When you open a solution,
   you immediately see what domains it contains.

3. **Reserved words have structural meaning**: Certain directory names
   (``core/``, ``contrib/``, ``applications/``, ``docs/``, ``deployment/``)
   are reserved and cannot be used as accelerator names.

4. **Dependencies point parentward**: Within an accelerator, inner layers
   (entities) know nothing of outer layers (infrastructure). Imports trend
   toward ``../`` (parent), not ``./subdir/`` (child).

5. **Convention over configuration**: Following the idioms gives you sensible
   defaults. A naive implementation should work out of the box.

6. **Viewpoints are universal**: HCD and C4 viewpoints can be applied to any
   solution that follows the core idioms. They are lenses, not dependencies.

7. **Contrib is opt-in**: Contrib modules (CEAP, polling, etc.) are
   batteries-included utilities that solutions explicitly choose to use.

Documents in This Proposal
--------------------------

.. toctree::
   :maxdepth: 1

   core_idioms
   accelerator_idioms
   application_idioms
   reserved_words
   dependency_layers
   self_hosting

The reading order matters: **core_idioms** defines the foundation that
everything else builds on. Start there.

Top-Level Structure
-------------------

The framework and all solutions share this shape::

    {solution}/
      {accelerator}/          # Bounded context (screaming)
      {accelerator}/          # Another bounded context
      applications/           # Exposure layer (reserved)
      docs/                   # Viewpoint projections (reserved)
      deployment/             # Runtime configuration (reserved)

The framework additionally has::

    julee/
      core/                   # The idioms themselves (reserved)
      hcd/                    # Viewpoint accelerator
      c4/                     # Viewpoint accelerator
      contrib/                # Optional modules (reserved)
        ceap/
        polling/
      applications/
      docs/
      deployment/

Dependency Graph
----------------

::

              ┌─────────────┐     ┌──────┐
              │ deployment/ │     │docs/ │
              └──────┬──────┘     └──┬───┘
                     │               │
                     └───────┬───────┘
                             ▼
                    ┌──────────────┐
                    │applications/ │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      ┌──────┐        ┌──────┐       ┌──────────┐
      │ hcd/ │        │ c4/  │       │ contrib/ │
      └──┬───┘        └──┬───┘       └────┬─────┘
         │               │                │
         └───────────────┼────────────────┘
                         ▼
                    ┌─────────┐
                    │  core/  │
                    └─────────┘

Import Path Examples
--------------------

The import paths communicate intent:

.. code-block:: python

    # Viewpoints - universal lenses for any solution
    from julee.hcd.entities import Story, Persona, Journey
    from julee.c4.entities import Container, Component

    # Contrib - opt-in batteries-included modules
    from julee.contrib.ceap.entities import Document, Assembly
    from julee.contrib.polling import Workflow

    # Core - the idioms everything is built on
    from julee.core.entities import BaseEntity
    from julee.core.repositories import BaseRepository

A newcomer seeing ``julee.contrib.ceap`` knows: "this is an official add-on
I'm choosing to use." Seeing ``julee.hcd`` says: "this is a fundamental way
of understanding julee solutions."

Status
------

**Proposal** - Under discussion, not yet approved for implementation.
