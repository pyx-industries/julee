Julee is a Framework
====================

**A reusable framework and a business application are different beasts.**
One is a vocabulary for building things; the other is the thing being built.

Julee is a framework for building resilient,
transparent, and accountable digital product supply chains.
It's a kind of orchestrator that manages work pipelines,
using a set of idioms based on "Clean Architecture" principles.

A "digital product supply chain" is a way of thinking about how work gets done.
That work might involve humans, traditional automation, and AI agents or services.
At it's heart, Julee applications are processes that follow business rules.
They are done in a way that leaves an impeccable audit trail,
which can be used to create a "digital product passport"
to accompany the output of the process.
This makes Julee particularly suitable for processes
with non-trivial compliance requirements, such as responsible AI requirements
or algorithmic due-diligence of high-integrity supply chain information.

The processes that Julee orchestrates may depend on unreliable services,
e.g. services which might temporarily fail, be rate-limited, or timeout, etc.
Julee runs the work pipelines in a way that is resilient,
with intelligent retries and so on.
It makes tradeoffs in favour of reliability and resilience,
at the expense of throughput and latency.
Julee is most suitable for processes which must be done correctly,
and which may be complex and long-running.

The clean architecture principles allow Julee applications to evolve.
Infrastructure can be swapped-out (without needing to rewire everything),
business-logic and domain models can be adapted as requirements change over time,
and the system remains manageable even in the most complicated enterprises.
Essentially, the digital supply chain transparency creates an opportunity for good process governance;
risks can be identified and mitigated, strategies implemented, and processes refined over time.
Comprehensive test automation, clean and clear boundaries enable best practice.


Framework vs Solution
---------------------

Understanding the difference between a framework and a solution
is essential to understanding why Julee's
codebase is organised the way it is.

**A framework provides vocabulary.** Julee's first-class concepts are
the building blocks for constructing digital supply chains:
The entities (domain models), business processes (use cases),
and protocols (repositories and services).
This is why Julee's codebase is organised around ``domain/``, ``infrastructure/``, ``repositories/``—
these are the words in Julee's vocabulary.

**A solution uses that vocabulary to say something specific.**
When you build a solution with Julee, your codebase should be organised
around your business domain, the specific problem you're solving.
Your top-level directories reflect your bounded contexts

If you are a software developer familiar with django,
then Julee is a framework in the same way that django is.
For everyone else, Julee is a toolkit for making software systems
that meet certain types of business need.
It's a consistent and idiomatic way of building software
that leverages reusable code and ideas, rather than reinventing them.

Let's get some terminology strait.


Julee Solution
^^^^^^^^^^^^^^
A Julee Solution is software that has been built
to meet some particular business requirements.
It includes one or more **application** that people use,
and it will have some bespoke configuration and code
that makes it unique.

The application(s) are built "the Julee way",
meaning the code and configuration is structured using Julee idioms.
It has a compile-time dependency on the framework,
which means it reuses a bunch of existing software that it doesn't need to re-implement itself.

A Julee solution may be a distributed system,
meaning it can depend on 3rd party services at run time.
These 3rd party service may themselves be julee solutions,
or not - they could be any other component that provides an appropriate interface.

Julee solutions can also incorporate internal services,
which may be bespoke for the solution, or imported at build-time
using something like a "reusable app" framework.

**Runtime view of a Julee solution:**

.. uml:: diagrams/c4_context.puml

This C4 context diagram shows how a deployed Julee application depends on:

- **Infrastructure** you deploy (Temporal, Object Storage, PostgreSQL)
- **Services** from the supply chain (Third-party APIs like Anthropic/OpenAI, Self-hosted services like local LLMs, Bundled services in your app)

These are runtime dependencies - your application calls them over the network at runtime.


Julee Framework
^^^^^^^^^^^^^^^
A python software package that is reused by the Julee solution.
This includes a number of shortcuts and helpers for building a julee solution,
as well as tools for managing it, and other reusable titbits that might save you some time.

In some ways it's a bit of an un-framework.
There is this idea that frameworks, databases, and other important technology details are actually unimportant.
The most important things are the salient features of the business domain.
The Julee framework is an implementation of Clean Architecture principles
that make these salient features prominent.
It's a set of idioms (ways of doing things) that consistently implement this clean architecture.

The julee framework has a "batteries included" philosophy,
so you can get started quickly and don't have to reinvent the wheel.
This means that the framework itself includes a number of high quality,
ready-made services, repositories and pipelines that are genericly useful
and can be incorporated into a julee solution cheeply.

**Build-time composition of a Julee solution:**

.. uml:: diagrams/c4_component.puml

This C4 component diagram shows how you compose your application at build time:

- **Julee Framework** (left boundary) provides the batteries:

  - Domain protocols and base models
  - CEAP use case implementations
  - Pre-built Temporal workflows
  - Repository implementations (MinIO, Memory)
  - Service implementations (Anthropic, OpenAI, local LLM)
  - Dependency injection container

- **Your Application** (right boundary) extends the framework:

  - Your domain models (extend framework models)
  - Your use cases (use framework patterns)
  - Your configuration (wire framework components)
  - Your API and workers (run framework workflows)

This is a compile-time dependency. You ``pip install julee`` and import its components into your code.


Services and Repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^
These are the components do useful things and can be part of a julee solution composition.
Repositories are components that store and access data.
Services are components that "do things" with data.

The Julee framework uses Python Protocols to define repository and service interfaces,
and a Julee Solution can use any implementation of a repository or service that complies with the interfaces.

The :doc:`repository pattern <clean_architecture/repositories>`, :doc:`service pattern <clean_architecture/services>`, and :doc:`protocol-based design <clean_architecture/protocols>` are covered in the Clean Architecture section.


Julee Pipelines
^^^^^^^^^^^^^^^
A Julee Pipeline is an orchestrated business process,
that combines business rules (a "use-case" in clean architecture terminology).
A julee solution is a collection of one or more Pipelines.

The pipelines are the compositions.
They produce a digital product by following business rules,
and the depend on services and repositories to get the work done.
The pipeline is the thing that runs reliably and keeps immaculate records.

:doc:`CEAP workflows <applications/worker>` are the included pipeline batteries.
