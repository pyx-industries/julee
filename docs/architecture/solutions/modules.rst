Modules
=======

Modules provide reusable functionality for Julee solutions. They can be **embedded** (imported and run in your process) or **dispatched** (called as external services).

This distinction matters for supply chain provenance: embedded modules run as part of your composition, while dispatched modules involve separate supply chain actors.

Module Types
------------

Julee solutions use three types of modules:

**Batteries-Included Modules**
    Ready-made functionality from the Julee framework. CEAP workflows, repository implementations, service integrations.

    See :doc:`batteries-included` for details.

**Third-Party Modules**
    External modules you import or integrate. Can be embedded or dispatched.

    See :doc:`3rd-party` for details.

**Domain-Specific Modules**
    Your own code implementing business logic specific to your solution.

Embedded vs Dispatched
----------------------

The key architectural decision is whether to **embed** or **dispatch** a module.

Embedded Modules
~~~~~~~~~~~~~~~~

Embedded modules are imported and run in your process:

::

    # Embedded: imported and runs in your process
    from some_library import PDFParser

    class DocumentProcessingComposition:
        def __init__(self, pdf_parser: PDFParser):
            self.pdf_parser = pdf_parser

        async def execute(self, document: bytes) -> dict:
            # PDF parsing runs in your process
            parsed = self.pdf_parser.parse(document)
            return parsed

**Characteristics:**

- Code runs in your process
- No network calls
- You control execution
- Your worker is the supply chain actor

**Supply chain perspective:** The embedded module's code becomes part of your composition. From a supply chain perspective, **you** (your worker) are the actor performing the work, even though you're using third-party code.

Dispatched Modules
~~~~~~~~~~~~~~~~~~

Dispatched modules are called as external services:

::

    # Dispatched: called over network as a service
    class DocumentProcessingComposition:
        def __init__(self, ai_service: KnowledgeService):
            self.ai_service = ai_service

        async def execute(self, document_id: str) -> dict:
            # AI processing happens on Anthropic's servers
            result = await self.ai_service.query(
                document_id,
                "Extract invoice data"
            )
            return result

**Characteristics:**

- Code runs on someone else's servers
- Network calls involved
- They control execution
- External party is a supply chain actor

**Supply chain perspective:** When you dispatch to an external service, that service becomes a **supply chain actor** in its own right. They process your data, and their processing is recorded in the workflow history.

Supply Chain Implications
-------------------------

The embedded/dispatched distinction has significant implications for supply chain provenance.

Embedded Module Provenance
~~~~~~~~~~~~~~~~~~~~~~~~~~

When using embedded modules:

::

    Activity: process_document
    Actor: worker-1 (your worker)
    Input: document bytes
    Output: parsed data
    Duration: 2.5 seconds

The workflow history shows **your worker** as the actor. The fact that you used a third-party library is an implementation detail not visible in the supply chain record.

**Implications:**

- You are responsible for the output
- You control the execution environment
- Audit trail shows your worker as the actor
- Compliance responsibility is yours

Dispatched Module Provenance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When dispatching to external services:

::

    Activity: extract_data
    Actor: worker-1 (your worker)
    Input: document_id, prompt
    Output: extracted_fields
    Duration: 45 seconds
    External Service: Anthropic Claude
    Service Response ID: msg_01XYZ...

The workflow history shows:

- Your worker initiated the request
- An external service (Anthropic) performed the AI processing
- The service's response is recorded

**Implications:**

- External service is a supply chain actor
- They have their own processing, logging, compliance
- Your audit trail shows the handoff
- Compliance responsibility is shared

Choosing Embedded vs Dispatched
-------------------------------

Decision Factors
~~~~~~~~~~~~~~~~

**Choose embedded when:**

- You need full control over execution
- Data sensitivity requires in-process handling
- Performance requires avoiding network latency
- You want to minimize supply chain actors
- The functionality is a library, not a service

**Choose dispatched when:**

- The service provides capabilities you can't replicate (AI, specialized processing)
- The service is managed/maintained by experts
- You want to outsource operational complexity
- The service model is economically advantageous
- Compliance requires separation of concerns

