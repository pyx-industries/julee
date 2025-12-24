"""
Memory implementation of DocumentRepository.

This module provides an in-memory implementation of the DocumentRepository
protocol that follows the Clean Architecture patterns defined in the
Fun-Police Framework. It handles document storage with content and metadata
in memory dictionaries, ensuring idempotency and proper error handling.

The implementation uses Python dictionaries to store document data, making it
ideal for testing scenarios where external dependencies should be avoided.
All operations are still async to maintain interface compatibility.
"""

import hashlib
import io
import logging
from typing import Any

from julee.contrib.ceap.entities.document import Document
from julee.contrib.ceap.repositories.document import DocumentRepository
from julee.core.entities.content_stream import ContentStream
from julee.core.infrastructure.repositories.memory.base import MemoryRepositoryMixin

logger = logging.getLogger(__name__)


class MemoryDocumentRepository(DocumentRepository, MemoryRepositoryMixin[Document]):
    """
    Memory implementation of DocumentRepository using Python dictionaries.

    This implementation stores document metadata and content in memory:
    - Documents: Dictionary keyed by document_id containing Document objects

    This provides a lightweight, dependency-free option for testing while
    maintaining the same interface as other implementations.
    """

    def __init__(self) -> None:
        """Initialize repository with empty in-memory storage."""
        self.logger = logger
        self.entity_name = "Document"
        self.id_field = "document_id"
        self.storage: dict[str, Document] = {}

        logger.debug("Initializing MemoryDocumentRepository")

    async def get(self, document_id: str) -> Document | None:
        """Retrieve a document with metadata and content.

        Args:
            document_id: Unique document identifier

        Returns:
            Document object if found, None otherwise
        """
        return self._get_entity(document_id)

    async def save(self, document: Document) -> None:
        """Save a document with its content and metadata.

        If the document has content_bytes, it will be normalized to bytes
        (encoding str as UTF-8), converted to a ContentStream and the
        content hash will be calculated automatically.

        Args:
            document: Document object to save

        Raises:
            ValueError: If document has no content or content_bytes
            TypeError: If content_bytes is not bytes or str
        """
        # Handle content_string conversion (only if no content provided)
        if document.content_bytes is not None:
            if isinstance(document.content_bytes, str):
                raw_bytes = document.content_bytes.encode("utf-8")
            elif isinstance(document.content_bytes, bytes):
                raw_bytes = document.content_bytes
            else:
                raise TypeError("content_bytes must be of type 'bytes' or 'str'.")

            content_stream = ContentStream(io.BytesIO(raw_bytes))

            # Calculate content hash
            content_hash = hashlib.sha256(raw_bytes).hexdigest()

            # Create new document with ContentStream and calculated hash
            document = document.model_copy(
                update={
                    "content": content_stream,
                    "content_multihash": content_hash,
                    "size_bytes": len(raw_bytes),
                }
            )

            self.logger.debug(
                "Converted content_bytes to ContentStream for document save",
                extra={
                    "document_id": document.document_id,
                    "content_hash": content_hash,
                    "content_length": len(raw_bytes),
                },
            )

        # Create a copy without content_string (content saved
        # in separate content-addressable storage)
        document_for_storage = document.model_copy(update={"content_bytes": None})
        self._save_entity(document_for_storage)

    async def generate_id(self) -> str:
        """Generate a unique document identifier.

        Returns:
            Unique document ID string
        """
        return self._generate_id("doc")

    async def get_many(self, document_ids: list[str]) -> dict[str, Document | None]:
        """Retrieve multiple documents by ID.

        Args:
            document_ids: List of unique document identifiers

        Returns:
            Dict mapping document_id to Document (or None if not found)
        """
        return self._get_many_entities(document_ids)

    async def list_all(self) -> list[Document]:
        """List all documents.

        Returns:
            List of all Document entities in the repository
        """
        self.logger.debug(
            f"Memory{self.entity_name}Repository: Listing all "
            f"{self.entity_name.lower()}s"
        )

        documents = list(self.storage.values())

        self.logger.info(
            f"Memory{self.entity_name}Repository: Listed all "
            f"{self.entity_name.lower()}s",
            extra={"count": len(documents)},
        )

        return documents

    def _add_log_extras(self, entity: Document, log_data: dict[str, Any]) -> None:
        """Add document-specific data to log entries."""
        super()._add_log_extras(entity, log_data)
        log_data["content_length"] = entity.size_bytes
