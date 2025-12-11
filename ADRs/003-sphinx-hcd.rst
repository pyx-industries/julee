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

1. **Extracts documentation from code artefacts**:
   - User stories from Gherkin feature files (acceptance tests)
   - Application metadata from YAML manifests
   - Accelerator structure from bounded context directories
   - Integration dependencies from manifest files

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
- **Stories**: Individual user needs (from Gherkin features)
- **Applications**: Entry points that expose features
- **Accelerators**: Bounded contexts that implement capabilities

This organisation serves multiple audiences:

- Business stakeholders navigate by persona and journey
- Product owners work with epics and stories
- Engineers trace stories to accelerators and code


Why Literate Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

By deriving documentation from artefacts that affect build and test outcomes,
documentation stays current:

- Stories come from ``.feature`` files that drive acceptance tests
- App metadata comes from ``app.yaml`` that configures applications
- use custom HCD directives for capturing structured data re: document-first entities,
  (i.e. entities that are not directly expressed or discoverable from the code).
- Cross-references are computed, not written manually or maintained.

Refactoring becomes safe: rename a feature file and documentation updates
automatically. Delete an accelerator and warnings appear during doc build.


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

1. **Single source of truth**: Documentation derives from test files and manifests
2. **Refactoring safety**: Rename or restructure; docs update automatically
3. **Build-time validation**: Missing documentation produces warnings
4. **Shared vocabulary**: Business and engineering speak the same HCD language
5. **Clean Architecture alignment**: Accelerators map to bounded contexts


Negative
~~~~~~~~

1. **Upfront structure**: Solutions must adopt standard directory layout or
   configure overrides
2. **Learning curve**: Teams must understand the directive vocabulary


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
