Third-Party Modules
===================

Third-party modules extend Julee solutions with external functionality. They can be :doc:`embedded or dispatched <modules>`—a distinction that affects supply chain provenance.

This page focuses on **integration patterns**, **evaluation criteria**, and **common third-party integrations**.

Integration Patterns
--------------------

Protocol-Based Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Hide third-party details behind protocols:

::

    # Protocol defines the interface
    class TextExtractor(Protocol):
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

    # Composition doesn't care which implementation
    class DocumentComposition:
        def __init__(self, extractor: TextExtractor):
            self.extractor = extractor  # Could be either

Adapter Pattern
~~~~~~~~~~~~~~~

Wrap third-party APIs to match your protocols:

::

    # Third-party client (their interface)
    from some_ai_provider import AIClient

    # Your protocol
    class KnowledgeService(Protocol):
        async def query(self, content: str, prompt: str) -> dict: ...

    # Adapter wraps their interface to match yours
    class SomeAIProviderAdapter:
        """Adapts SomeAIProvider to KnowledgeService protocol."""

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

Factory Pattern
~~~~~~~~~~~~~~~

Create implementations based on configuration:

::

    def get_knowledge_service(settings: Settings) -> KnowledgeService:
        provider = settings.ai_provider

        if provider == "anthropic":
            return AnthropicKnowledgeService(api_key=settings.anthropic_api_key)
        elif provider == "openai":
            return OpenAIKnowledgeService(api_key=settings.openai_api_key)
        elif provider == "local":
            return LocalLLMService(endpoint=settings.llm_endpoint)
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

Julee provides :py:class:`~julee.services.knowledge_service.anthropic.AnthropicKnowledgeService` and other provider implementations::


    # Anthropic
    from julee.services.knowledge_service.anthropic import AnthropicKnowledgeService

    service = AnthropicKnowledgeService(
        api_key=settings.anthropic_api_key,
        model="claude-3-5-sonnet-20241022"
    )

    # OpenAI
    from julee.services.knowledge_service.openai import OpenAIKnowledgeService

    service = OpenAIKnowledgeService(
        api_key=settings.openai_api_key,
        model="gpt-4o"
    )

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

::

    # AWS S3
    import boto3

    class S3Repository:
        def __init__(self):
            self.client = boto3.client('s3')

        async def store(self, key: str, data: bytes):
            self.client.put_object(Bucket='my-bucket', Key=key, Body=data)

    # MinIO (S3-compatible, self-hosted)
    from minio import Minio

    class MinioRepository:
        def __init__(self, endpoint: str):
            self.client = Minio(endpoint)

Testing with Third-Party Modules
--------------------------------

Mock External Services
~~~~~~~~~~~~~~~~~~~~~~

::

    class MockKnowledgeService:
        """Mock for testing without hitting real API."""

        async def query(self, content: str, prompt: str) -> dict:
            return {"result": "mocked response", "confidence": 1.0}

    @pytest.mark.asyncio
    async def test_composition():
        composition = MyComposition(
            knowledge_service=MockKnowledgeService()
        )
        result = await composition.execute("test input")
        assert result is not None

Integration Tests with Real Services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_with_real_anthropic():
        service = AnthropicKnowledgeService(
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        result = await service.query("Hello", "Respond with 'Hi'")
        assert "Hi" in result["response"]

Summary
-------

Third-party modules extend Julee with external functionality. Use protocol-based integration, adapters, or factory patterns to hide implementation details. The :doc:`embedded vs dispatched <modules>` distinction affects supply chain provenance.
