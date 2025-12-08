Accelerators
============

An **accelerator** is a collection of :doc:`pipelines <pipelines>` that work together to make an area of business go faster.

Julee is a framework for accountable and transparent digital supply chains. Accelerators are how solutions deliver that value - automating business processes that would otherwise be slow and manual, while maintaining the audit trails needed for compliance and due diligence.

Structure
---------

A solution screams its accelerators:

::

    solution/
      src/
        accelerator_a/
          domain/
          use_cases/
          infrastructure/
        accelerator_b/
          domain/
          use_cases/
          infrastructure/
      apps/
        api/
        cli/
        worker/

Each accelerator is a top-level package in ``src/``. The solution's architecture speaks its business language.
