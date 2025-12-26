"""
Dependency injection container for the composite worker.

This module provides a proper DependencyContainer for the composite worker,
following the same pattern as apps/api/ceap/dependencies.py. It manages
singleton lifecycle for infrastructure dependencies and provides factory
methods for creating activity instances from all contrib modules.
"""

import asyncio
import logging
import os
from typing import Any

from minio import Minio
from temporalio.client import Client
from temporalio.service import RPCError

from julee.contrib.ceap.infrastructure.temporal.repositories.activities import (
    TemporalMinioAssemblyRepository,
    TemporalMinioAssemblySpecificationRepository,
    TemporalMinioDocumentPolicyValidationRepository,
    TemporalMinioDocumentRepository,
    TemporalMinioKnowledgeServiceConfigRepository,
    TemporalMinioKnowledgeServiceQueryRepository,
    TemporalMinioPolicyRepository,
)
from julee.contrib.ceap.infrastructure.temporal.services.activities import (
    TemporalKnowledgeService,
)
from julee.contrib.polling.infrastructure.temporal.activities import (
    TemporalPollerService,
)
from julee.core.infrastructure.repositories.minio.client import MinioClient
from julee.core.infrastructure.temporal.data_converter import temporal_data_converter

logger = logging.getLogger(__name__)


class WorkerDependencyContainer:
    """
    Dependency injection container for the composite worker.

    This container manages singleton lifecycle for infrastructure dependencies
    and provides factory methods for creating activity instances. It follows
    the same pattern as apps/api/ceap/dependencies.py.

    The composite worker owns its own DI - it doesn't delegate to contrib
    modules for instantiation. Instead, it imports activity classes from
    contrib and wires them up with its own managed dependencies.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}

    def get_minio_client(self) -> MinioClient:
        """Get or create MinIO client singleton."""
        if "minio_client" not in self._instances:
            minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
            minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
            minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

            logger.info(
                "Creating MinIO client",
                extra={"endpoint": minio_endpoint},
            )

            # minio.Minio implements the MinioClient protocol
            self._instances["minio_client"] = Minio(
                endpoint=minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False,
            )

        return self._instances["minio_client"]  # type: ignore[return-value]

    async def get_temporal_client(
        self, attempts: int = 10, delay: int = 5
    ) -> Client:
        """Get or create Temporal client singleton with retries.

        Args:
            attempts: Maximum number of connection attempts.
            delay: Delay in seconds between retry attempts.

        Returns:
            Connected Temporal client.

        Raises:
            RuntimeError: If all connection attempts fail.
        """
        if "temporal_client" in self._instances:
            return self._instances["temporal_client"]  # type: ignore[return-value]

        endpoint = os.environ.get("TEMPORAL_ENDPOINT", "localhost:7234")

        logger.debug(
            "Attempting to connect to Temporal",
            extra={
                "endpoint": endpoint,
                "max_attempts": attempts,
                "delay_seconds": delay,
            },
        )

        for attempt in range(attempts):
            try:
                client = await Client.connect(
                    endpoint,
                    data_converter=temporal_data_converter,
                    namespace="default",
                )
                logger.info(
                    "Successfully connected to Temporal",
                    extra={
                        "endpoint": endpoint,
                        "attempt": attempt + 1,
                        "data_converter_type": type(client.data_converter).__name__,
                    },
                )
                self._instances["temporal_client"] = client
                return client
            except RPCError as e:
                logger.warning(
                    "Failed to connect to Temporal",
                    extra={
                        "endpoint": endpoint,
                        "attempt": attempt + 1,
                        "max_attempts": attempts,
                        "error": str(e),
                        "retry_in_seconds": delay,
                    },
                )
                if attempt + 1 == attempts:
                    logger.error(
                        "All connection attempts to Temporal failed",
                        extra={"endpoint": endpoint, "total_attempts": attempts},
                    )
                    raise
                await asyncio.sleep(delay)

        raise RuntimeError("Failed to connect to Temporal after all attempts")

    def create_ceap_activity_instances(self) -> list[Any]:
        """Create CEAP activity instances with proper DI wiring.

        The composite worker owns the DI for CEAP activities, wiring them
        with its managed MinIO client.

        Returns:
            List of CEAP activity instances.
        """
        minio = self.get_minio_client()

        # Create document repo first as it's needed by TemporalKnowledgeService
        document_repo = TemporalMinioDocumentRepository(client=minio)

        return [
            TemporalMinioAssemblyRepository(client=minio),
            TemporalMinioAssemblySpecificationRepository(client=minio),
            document_repo,
            TemporalMinioKnowledgeServiceConfigRepository(client=minio),
            TemporalMinioKnowledgeServiceQueryRepository(client=minio),
            TemporalMinioPolicyRepository(client=minio),
            TemporalMinioDocumentPolicyValidationRepository(client=minio),
            TemporalKnowledgeService(document_repo=document_repo),
        ]

    def create_polling_activity_instances(self) -> list[Any]:
        """Create polling activity instances.

        Polling activities are simpler - no MinIO dependencies required.

        Returns:
            List of polling activity instances.
        """
        return [
            TemporalPollerService(),
        ]

    def create_all_activity_instances(self) -> list[Any]:
        """Create all activity instances from all contrib modules.

        Returns:
            Combined list of all activity instances.
        """
        return (
            self.create_ceap_activity_instances() +
            self.create_polling_activity_instances()
        )
