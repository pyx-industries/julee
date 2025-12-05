Automate Digital Product Supply Chains
======================================

Julee is a framework for building resilient,
transparent, and accountable digital product supply chains.
It's a kind of orchestrator that manages work pipelines,
using a set of idioms based on "Clean Architecture" principles.

A "digital product supply chain" is a way of thinking about how work gets done.
That work might involve humans, traditional automation, and AI agents or services.
At it's heart, Julee applications are process that follow business rules.
They are done in a way that leaves an impecable audit trail,
which can be used to create a "digital product passport"
to acompany the output of the process.
This makes Julee particularly suitable for processes
with non-trivial compliance requirements, such as responsible AI requirements
or algorithmic due-dilligence of high-integrity supply chain information.

The processes that Julee orchestrates may depend on unreliable services,
e.g. services which might temporarially fail, be rate-limited, or timeout, etc.
Julee runs the work pipelines in a way that is resiliant,
with intelligent retrys and so on.
It make tradeoffs in favour of reliability and resiliance,
at the expense of throughput and latency.
Julee is most suitable for processes which must be done correctly,
and which may be complex and long-running.

The clean architecture principles allow Julee applications to evolve.
Infrastructure can be swapped-out (without needing to rewire everything),
business-logic and domain models can be adapted as requirements change over time,
and the system remains managable even in the most complicated enterprises.
Essentially, the digital supply chain transparancy creates an opportunity for good process governance;
risks can be identified and mitigated, strategies implemented, and processes refined over time.
Comprehensive test automation, clean and clear boundaries, and  enable best practice,


What, if anything, is a Framework?
----------------------------------

If you are a software developer familiar with django,
then the short answer is that Julee is a framework
in the same way that django is.
For everyone else, Julee is a toolkit for making software systems
that meet certain types of business need.
It's a consistent and idiomatic way of building software
that leverages reusable code and ideas, rather than reinventing them.

Let's get some terminology strait.


Julee Solution
^^^^^^^^^^^^^^
A Julee Solution is a technical solution to partiular set of business problems.
It is a software system that has been built
to meet some particular business requirements.
It includes one or more **application** that people use,
and it will have some bespoke configuration and code
that makes it unique.

The application(s) are built "the Julee way",
meaning the code and configuration is structured using Julee idioms.
It has a compile-time dependency on the open source julee framework,
which means it reuses a bunch of existing software that it doesn't need to re-implement itself.

Julee solutions may be distributed systems,
meaning they can depend on 3rd party services.
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

See :doc:`repositories` for the repository pattern.

See :doc:`services` for the service pattern.

See :doc:`protocols` for protocol-based design.


Julee Pipelines
^^^^^^^^^^^^^^^
A Julee Pipeline is an orchestrated business process,
that combines business rules (a "use-case" in clean architecture terminology).
A julee solution is a collection of one or more Pipelines.

The pipelines are the compositions.
They produce a digital product by following business rules,
and the depend on services and repositories to get the work done.
The pipeline is the thing that runs reliably and keeps immaculate records.

See :doc:`workflows` for CEAP workflows - the included pipeline batteries.


What Batteries are Included?
-----------------------------

Like Django provides an admin interface and ORM out-of-the-box, Julee provides production-ready components:

**CEAP Workflows**
    Pre-built workflows implementing the Capture, Extract, Assemble, Publish pattern for AI-driven document processing.

**Repository Layer**
    Storage abstractions with pluggable implementations (MinIO, PostgreSQL, in-memory).

**Service Layer**
    Integration patterns for AI and external services (Anthropic, OpenAI, local LLMs).

**Domain Models**
    Ready-to-use Pydantic models for common entities (Document, Assembly, Policy).

**Dependency Injection**
    Configuration and service wiring using FastAPI's DI system.

**Temporal Integration**
    Workflow orchestration, activity patterns, and testing utilities.

You can use these batteries as-is or customize them for your needs.

Clean Architecture for Manageability
-------------------------------------

Julee's Clean Architecture approach makes complicated systems manageable:

**Layer Separation**
    Domain logic lives separately from infrastructure. Change databases without touching business rules.

**Protocol-Based Design**
    All external dependencies (AI services, storage) hide behind protocols. Swap implementations easily.

**Testability**
    Every layer can be tested independently. Fast unit tests with mocks, integration tests with real services.

**Explicit Dependencies**
    Dependency injection makes system wiring visible and configurable.

**Maintainability**
    Changes stay localized. Adding a new AI provider doesn't require rewriting workflows.

For details on the layered architecture, see :doc:`clean_architecture`.

For protocol-based design patterns, see :doc:`protocols`.

When to Use Julee
-----------------

Julee is ideal for:

**Document Processing Pipelines**
    Extract structured data from documents using AI services. Julee's CEAP workflows are purpose-built for this.

**AI-Augmented Workflows**
    Any long-running process that involves AI services. Temporal handles orchestration, Julee provides the patterns.

**Compliance-Critical Systems**
    When you need audit trails and policy enforcement. Julee's architecture ensures accountability.

**Multi-Provider AI Systems**
    Compare AI providers, switch between them, or use different providers for different tasks.

**Systems Requiring High Reliability**
    When failures must be handled gracefully. Temporal's durability plus Clean Architecture's testability.

When Not to Use Julee
----------------------

Julee might be overkill for:

**Simple Scripts**
    If you just need to call an AI API once, use the API directly.

**Real-Time Systems**
    Temporal workflows have overhead. For sub-second latency requirements, use simpler approaches.

**Non-AI Workflows**
    While Julee's architecture works for any domain, it's optimized for AI pipelines.

What You Get
------------

**Immediate Productivity**
    Start with working CEAP workflows. Customize as needed rather than building from scratch.

**Production-Ready Patterns**
    Repository, Service, and Workflow patterns proven in real systems.

**Testing Infrastructure**
    In-memory implementations for fast tests. Temporal testing utilities for workflow tests.

**Flexibility**
    Protocol-based design means you're never locked in. Swap any component.

**Observability**
    Temporal UI and event sourcing give complete visibility into system behavior.

**Framework, Not a Monolith**
    Install Julee as a dependency. Use what you need, extend what you want.

Next Steps
----------

**Understand the Architecture**
    - :doc:`clean_architecture` - How Julee organizes code into layers
    - :doc:`protocols` - How protocol-based design enables flexibility

**Learn the Patterns**
    - :doc:`repositories` - The repository pattern for persistence
    - :doc:`services` - The service pattern for AI and external operations
    - :doc:`workflows` - CEAP workflows for document processing

**Deploy Your System**
    - :doc:`deployment` - Runtime architecture and deployment patterns
