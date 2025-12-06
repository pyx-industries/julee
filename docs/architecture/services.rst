Services
========

**Canonical Definition: Services do things.**

A service performs complex operations beyond simple persistence. Services often delegate to external actors in the digital supply chain.

This is the single source of truth for the service pattern in Julee.

What is a Service?
------------------

A service is responsible for complex operations that don't fit the CRUD pattern.

**Responsibilities:**

- AI/LLM operations (extraction, generation, classification)
- External API integration (email, payment, notification)
- Complex business logic requiring external resources
- Operations coordinating multiple systems

**Not responsibilities:**

- Simple CRUD persistence (use a repository)
- Domain rules (use a use case)
- Workflow orchestration (use Temporal workflows)

**Key distinction:** Services handle *operations beyond storage*.

For simple persistence, see :doc:`repositories`.

When to Use a Service
---------------------

Create a service when you need to:

**Integrate AI/LLMs**
    Extract data from documents, generate content, classify text, answer questions.

**Call External APIs**
    Send emails, process payments, validate addresses, fetch external data.

**Perform Complex Computations**
    Heavy processing, data transformations, complex analysis requiring specialized tools.

**Coordinate with Supply Chain Actors**
    Any operation delegated to third-party providers or self-hosted services.

When NOT to Use a Service
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Don't create services for:**

- Storing and retrieving entities (use a repository)
- Domain validation rules (use domain models)
- Workflow orchestration (use Temporal workflows)
- Simple transformations (use use cases)

Services as Supply Chain Actors
--------------------------------

Services represent **supply chain actors** in your digital product supply chain.

Three Types of Services
~~~~~~~~~~~~~~~~~~~~~~~

**1. Third-Party APIs**
    External services you depend on:

    - **AI Providers**: Anthropic, OpenAI, Cohere
    - **Communication**: SendGrid, Twilio, Mailgun
    - **Infrastructure**: Stripe, Auth0, DataDog
    - **Data**: Google Maps, Weather APIs

    You don't control these. They're supply chain dependencies.

**2. Self-Hosted Services**
    Services you deploy and operate:

    - **Local LLMs**: Ollama, LM Studio, vLLM
    - **Custom processors**: Document parsers, image processors
    - **Internal APIs**: Authentication services, data services

    You control deployment, but they're still separate services.

**3. Bundled Services**
    Custom logic deployed with your application:

    - **Business logic services**: Complex calculations, validations
    - **Integration adapters**: Wrappers for external APIs

    Part of your deployment, but architected as services.

What is NOT a Service
~~~~~~~~~~~~~~~~~~~~~

**Infrastructure components:**

- **MinIO/S3**: Storage backend (repository implementation)
- **PostgreSQL**: Database (repository implementation)
- **Temporal**: Workflow orchestration (infrastructure)
- **Redis**: Cache (infrastructure component)

These are infrastructure, not services.

The Service Protocol
--------------------

**The canonical protocol for AI services.**

The primary service in Julee is ``KnowledgeService`` for AI operations::

    from typing import Protocol

    class KnowledgeService(Protocol):
        """Protocol for AI knowledge extraction services.

        Knowledge services handle AI/LLM operations for extracting
        structured data from documents.
        """

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Register content with the service.

            Args:
                content: File content bytes
                content_type: MIME type (e.g., "application/pdf")

            Returns:
                File identifier for use in queries

            Raises:
                ServiceError: If registration fails
            """
            ...

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query the service with a prompt.

            Args:
                file_id: File identifier from register_file
                prompt: Natural language prompt
                response_schema: Optional JSON schema for structured output

            Returns:
                Structured data extracted from the file

            Raises:
                ServiceError: If query fails
            """
            ...

**Protocol variations:**

Different services have different operations. Create protocols that match your needs::

    class ValidationService(Protocol):
        """Protocol for document validation."""

        async def validate(
            self,
            document: Document,
            policy: Policy
        ) -> ValidationResult:
            """Validate document against policy."""
            ...

    class NotificationService(Protocol):
        """Protocol for sending notifications."""

        async def send_email(
            self,
            to: str,
            subject: str,
            body: str
        ) -> None:
            """Send email notification."""
            ...

        async def send_sms(
            self,
            to: str,
            message: str
        ) -> None:
            """Send SMS notification."""
            ...

Service Implementations
-----------------------