Hybrid Approaches
~~~~~~~~~~~~~~~~~

Many solutions use both:

::

    class InvoiceProcessingComposition:
        def __init__(
            self,
            # Embedded: PDF parsing
            pdf_parser: PDFParser,
            # Dispatched: AI extraction
            ai_service: KnowledgeService,
            # Embedded: Validation
            validator: InvoiceValidator,
        ):
            self.pdf_parser = pdf_parser
            self.ai_service = ai_service
            self.validator = validator

        async def execute(self, document: bytes) -> Invoice:
            # Embedded: parse PDF (you are the actor)
            text = self.pdf_parser.extract_text(document)

            # Dispatched: AI extraction (Anthropic is an actor)
            extracted = await self.ai_service.query(text, "Extract invoice fields")

            # Embedded: validate (you are the actor)
            invoice = self.validator.validate(extracted)

            return invoice

The supply chain record shows:

1. Your worker parsed the PDF
2. Anthropic extracted the fields
3. Your worker validated the result

Self-Hosted Services
--------------------

A middle ground: dispatch to services you host yourself.

::

    class DocumentProcessingComposition:
        def __init__(
            self,
            # Dispatched to self-hosted Ollama
            local_llm: KnowledgeService,
        ):
            self.local_llm = local_llm

        async def execute(self, document_id: str) -> dict:
            # AI processing on your Ollama server
            result = await self.local_llm.query(document_id, "Extract data")
            return result

**Supply chain perspective:**

- The service is still a separate actor (different process/server)
- But you control and operate that actor
- Compliance responsibility is clearer
- Audit trail shows the service call

This is common for:

- Self-hosted LLMs (Ollama, vLLM)
- Internal microservices
- On-premise processing requirements

Module Integration Patterns
---------------------------

Pattern: Protocol Abstraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Hide embedded/dispatched behind a protocol:

::

    class KnowledgeService(Protocol):
        async def query(self, content: str, prompt: str) -> dict: ...

    # Embedded implementation
    class LocalKnowledgeService:
        def __init__(self, model: LocalLLM):
            self.model = model

        async def query(self, content: str, prompt: str) -> dict:
            # Runs in-process
            return self.model.generate(content, prompt)

    # Dispatched implementation
    class AnthropicKnowledgeService:
        def __init__(self, api_key: str):
            self.client = Anthropic(api_key=api_key)

        async def query(self, content: str, prompt: str) -> dict:
            # Calls external API
            response = await self.client.messages.create(...)
            return response.content

The composition doesn't know (or care) which implementation is used:

::

    class ExtractionComposition:
        def __init__(self, knowledge: KnowledgeService):
            self.knowledge = knowledge  # Could be embedded or dispatched

        async def execute(self, content: str) -> dict:
            return await self.knowledge.query(content, "Extract data")

Pattern: Configuration-Based Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose embedded vs dispatched via configuration:

::

    def get_knowledge_service(settings: Settings) -> KnowledgeService:
        if settings.ai_mode == "embedded":
            # Use local LLM (embedded)
            return LocalKnowledgeService(load_local_model())
        elif settings.ai_mode == "self-hosted":
            # Use self-hosted Ollama (dispatched, but you operate it)
            return OllamaKnowledgeService(endpoint=settings.ollama_endpoint)
        elif settings.ai_mode == "cloud":
            # Use Anthropic (dispatched to third party)
            return AnthropicKnowledgeService(api_key=settings.anthropic_api_key)

This allows the same composition to run with different supply chain characteristics based on deployment requirements.

Summary
-------

**Modules can be embedded or dispatched, with different supply chain implications.**

**Embedded modules:**

- Run in your process
- You are the supply chain actor
- Full control, full responsibility

**Dispatched modules:**

- Run on external services
- External party is a supply chain actor
- Shared responsibility, recorded handoffs

**Key principle:** The choice between embedded and dispatched affects who appears in your supply chain audit trail and who bears compliance responsibility.

For batteries-included modules, see :doc:`batteries-included`.

For third-party integration, see :doc:`3rd-party`.

For supply chain provenance in pipelines, see :doc:`pipelines`.
