ADR: Sphinx HCD Extensions Package
===================================


Status
------

Proposed


Date
----

2025-12-11


Context
-------

Julee solutions follow Clean Architecture principles for code organisation, with
bounded contexts, dependency inversion, and explicit use cases. Documentation
must harmonise with this structure while remaining accessible to non-technical
stakeholders.

Human-Centered Design (HCD) provides the common language that allows business
and engineering to communicate. Documentation organised around personas,
journeys, epics, and stories will facilitate this. We need a way to naturally
map that kind of documentation to the clean code.

Two problems emerge:

1. **Documentation bitrot**: Static documentation drifts from implementation.
   Documentation claims one thing; code does another. This must not be allowed
   to happen, it must be easire to keep them synced than not.

2. **Duplication and inconsistency**: When documentation is manually maintained,
   the same concepts get documented multiple times with subtle differences.
   Refactoring becomes risky because documentation updates are forgotten.

The solution is literate documentation (in the Donald Knuth sense): documentation
that is DRY, derives from authoritative sources, and reflects code reality. Rather
than describing what the code should do, documentation should describe what the
code does, generated from the actual artefacts.

More specifically, the ideal pattern is to:

* auto-document the code using standard sphinx tools
* inspect the "single source of truth" where possible.
  This might be the code itself, or possibly a few choice metadata files
  that are discoverable and maintainable.
* Use these "sources of truth" to maintain indexes and cross-references,
  and use manually writen documentation to elaborate with human insight. 


Decision
--------

Create a Sphinx extension package ``julee.docs.sphinx_hcd`` that:

1. **Supports both document-first and code-first entities**:
   - Document-first: Personas, journeys, epics, stories via ``define-*`` directives
   - Code-first: Applications from YAML manifests, accelerators from directory
     structure, integrations from manifest files
   - Stories can optionally link to Gherkin feature files for testability

2. **Cross-references automatically**:
   - Stories to personas, apps, epics, and journeys
   - Apps to accelerators and personas
   - Journeys to stories and epics

3. **Validates coverage**:
   - Warns about apps without documentation
   - Warns about stories referencing unknown entities
   - Warns about orphaned documentation

4. **Generates visualisations**:
   - Dependency diagrams via PlantUML
   - Journey flow diagrams
   - Integration architecture diagrams


Why HCD Organisation
~~~~~~~~~~~~~~~~~~~~

Documentation is organised by HCD concepts rather than code structure:

- **Personas**: Who uses the system
- **Journeys**: Paths through the system to achieve goals
- **Epics**: Capabilities delivered by groups of stories
- **Stories**: Individual user needs
- **Applications**: Entry points that expose features
- **Accelerators**: Bounded contexts that implement capabilities

This organisation serves multiple audiences:

- Business stakeholders navigate by persona and journey
- Product owners work with epics and stories
- Engineers trace stories to accelerators and code


Story, Feature, Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

A capability is viewed from three perspectives:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Concept
     - Perspective
     - Question Answered
   * - **Story**
     - Need
     - What does the user want to accomplish?
   * - **Feature**
     - Access
     - How does the user access this capability?
   * - **Pipeline**
     - Execution
     - How is this capability implemented?

All three ultimately implement a **UseCase** operating on **Entities**.

An **Epic** collects stories that together deliver a **Feature**. The sum of an
Epic's stories equals the Feature's scope.


Story Lifecycle
~~~~~~~~~~~~~~~

Stories progress through maturity states:

1. **Referenced** — Named in a journey or epic via ``step-story::``. The need
   is identified but not yet elaborated.

2. **Defined** — Documented with ``define-story::`` directive. The story has
   acceptance criteria and belongs to an application.

3. **Testable** — Linked to a ``.feature`` file. Acceptance tests exist.

4. **Implemented** — A pipeline satisfies the story. The capability is live.

This lifecycle supports design-first workflows: journeys can reference stories
that don't exist yet. Implementation follows design.

::

    .. define-story:: upload-scheme-documentation
       :app: staff-portal
       :persona: Knowledge Curator
       :feature-file: tests/e2e/staff-portal/features/upload.feature

       As a Knowledge Curator
       I want to upload scheme documentation
       So that I can build the vocabulary knowledge base

The ``:feature-file:`` option is optional. When present, story content can be
extracted from the Gherkin file. When absent, the story is document-first.


Document-First vs Code-First
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Entities fall into two categories based on their source of truth:

**Document-first** (defined in RST, may link to code):

- Personas — who uses the system
- Journeys — paths to achieve goals
- Epics — capability groupings
- Stories — user needs (optionally linked to Gherkin)

**Code-first** (discovered from artefacts, elaborated in RST):

- Applications — from ``app.yaml`` manifests
- Accelerators — from bounded context directories
- Integrations — from manifest files

Document-first entities use ``define-*`` directives. Code-first entities are
discovered automatically; RST provides additional context and cross-references.


Why Literate Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

By deriving documentation from artefacts that affect build and test outcomes,
documentation stays current:

- App metadata comes from ``app.yaml`` that configures applications
- Accelerators discovered from bounded context directory structure
- Stories optionally link to ``.feature`` files that drive acceptance tests
- Document-first entities use custom HCD directives for structured capture
- Cross-references are computed, not written manually

Refactoring becomes safe: rename a feature file and documentation updates
automatically. Delete an accelerator and warnings appear during doc build.


Validation
~~~~~~~~~~

The extension validates documentation completeness at build time:

**Warnings** (non-fatal):

- Story referenced in journey/epic but not defined
- Defined story without ``:feature-file:`` link (testability gap)
- Application without associated stories
- Accelerator without documentation

**Errors** (fatal):

- Story references unknown persona
- Story references unknown application
- Circular journey dependencies


Alternatives Considered
~~~~~~~~~~~~~~~~~~~~~~~

**Manual documentation with review discipline**

Rejected. Review discipline erodes over time. Documentation becomes a tax rather
than an asset. Teams stop trusting it.

**Auto-generated API documentation only**

Rejected. API docs (autodoc, autoapi) capture the "how" but miss the "why" and
"who". They don't speak business language.

**Wiki or external documentation**

Rejected. Disconnected from code, version control, and build process. Maximum
bitrot risk.

**Inline docstrings only**

Rejected. Docstrings serve developers reading code, not stakeholders navigating
by user need. Different audiences require different organisation.


Consequences
------------


Positive
~~~~~~~~

1. **Single source of truth**: Each entity has one authoritative definition
2. **Design-first workflow**: Journeys can reference stories before implementation
3. **Refactoring safety**: Rename or restructure; docs update automatically
4. **Build-time validation**: Missing documentation produces warnings
5. **Shared vocabulary**: Business and engineering speak the same HCD language
6. **Clean Architecture alignment**: Accelerators map to bounded contexts
7. **Gradual testability**: Stories can exist without Gherkin, then gain tests later


Negative
~~~~~~~~

1. **Upfront structure**: Solutions must adopt standard directory layout or
   configure overrides
2. **Learning curve**: Teams must understand the directive vocabulary
3. **Incomplete validation**: Some cross-references only validated when both
   entities are defined


Neutral
~~~~~~~

1. **Sphinx dependency**: Solutions already use Sphinx for technical docs


Package Location
----------------

``julee.docs.sphinx_hcd`` within the Julee framework, installable via PyPI.

Usage:

.. code-block:: python

    extensions = ["julee.docs.sphinx_hcd"]


References
----------

- Knuth, Donald. "Literate Programming" (1984)
- Martin, Robert C. "Clean Architecture" (2017)
- Norman, Don. "The Design of Everyday Things" (1988)