Anthropic Knowledge Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Claude AI integration for document processing::

    from anthropic import Anthropic, AsyncAnthropic
    from domain.models import Document

    class AnthropicKnowledgeService:
        """Anthropic Claude implementation of KnowledgeService.

        Uses Claude for AI-powered knowledge extraction.
        """

        def __init__(
            self,
            api_key: str,
            model: str = "claude-3-5-sonnet-20241022"
        ):
            self.client = AsyncAnthropic(api_key=api_key)
            self.model = model

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Register file with Anthropic.

            Returns a pseudo-ID since Anthropic doesn't have file storage.
            Content will be sent with each query.
            """
            # Store content temporarily or return reference
            import hashlib
            file_id = hashlib.sha256(content).hexdigest()
            self._files[file_id] = content
            return file_id

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query Claude with document content."""
            content = self._files.get(file_id)
            if not content:
                raise ValueError(f"File {file_id} not found")

            # Call Claude API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": base64.b64encode(content).decode()
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            # Extract and parse response
            response_text = message.content[0].text

            if response_schema:
                # Parse structured response
                return json.loads(response_text)
            else:
                return {"text": response_text}

**When to use:** Production AI extraction with Claude.

OpenAI Knowledge Service
~~~~~~~~~~~~~~~~~~~~~~~~~

GPT integration for document processing::

    from openai import AsyncOpenAI

    class OpenAIKnowledgeService:
        """OpenAI GPT implementation of KnowledgeService."""

        def __init__(
            self,
            api_key: str,
            model: str = "gpt-4o"
        ):
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Upload file to OpenAI."""
            file_response = await self.client.files.create(
                file=content,
                purpose="assistants"
            )
            return file_response.id

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query GPT with file content."""
            # Create assistant with file access
            assistant = await self.client.beta.assistants.create(
                model=self.model,
                tools=[{"type": "file_search"}],
                file_ids=[file_id]
            )

            # Create thread and run
            thread = await self.client.beta.threads.create()
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )

            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )

            # Wait for completion and get response
            # ... (implementation details)

            if response_schema:
                return json.loads(response_text)
            else:
                return {"text": response_text}

**When to use:** When you prefer OpenAI's GPT models.

Local LLM Service
~~~~~~~~~~~~~~~~~

Self-hosted LLM for cost control and privacy::

    import httpx

    class LocalLLMService:
        """Local LLM implementation (Ollama, LM Studio, etc.).

        Uses a self-hosted LLM via HTTP API.
        """

        def __init__(
            self,
            endpoint: str = "http://localhost:11434",
            model: str = "llama2"
        ):
            self.endpoint = endpoint
            self.model = model
            self.client = httpx.AsyncClient()

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Store file content for later queries."""
            file_id = str(uuid.uuid4())
            self._files[file_id] = content.decode('utf-8')
            return file_id

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query local LLM."""
            content = self._files.get(file_id)
            if not content:
                raise ValueError(f"File {file_id} not found")

            # Construct prompt with file content
            full_prompt = f"""Document:
            {content}

            {prompt}

            Respond in JSON format.
            """

            # Call local LLM API
            response = await self.client.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                }
            )

            result = response.json()
            response_text = result["response"]

            if response_schema:
                return json.loads(response_text)
            else:
                return {"text": response_text}

**When to use:** Cost optimization, data privacy, offline operation.

Memory Knowledge Service
~~~~~~~~~~~~~~~~~~~~~~~~~

Fast mock for testing::

    class MemoryKnowledgeService:
        """In-memory mock implementation of KnowledgeService.

        Returns predictable mock data for testing.
        """

        def __init__(self):
            self._responses = {}

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Return mock file ID."""
            return "mock-file-id"

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Return mock response."""
            # Check for programmed response
            if prompt in self._responses:
                return self._responses[prompt]

            # Default mock response
            if response_schema:
                # Return empty data matching schema
                return {key: None for key in response_schema.get("properties", {})}
            else:
                return {"text": "Mock response"}

        def program_response(self, prompt: str, response: dict):
            """Program specific response for testing."""
            self._responses[prompt] = response

**When to use:** Unit tests, CI/CD pipelines, development.

Using Services
--------------

In Use Cases
~~~~~~~~~~~~

