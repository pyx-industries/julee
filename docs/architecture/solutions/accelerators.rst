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
          usecases/
          infrastructure/
        accelerator_b/
          domain/
          usecases/
          infrastructure/
      apps/
        api/
        cli/
        worker/

Each accelerator is a top-level package in ``src/``. The solution's architecture speaks its business language.

``apps/`` is optional
---------------------

The layout above is the common shape, not the required one. A solution
may have no ``apps/`` at all.

An observability stack is the worked example: Loki, Prometheus, Grafana,
an OTel collector, an OIDC identity provider and an SMTP relay, composed
by a deployment, with bounded contexts modelling log, metric and trace
identity, retention and ingestion contracts. It has a domain and no
deployable application of its own, and it is a solution.

What a solution needs is somewhere that composes it — where the concrete
repositories and services are chosen and wired. ``apps/`` is where that
usually sits, and it is the default, but it is named rather than assumed:

.. code-block:: toml

    [tool.julee]
    composition_roots = ["sphinx_hcd/sphinx", "sphinx_c4/sphinx"]

That is ``julee-viewpoints``, which is composed by a Sphinx extension.
A solution whose composition is a ``deployments/`` directory of compose
files says so the same way.

Doctrine reads ``composition_roots`` to decide who may reach into a
kit's ``infrastructure/``, so this is not decoration: it is how the
dependency rule knows a composition root from a bounded context
reaching where it should not.
