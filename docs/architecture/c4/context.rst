System Context
==============

Julee Tooling supports the development of :doc:`solutions <../framework>`.
This page shows who uses the tooling and what external systems it interacts with.

.. define-software-system:: julee-tooling
   :name: Julee Tooling
   :type: internal
   :hidden:

   Accelerators and applications for developing solutions

.. define-software-system:: julee-solution
   :name: Julee Solution
   :type: external
   :hidden:

   The solution being developed - code, docs, config

.. define-relationship::
   :from: person:solutions-developer
   :to: system:julee-tooling
   :description: Uses
   :hidden:

.. define-relationship::
   :from: person:framework-contributor
   :to: system:julee-tooling
   :description: Extends
   :hidden:

.. define-relationship::
   :from: person:documentation-author
   :to: system:julee-tooling
   :description: Documents with
   :hidden:

.. define-relationship::
   :from: system:julee-tooling
   :to: system:julee-solution
   :description: Reads/writes artifacts
   :hidden:

.. persona-index::
   :format: summary

The :doc:`Julee Solution <../framework>` being developed is the external system.
The tooling reads and writes solution artifacts:

- RST documentation files
- Code structure and patterns
- Configuration and manifests

.. system-context-diagram:: julee-tooling
   :title: System Context - Julee Tooling