Use cases depend on service protocols::

    from domain.services.knowledge import KnowledgeService
    from domain.repositories.document import DocumentRepository

    class ExtractDataUseCase:
        def __init__(
            self,
            doc_repo: DocumentRepository,
            knowledge: KnowledgeService
        ):
            self.doc_repo = doc_repo
            self.knowledge = knowledge

        async def execute(self, doc_id: str, prompt: str) -> dict:
            # Get document from repository
            doc = await self.doc_repo.get(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Register with AI service
            file_id = await self.knowledge.register_file(
                doc.content,
                doc.content_type
            )

            # Query AI service
            result = await self.knowledge.query(
                file_id,
                prompt
            )

            return result

The use case has no knowledge of which AI provider is being used.

In API Endpoints
~~~~~~~~~~~~~~~~

Inject services via dependency injection::

    from fastapi import APIRouter, Depends
    from domain.services.knowledge import KnowledgeService
    from infrastructure.dependencies import get_knowledge_service

    router = APIRouter()

    @router.post("/extract")
    async def extract_data(
        file: UploadFile,
        prompt: str,
        knowledge: KnowledgeService = Depends(get_knowledge_service)
    ) -> dict:
        """Extract data from uploaded file."""
        content = await file.read()

        file_id = await knowledge.register_file(
            content,
            file.content_type
        )

        result = await knowledge.query(file_id, prompt)

        return result

See :doc:`protocols` for dependency injection details.

Testing with Services
---------------------

Unit Tests
~~~~~~~~~~

Use mock services for fast tests::

    import pytest
    from infrastructure.services.memory_knowledge import MemoryKnowledgeService
    from domain.use_cases.extract_data import ExtractDataUseCase

    @pytest.mark.asyncio
    async def test_extract_data():
        # Create mock service
        knowledge = MemoryKnowledgeService()

        # Program expected response
        knowledge.program_response(
            "Extract the title",
            {"title": "Test Document"}
        )

        # Create use case with mock
        use_case = ExtractDataUseCase(
            doc_repo=mock_repo,
            knowledge=knowledge
        )

        # Test
        result = await use_case.execute("doc-1", "Extract the title")

        # Verify
        assert result["title"] == "Test Document"

**Benefits:**

- No external API calls
- Fast execution
- Deterministic results
- No API costs

Integration Tests
~~~~~~~~~~~~~~~~~

Test with real services::

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_anthropic_extraction():
        # Use real Anthropic service
        knowledge = AnthropicKnowledgeService(
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )

        # Register test file
        with open("test_document.pdf", "rb") as f:
            content = f.read()

        file_id = await knowledge.register_file(
            content,
            "application/pdf"
        )

        # Query
        result = await knowledge.query(
            file_id,
            "Extract the document title"
        )

        # Verify structure (not exact content)
        assert "title" in result
        assert isinstance(result["title"], str)

**Benefits:**

- Verifies actual AI behavior
- Tests API integration
- Catches service-specific issues

Comparing Providers
~~~~~~~~~~~~~~~~~~~

Test multiple providers with same interface::

    @pytest.mark.parametrize("service_class", [
        AnthropicKnowledgeService,
        OpenAIKnowledgeService,
        LocalLLMService
    ])
    @pytest.mark.asyncio
    async def test_knowledge_service(service_class):
        """Test all providers with same test."""
        service = create_service(service_class)

        file_id = await service.register_file(
            test_content,
            "application/pdf"
        )

        result = await service.query(
            file_id,
            "Extract title and author"
        )

        # Verify structure is consistent
        assert "title" in result
        assert "author" in result

Common Patterns
---------------

Pattern: Retry Logic
~~~~~~~~~~~~~~~~~~~~

Handle service failures gracefully::

    from tenacity import retry, stop_after_attempt, wait_exponential

    class ResilientKnowledgeService:
        """Wrapper adding retry logic to any knowledge service."""

        def __init__(self, service: KnowledgeService):
            self.service = service

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Register with retries."""
            return await self._register_with_retry(content, content_type)

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        async def _register_with_retry(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            return await self.service.register_file(content, content_type)

        async def query(self, file_id: str, prompt: str) -> dict:
            """Query with retries."""
            return await self._query_with_retry(file_id, prompt)

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        async def _query_with_retry(
            self,
            file_id: str,
            prompt: str
        ) -> dict:
            return await self.service.query(file_id, prompt)

Pattern: Caching Service
~~~~~~~~~~~~~~~~~~~~~~~~~

Cache expensive service calls::

    from functools import lru_cache
    import hashlib

    class CachedKnowledgeService:
        """Wrapper adding caching to knowledge service."""

        def __init__(self, service: KnowledgeService):
            self.service = service
            self._cache: dict[str, dict] = {}

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Register (no caching for file registration)."""
            return await self.service.register_file(content, content_type)

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query with caching."""
            # Create cache key
            cache_key = f"{file_id}:{hashlib.sha256(prompt.encode()).hexdigest()}"

            # Check cache
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Call service
            result = await self.service.query(file_id, prompt, response_schema)

            # Cache result
            self._cache[cache_key] = result

            return result

Pattern: Fallback Service
~~~~~~~~~~~~~~~~~~~~~~~~~~

Try multiple services in sequence::

    class FallbackKnowledgeService:
        """Try multiple services, fall back if primary fails."""

        def __init__(
            self,
            primary: KnowledgeService,
            fallback: KnowledgeService
        ):
            self.primary = primary
            self.fallback = fallback

        async def register_file(
            self,
            content: bytes,
            content_type: str
        ) -> str:
            """Register with primary, fall back if it fails."""
            try:
                return await self.primary.register_file(content, content_type)
            except Exception:
                return await self.fallback.register_file(content, content_type)

        async def query(
            self,
            file_id: str,
            prompt: str,
            response_schema: dict | None = None
        ) -> dict:
            """Query with fallback."""
            try:
                return await self.primary.query(file_id, prompt, response_schema)
            except Exception:
                return await self.fallback.query(file_id, prompt, response_schema)

Common Mistakes
---------------

Mistake 1: Service Doing Persistence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class KnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            result = await self.call_ai_api(file_id, prompt)

            # Service storing results ❌
            await self.db.save_result(result)

            return result

**Right:**

::

    # Service returns result ✓
    class KnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            return await self.call_ai_api(file_id, prompt)

    # Use case handles persistence ✓
    class ExtractDataUseCase:
        async def execute(self, file_id: str, prompt: str):
            result = await self.knowledge.query(file_id, prompt)

            # Use case stores via repository
            await self.result_repo.create(result)

Mistake 2: Business Logic in Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class KnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            result = await self.call_ai_api(file_id, prompt)

            # Business rule in service ❌
            if result["confidence"] < 0.8:
                raise ValueError("Confidence too low")

            return result

**Right:**

::

    # Service returns raw result ✓
    class KnowledgeService:
        async def query(self, file_id: str, prompt: str) -> dict:
            return await self.call_ai_api(file_id, prompt)

    # Use case implements business rule ✓
    class ExtractDataUseCase:
        async def execute(self, file_id: str, prompt: str):
            result = await self.knowledge.query(file_id, prompt)

            if result["confidence"] < 0.8:
                raise ValueError("Confidence too low")

            return result

Mistake 3: Service Calling Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Wrong:**

::

    class ValidationService:
        def __init__(self, knowledge: KnowledgeService):
            self.knowledge = knowledge

        async def validate(self, doc: Document) -> bool:
            # Service calling service ❌
            result = await self.knowledge.query(doc.file_id, "Validate")
            return result["is_valid"]

**Right:**

::

    # Services stay independent ✓
    class ValidationService:
        async def validate(self, doc: Document, data: dict) -> bool:
            # Validate using provided data
            return self._check_rules(data)

    # Use case coordinates services ✓
    class ValidateDocumentUseCase:
        def __init__(
            self,
            knowledge: KnowledgeService,
            validator: ValidationService
        ):
            self.knowledge = knowledge
            self.validator = validator

        async def execute(self, doc: Document):
            # Extract data
            data = await self.knowledge.query(doc.file_id, "Extract")

            # Validate data
            is_valid = await self.validator.validate(doc, data)

            return is_valid

Summary
-------

**Services do things.**

Key principles:

**Complex Operations**
    Beyond CRUD - AI, external APIs, complex processing.

**Supply Chain Actors**
    Third-party APIs, self-hosted services, bundled logic.

**Protocol-Based**
    Domain defines protocol, infrastructure implements.

**No Persistence**
    Services operate, repositories persist.

**Multiple Implementations**
    Anthropic vs OpenAI vs local LLM - same protocol.

**Dependency Injection**
    Wire implementations at runtime.

For the repository pattern, see :doc:`repositories`.

For dependency injection, see :doc:`protocols`.

For layer organization, see :doc:`clean_architecture`.
