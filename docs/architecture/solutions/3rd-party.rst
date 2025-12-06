Third-Party Modules
===================

Third-party modules extend Julee solutions with external functionality. They can be **embedded** (imported libraries) or **dispatched** (external services).

Understanding how third-party modules integrate is important for supply chain management and compliance.

Types of Third-Party Modules
----------------------------

Embedded Libraries
~~~~~~~~~~~~~~~~~~

Python packages you import and run in your process:

::

    # Embedded: runs in your process
    import pypdf
    from langchain import LLMChain

    class DocumentProcessor:
        def __init__(self):
            self.pdf_reader = pypdf.PdfReader

        async def process(self, document: bytes) -> str:
            # PDF parsing runs in your worker
            reader = self.pdf_reader(BytesIO(document))
            return reader.pages[0].extract_text()

**Examples:**

- PDF processing (pypdf, pdfplumber)
- Document parsing (python-docx, openpyxl)
- Data processing (pandas, numpy)
- Local LLM wrappers (llama-cpp-python)

**Supply chain:** Your worker is the actor. The library is a tool you use.

External Services (APIs)
~~~~~~~~~~~~~~~~~~~~~~~~

Services you call over the network:

::

    # Dispatched: runs on their servers
    from anthropic import Anthropic

    class AIService:
        def __init__(self, api_key: str):
            self.client = Anthropic(api_key=api_key)

        async def extract(self, content: str) -> dict:
            # Processing happens on Anthropic's servers
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": content}]
            )
            return response

**Examples:**

- AI providers (Anthropic, OpenAI, Cohere)
- Cloud services (AWS, GCP, Azure)
- SaaS APIs (Stripe, SendGrid, Twilio)
- Data providers (weather APIs, geocoding)

**Supply chain:** The service provider is a supply chain actor.

Self-Hosted Services
~~~~~~~~~~~~~~~~~~~~

Services you deploy and operate yourself:

::

    # Dispatched to your infrastructure
    import httpx

    class LocalLLMService:
        def __init__(self, endpoint: str = "http://localhost:11434"):
            self.endpoint = endpoint
            self.client = httpx.AsyncClient()

        async def generate(self, prompt: str) -> str:
            # Processing happens on your Ollama server
            response = await self.client.post(
                f"{self.endpoint}/api/generate",
                json={"model": "llama2", "prompt": prompt}
            )
            return response.json()["response"]

**Examples:**

- Self-hosted LLMs (Ollama, vLLM, text-generation-inference)
- Internal microservices
- On-premise processing services
- Private cloud deployments

**Supply chain:** You operate the service, but it's still a separate actor in the workflow.

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

Supply Chain Considerations
---------------------------

Actor Identification
~~~~~~~~~~~~~~~~~~~~

For compliance and audit, identify who performs each operation:

::

    # Embedded: you are the actor
    Activity: parse_document
    Actor: worker-1 (your process)
    Tool: pypdf library
    Duration: 0.5s

    # Dispatched: they are an actor
    Activity: extract_data
    Actor: worker-1 (initiator)
    External Actor: Anthropic (processor)
    Service: claude-3-5-sonnet
    Duration: 12s

Data Flow
~~~~~~~~~

Track where data goes:

**Embedded:** Data stays in your process.

::

    Document bytes → Your worker → Parsed text
    (data never leaves your infrastructure)

**Dispatched:** Data sent to external party.

::

    Document bytes → Your worker → Anthropic API → Response
    (data sent to Anthropic's servers for processing)

Compliance Implications
~~~~~~~~~~~~~~~~~~~~~~~

**Embedded modules:**

- You control data handling
- Your security policies apply
- Your compliance responsibility

**Dispatched modules:**

- Data leaves your control
- Their security policies apply
- Shared compliance responsibility
- May need data processing agreements

Choosing Third-Party Modules
----------------------------

Evaluation Criteria
~~~~~~~~~~~~~~~~~~~

**Functionality**
    Does it do what you need? How well?

**Reliability**
    Uptime, error rates, support quality.

**Security**
    Data handling, encryption, compliance certifications.

**Performance**
    Latency, throughput, rate limits.

**Cost**
    Pricing model, cost at your scale.

**Lock-in**
    How hard to switch? Are there alternatives?

Embedded vs Dispatched Decision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Choose embedded when:**

- Data sensitivity prohibits external transfer
- You need full control over processing
- Performance requires in-process execution
- Cost of external services is prohibitive
- You have expertise to operate the functionality

**Choose dispatched when:**

- Functionality is complex/specialized (AI)
- Vendor has superior capabilities
- Operational burden should be outsourced
- Pay-per-use economics are favorable
- Compliance requires separation of concerns

Common Third-Party Integrations
-------------------------------

AI/LLM Providers
~~~~~~~~~~~~~~~~

::

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

**Third-party modules extend Julee solutions with external functionality.**

**Two integration modes:**

- **Embedded:** Import and run in your process. You are the actor.
- **Dispatched:** Call over network. They are a supply chain actor.

**Integration patterns:**

- Protocol-based: Hide details behind interfaces
- Adapter: Wrap their API to match your protocols
- Factory: Select implementation by configuration

**Supply chain implications:**

- Embedded: Data stays in your control
- Dispatched: Data flows to external parties
- Both: Need appropriate compliance handling

For embedded vs dispatched decisions, see :doc:`modules`.

For batteries-included modules, see :doc:`batteries-included`.
