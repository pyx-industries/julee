Third-Party Modules
===================

Third-party modules extend Julee solutions with external functionality. They can be :doc:`embedded or dispatched <modules>`—a distinction that affects supply chain provenance.

This page focuses on **integration patterns**, **evaluation criteria**, and **common third-party integrations**.

Nearly everything on this page is an
:doc:`oracle </architecture/clean_architecture/oracles>`.

An oracle is the :doc:`driven port </architecture/clean_architecture/protocols>`
for asking something the solution does not control,
and getting the answer back in that thing's currency rather than yours.
It names no :doc:`entity </architecture/clean_architecture/entities>`,
which is exactly what wrapping a third party looks like:
you get their JSON, their string, their status—not one of your concepts.

The word is recent. Before it existed, authors reached for
``*Repository`` or ``*Service``, and a census across ten codebases
found four of them splitting evenly between the two.
The examples below are named as oracles because that is what they are.

Integration Patterns
--------------------

Protocol-Based Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Hide third-party details behind protocols.
``extract`` takes bytes and returns a string—no entity in sight—
so the port is an oracle::

    # Protocol defines the interface
    class TextExtractorOracle(Protocol):
        async def extract(self, document: bytes) -> str: ...

    # Embedded implementation using pypdf
    class PyPDFExtractor:
        async def extract(self, document: bytes) -> str:
            reader = pypdf.PdfReader(BytesIO(document))
            return "\n".join(page.extract_text() for page in reader.pages)

    # Dispatched implementation using external service
    class CloudExtractorService:
        def __init__(self, api_key: str):
            self.client = SomeCloudAPI(api_key)

        async def extract(self, document: bytes) -> str:
            return await self.client.extract_text(document)

    # Use case doesn't care which implementation
    class DocumentUseCase:
        def __init__(self, extractor: TextExtractorOracle):
            self.extractor = extractor  # Could be either

Both implementations do I/O—one reads a PDF, the other calls a cloud API—
so a :doc:`pipeline </architecture/solutions/pipelines>` reaches this port
through a Temporal activity.

Adapter Pattern
~~~~~~~~~~~~~~~

Wrap third-party APIs to match your protocols.

The protocol below takes two strings and returns a ``dict``.
It is named ``*Oracle`` rather than ``*Service`` because it is bound to
no entity: an LLM hands back its own JSON, and calling that a
:doc:`service </architecture/clean_architecture/services>`
would promise a transformation between two of your entities
that this protocol does not perform.

::

    # Third-party client (their interface)
    from some_ai_provider import AIClient

    # Your protocol
    class KnowledgeOracle(Protocol):
        async def query(self, content: str, prompt: str) -> dict: ...

    # Adapter wraps their interface to match yours
    class SomeAIProviderAdapter:
        """Adapts SomeAIProvider to the KnowledgeOracle protocol."""

        def __init__(self, api_key: str):
            self.client = AIClient(api_key=api_key)

        async def query(self, content: str, prompt: str) -> dict:
            # Translate to their API
            response = await self.client.analyze(
                text=content,
                instructions=prompt,
                output_format="json"
            )
            # Translate response to your format
            return {"result": response.data, "confidence": response.score}

Returning a ``dict`` is the honest choice here, not a shortcut.
Modelling a provider's response as a domain entity
would be a claim the solution cannot keep:
the provider changes its shape when it likes.
If you do model it—and return one of your own entities—
what you have is a
:doc:`repository </architecture/clean_architecture/repositories>`
bound to that entity, not an oracle at all.

Factory Pattern
~~~~~~~~~~~~~~~

Create implementations based on configuration:

