System Context
==============

Julee Tooling supports the development of :doc:`solutions <../framework>`.
This page shows who uses the tooling and what external systems it interacts with.

Users
-----

.. persona-index::

External System
---------------

The :doc:`Julee Solution <../framework>` being developed is the external system.
The tooling reads and writes solution artifacts:

- RST documentation files
- Code structure and patterns
- Configuration and manifests

System Context Diagram
----------------------

.. uml::

   @startuml
   !include <C4/C4_Context>

   title System Context - Julee Tooling

   Person(dev, "Solutions Developer", "Builds workflow solutions using Julee patterns")
   Person(contrib, "Framework Contributor", "Extends accelerators and applications")
   Person(author, "Documentation Author", "Creates documentation using accelerators")

   System(tooling, "Julee Tooling", "Accelerators and applications for developing solutions")

   System_Ext(solution, "Julee Solution", "The solution being developed - code, docs, config")

   Rel(dev, tooling, "Uses")
   Rel(contrib, tooling, "Extends")
   Rel(author, tooling, "Documents with")

   Rel(tooling, solution, "Reads/writes artifacts")

   @enduml
