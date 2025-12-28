"""CEAP (Capture, Extract, Assemble, Publish) accelerator.

A general purpose AI heuristic workflow useful in many circumstances.
CEAP demonstrates Clean Architecture principles through a real-world
document processing pipeline.

Architecture Walkthrough
------------------------
CEAP is an automated process with no user interaction, executed by a
Worker application. The most interesting part is the pipeline called
:py:class:`~julee.contrib.ceap.use_cases.ExtractAssembleDataUseCase`.

A use case is usually specific to a business domain, but CEAP is unusual
because it's a generic, reusable pattern. That's why it's part of the
framework - you can reuse it without having to reinvent the wheel.

The use case is understandable and testable, but it leaves a lot to the
imagination. What is a KnowledgeService? A DocumentRepository? An
AssemblyRepository, AssemblySpecificationRepository,
KnowledgeServiceQueryRepository, or KnowledgeServiceConfigRepository?
How do they work? Those questions are answered separately.

Repositories store and access data. As long as the use case can use them,
it shouldn't have to care about how they work. So "what is the repository"
is first defined in the abstract, using a Python Protocol specification,
which is part of the domain model.

Second, "how do they work" is an infrastructure concern. There is code
that implements the protocol using technology. Actually, we have more
than one implementation of each - MinIO implementations for production,
memory implementations for testing. The memory implementations are volatile
and unsuitable for production, but useful as testing doubles in unit tests
that run fast and in parallel without external dependencies.

So, each use case defines a deterministic business process, but a lot of
the heavy lifting is being done by the entity classes in the domain model.

Capabilities
------------
- Document capture and extraction
- Assembly of document components
- Policy validation and enforcement
- Knowledge service integration (Anthropic, OpenAI, etc.)
"""
