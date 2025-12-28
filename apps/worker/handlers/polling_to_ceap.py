"""Polling→CEAP bridge handler.

This handler bridges the Polling and CEAP bounded contexts. When Polling
detects new data, this handler captures it as a CEAP document.

The Polling module doesn't know about CEAP. It's injected with a handler
that happens to call CEAP. This is explicit cross-BC coordination, visible
in the solution's composition root. See ADR 003.
"""

import logging
from datetime import datetime, timezone
from io import BytesIO

from julee.contrib.ceap.entities.document import Document
from julee.contrib.ceap.repositories.document import DocumentRepository
from julee.core.entities.acknowledgement import Acknowledgement

logger = logging.getLogger(__name__)


class CeapDocumentCaptureHandler:
    """Handler that captures polled data as CEAP documents.

    This is a solution-specific handler that bridges Polling to CEAP.
    It implements the NewDataHandler protocol from polling.
    """

    def __init__(self, document_repo: DocumentRepository) -> None:
        """Initialize with CEAP document repository.

        Args:
            document_repo: Repository for storing captured documents.
        """
        self._document_repo = document_repo

    async def handle(
        self,
        endpoint_id: str,
        content: bytes,
        content_hash: str,
    ) -> Acknowledgement:
        """Capture polled content as a CEAP document.

        Args:
            endpoint_id: Identifier of the polled endpoint
            content: The new content that was detected
            content_hash: SHA256 hash of the content

        Returns:
            Acknowledgement indicating capture status.
        """
        logger.info(
            "Capturing polled data as CEAP document",
            extra={
                "endpoint_id": endpoint_id,
                "content_hash": content_hash[:8] + "...",
                "content_size": len(content),
            },
        )

        try:
            # Generate document ID
            document_id = await self._document_repo.generate_id()

            # Create document from polled content
            document = Document(
                document_id=document_id,
                content_stream=BytesIO(content),
                content_hash=content_hash,
                content_type="application/octet-stream",
                metadata={
                    "source": "polling",
                    "endpoint_id": endpoint_id,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Save to repository
            await self._document_repo.save(document)

            logger.info(
                "Successfully captured document",
                extra={
                    "document_id": document_id,
                    "endpoint_id": endpoint_id,
                },
            )

            return Acknowledgement.wilco(
                info=[f"Captured as document {document_id}"],
            )

        except Exception as e:
            logger.error(
                "Failed to capture document",
                extra={
                    "endpoint_id": endpoint_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            return Acknowledgement.roger(
                f"Failed to capture document: {e}",
                errors=[type(e).__name__],
            )
