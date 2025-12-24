Reserved Words
==============

.. contents:: Contents
   :local:
   :depth: 2

Overview
--------

Certain directory names at the top level of a julee solution have structural
meaning and cannot be used as accelerator (bounded context) names. These
reserved words form the framework's "syntax," while accelerators provide the
solution's "vocabulary."

Reserved Directory Names
------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Name
     - Scope
     - Purpose
   * - ``core/``
     - Framework only
     - The idioms that make something a julee solution. Solutions import
       from ``julee.core``, they don't define their own.
   * - ``contrib/``
     - Framework only
     - Optional batteries-included modules. Solutions import from
       ``julee.contrib.*``, they don't define their own contrib.
   * - ``applications/``
     - Framework and solutions
     - Exposure layer: APIs, MCP servers, Sphinx extensions, workers.
   * - ``docs/``
     - Framework and solutions
     - Viewpoint projections applied to this solution. Where HCD and C4
       lenses render as documentation.
   * - ``deployment/``
     - Framework and solutions
     - Runtime configuration: Docker, Kubernetes, environment setup.

Identification Rule
-------------------

A simple rule identifies accelerators:

.. code-block:: python

    RESERVED = {'core', 'contrib', 'applications', 'docs', 'deployment'}

    def is_accelerator(dirname: str) -> bool:
        """Return True if dirname is an accelerator, not a reserved word."""
        return (
            dirname not in RESERVED
            and not dirname.startswith('_')
            and not dirname.startswith('.')
        )

Example: Framework Structure
----------------------------

::

    julee/
      core/              # Reserved - the idioms
      hcd/               # Accelerator (viewpoint)
      c4/                # Accelerator (viewpoint)
      contrib/           # Reserved - contains nested accelerators
        ceap/            # Accelerator (contrib module)
        polling/         # Accelerator (contrib module)
      applications/      # Reserved - exposure layer
      docs/              # Reserved - viewpoint projections
      deployment/        # Reserved - runtime config

Example: Solution Structure
---------------------------

::

    my_solution/
      billing/           # Accelerator - bounded context
      inventory/         # Accelerator - bounded context
      shipping/          # Accelerator - bounded context
      applications/      # Reserved - this solution's APIs, etc.
      docs/              # Reserved - this solution's documentation
      deployment/        # Reserved - this solution's runtime config

Viewing the Directory
---------------------

When you ``ls`` a julee solution, the reserved words tell you where to find
infrastructure concerns, while everything else is a domain::

    $ ls my_solution/
    billing/          # <- domain (not reserved)
    inventory/        # <- domain (not reserved)
    shipping/         # <- domain (not reserved)
    applications/     # <- reserved (exposure)
    docs/             # <- reserved (viewpoints applied)
    deployment/       # <- reserved (runtime)

This "screaming architecture" means the bounded contexts are immediately
visible—no digging into nested directories to understand what the solution
does.

Why These Names?
----------------

core/
^^^^^

The name ``core`` signals "this is foundational, everything depends on it."
It's the parent accelerator that defines the idioms all other accelerators
are ontologically bound to.

contrib/
^^^^^^^^

Borrowed from Django's "contrib" pattern (``django.contrib.auth``,
``django.contrib.admin``). It signals "official, supported, batteries-included"
while also indicating "optional, you choose to use this."

applications/
^^^^^^^^^^^^^

Clean Architecture terminology. Applications are the layer that exposes
domain logic to the outside world—whether via HTTP APIs, CLI tools, message
queues, or documentation renderers.

docs/
^^^^^

An affordance for new users. Documentation is expected here. It also signals
that docs are a first-class concern, not an afterthought.

deployment/
^^^^^^^^^^^

Where operational concerns live. Separates "what the solution does" from
"how it runs in production."