::

    def get_knowledge_oracle(settings: Settings) -> KnowledgeOracle:
        provider = settings.ai_provider

        if provider == "anthropic":
            return AnthropicKnowledgeOracle(api_key=settings.anthropic_api_key)
        elif provider == "openai":
            return OpenAIKnowledgeOracle(api_key=settings.openai_api_key)
        elif provider == "local":
            return LocalLLMOracle(endpoint=settings.llm_endpoint)
        elif provider == "custom":
            return CustomProviderAdapter(api_key=settings.custom_api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

Evaluation Criteria
-------------------

When choosing third-party modules, consider:

- **Functionality** - Does it do what you need? How well?
- **Reliability** - Uptime, error rates, support quality
- **Security** - Data handling, encryption, compliance certifications
- **Performance** - Latency, throughput, rate limits
- **Cost** - Pricing model, cost at your scale
- **Lock-in** - How hard to switch? Are there alternatives?

The :doc:`embedded vs dispatched <modules>` distinction also affects evaluation.

Common Third-Party Integrations
-------------------------------

AI/LLM Providers
~~~~~~~~~~~~~~~~

The CEAP kit routes to a provider from configuration
rather than exposing one class per provider::

    from julee_ceap.infrastructure.services.knowledge_service.factory import (
        knowledge_service_factory,
    )

    service = knowledge_service_factory(knowledge_service_config)

The configuration names the provider and model,
so adding one is a change to the factory and its config,
not to any :doc:`use case </architecture/clean_architecture/use_cases>`.

Document Processing
~~~~~~~~~~~~~~~~~~~

::

    # Embedded PDF processing
    import pypdf

    class PDFProcessor:
        async def extract_text(self, document: bytes) -> str:
            reader = pypdf.PdfReader(BytesIO(document))
            return "\n".join(p.extract_text() for p in reader.pages)

    # Cloud document processing
    from azure.ai.documentintelligence import DocumentIntelligenceClient

    class AzureDocumentProcessor:
        async def extract_text(self, document: bytes) -> str:
            result = await self.client.analyze_document(
                "prebuilt-read", document
            )
            return result.content

Storage Services
~~~~~~~~~~~~~~~~

Storing raw bytes under a key is an
:doc:`oracle </architecture/clean_architecture/oracles>`,
not a :doc:`repository </architecture/clean_architecture/repositories>`.
The port below deals in ``str`` and ``bytes``:
it knows nothing about any of your entities,
so it cannot be bound to one.

::

    # AWS S3
    import boto3

    class S3Oracle:
        def __init__(self):
            self.client = boto3.client('s3')

        async def store(self, key: str, data: bytes):
            self.client.put_object(Bucket='my-bucket', Key=key, Body=data)

    # MinIO (S3-compatible, self-hosted)
    from minio import Minio

    class MinioOracle:
        def __init__(self, endpoint: str):
            self.client = Minio(endpoint)

Julee's own MinIO classes *are* repositories,
and the difference is instructive.
``MinioDocumentRepository`` is bound to ``Document``:
it takes and returns that entity,
and serialising it to an object is an implementation detail.
The example above never mentions an entity at all.

Both do I/O, so either way a
:doc:`pipeline </architecture/solutions/pipelines>`
reaches them through an activity.

Testing with Third-Party Modules
--------------------------------

Mock External Services
~~~~~~~~~~~~~~~~~~~~~~

::

    class MockKnowledgeOracle:
        """Mock for testing without hitting real API."""

        async def query(self, content: str, prompt: str) -> dict:
            return {"result": "mocked response", "confidence": 1.0}

    @pytest.mark.asyncio
    async def test_use_case():
        use_case = MyUseCase(
            knowledge_oracle=MockKnowledgeOracle()
        )
        result = await use_case.execute("test input")
        assert result is not None

Integration Tests with Real Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_with_real_provider():
        oracle = knowledge_service_factory(config)
        result = await oracle.query("Hello", "Respond with 'Hi'")
        assert "Hi" in result["response"]

Summary
-------

Third-party modules extend Julee with external functionality. Use protocol-based integration, adapters, or factory patterns to hide implementation details. The :doc:`embedded vs dispatched <modules>` distinction affects supply chain provenance.

Almost every port on this page is an
:doc:`oracle </architecture/clean_architecture/oracles>`:
bound to no entity, dealing in the third party's currency,
and reached from a :doc:`pipeline <pipelines>` through an activity.
If you find yourself modelling the response as one of your own entities,
you have written a
:doc:`repository </architecture/clean_architecture/repositories>` instead,
and that is a fine thing to do—as long as you can keep the promise.
