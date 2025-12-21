Containers
==========

Julee Tooling consists of applications that expose accelerators for developing
solutions. Each accelerator is a bounded context with domain models, repositories,
and use cases.

Applications
------------

Applications provide access to the accelerators through different interfaces.

**Sphinx Extensions** - generate documentation at build time:

- ``sphinx_hcd`` - HCD directives (personas, journeys, stories, epics, apps)
- ``sphinx_c4`` - C4 directives (systems, containers, components, relationships)

**REST APIs** - programmatic access:

- ``hcd_api`` - CRUD operations for HCD entities
- ``c4_api`` - CRUD operations for C4 entities

**MCP Servers** - AI assistant access:

- ``hcd_mcp`` - MCP protocol for HCD queries and mutations
- ``c4_mcp`` - MCP protocol for C4 queries and mutations

Accelerators
------------

Each accelerator is a bounded context for conceptualising solutions.

**HCD Accelerator** - human-centered design:

- Personas - types of users
- Journeys - user goals and flows
- Stories - specific interactions (Gherkin)
- Epics - groups of related stories
- Applications - entry points users interact with

**C4 Accelerator** - software architecture:

- Software Systems - top-level system boundaries
- Containers - deployable units
- Components - modules within containers
- Relationships - dependencies and interactions

Foundation
----------

Both accelerators are built on clean architecture idioms:

- Domain models (Pydantic entities)
- Repository protocols (abstract persistence)
- Use cases (application business rules)
- Memory and file-based repository implementations

Container Diagram
-----------------

.. uml::

   @startuml
   !include <C4/C4_Container>

   title Container Diagram - Julee Tooling

   Person(user, "User", "Any persona using the tooling")

   System_Boundary(tooling, "Julee Tooling") {

      Container_Boundary(apps, "Applications") {
         Container(sphinx_hcd, "sphinx_hcd", "Python/Sphinx", "HCD documentation directives")
         Container(sphinx_c4, "sphinx_c4", "Python/Sphinx", "C4 documentation directives")
         Container(hcd_api, "hcd_api", "FastAPI", "HCD REST API")
         Container(c4_api, "c4_api", "FastAPI", "C4 REST API")
         Container(hcd_mcp, "hcd_mcp", "MCP", "HCD AI assistant access")
         Container(c4_mcp, "c4_mcp", "MCP", "C4 AI assistant access")
      }

      Container_Boundary(accelerators, "Accelerators") {
         Container(hcd, "HCD Accelerator", "Python", "Personas, journeys, stories, epics, apps")
         Container(c4, "C4 Accelerator", "Python", "Systems, containers, components, relationships")
      }

      Container(foundation, "Foundation", "Python", "Clean architecture idioms and utilities")
   }

   System_Ext(solution, "Julee Solution", "Code, docs, config")

   Rel(user, sphinx_hcd, "Writes RST")
   Rel(user, sphinx_c4, "Writes RST")
   Rel(user, hcd_api, "HTTP")
   Rel(user, c4_api, "HTTP")
   Rel(user, hcd_mcp, "MCP")
   Rel(user, c4_mcp, "MCP")

   Rel(sphinx_hcd, hcd, "Uses")
   Rel(sphinx_c4, c4, "Uses")
   Rel(hcd_api, hcd, "Uses")
   Rel(c4_api, c4, "Uses")
   Rel(hcd_mcp, hcd, "Uses")
   Rel(c4_mcp, c4, "Uses")

   Rel(hcd, foundation, "Built on")
   Rel(c4, foundation, "Built on")

   Rel(hcd, solution, "Reads/writes")
   Rel(c4, solution, "Reads/writes")

   @enduml
