"""
Standalone CEAP Temporal worker entry point.

This module provides a standalone worker process for CEAP (Content Extraction
and Assembly Pipeline) operations. It is a complete reference implementation
demonstrating how to use the CEAP contrib module with Temporal.

Usage:
    python -m julee.contrib.ceap.apps.worker.main

Environment Variables:
    TEMPORAL_ENDPOINT: Temporal server address (default: localhost:7234)
    MINIO_ENDPOINT: MinIO server address (default: localhost:9000)
    MINIO_ACCESS_KEY: MinIO access key (default: minioadmin)
    MINIO_SECRET_KEY: MinIO secret key (default: minioadmin)
    LOG_LEVEL: Logging level (default: INFO)
    LOG_FORMAT: Logging format string
"""

import asyncio
import logging
import os
from typing import Any

from minio import Minio
from temporalio.client import Client
from temporalio.service import RPCError
from temporalio.worker import Worker

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
from julee.core.infrastructure.repositories.minio.client import MinioClient
from julee.core.infrastructure.temporal.activities import (
    collect_activities_from_instances,
)
from julee.core.infrastructure.temporal.data_converter import temporal_data_converter

from . import TASK_QUEUE, get_workflow_classes

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging based on environment variables."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_format = os.environ.get(
        "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}, defaulting to INFO")
        numeric_level = logging.INFO

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        force=True,  # Override any existing configuration
    )

    logger.info(
        "Logging configured",
        extra={"log_level": log_level, "numeric_level": numeric_level},
    )


async def get_temporal_client_with_retries(
    endpoint: str, attempts: int = 10, delay: int = 5
) -> Client:
    """Attempt to connect to Temporal with retries.

    Args:
        endpoint: Temporal server address.
        attempts: Maximum number of connection attempts.
        delay: Delay in seconds between retry attempts.

    Returns:
        Connected Temporal client.

    Raises:
        RuntimeError: If all connection attempts fail.
    """
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
            # Use the proper Pydantic v2 data converter and connect to the
            # 'default' namespace
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

    # This should never be reached due to the raise in the loop, but mypy
    # needs it
    raise RuntimeError("Failed to connect to Temporal after all attempts")


class CeapWorkerDependencyContainer:
    """
    Dependency injection container for standalone CEAP worker.

    This container manages singleton lifecycle for infrastructure dependencies
    and provides factory methods for creating activity instances. It follows
    the same pattern as apps/api/ceap/dependencies.py.
    """

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}

    def get_minio_client(self) -> MinioClient:
        """Get or create MinIO client singleton."""
        if "minio_client" not in self._instances:
            minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
            minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
            minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

            logger.debug(
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

    def create_activity_instances(self) -> list[Any]:
        """Create all CEAP activity instances with proper DI wiring.

        Returns:
            List of activity instances ready for Temporal worker registration.
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


async def run_worker() -> None:
    """Run the standalone CEAP Temporal worker.

    This function initializes and runs a Temporal worker that handles
    CEAP pipelines (ExtractAssemblePipeline, ValidateDocumentPipeline)
    and their associated activities.
    """
    # Setup logging first
    setup_logging()

    # Connect to Temporal server using environment variable
    temporal_endpoint = os.environ.get("TEMPORAL_ENDPOINT", "localhost:7234")
    logger.info(
        "Starting CEAP Temporal worker",
        extra={"temporal_endpoint": temporal_endpoint, "task_queue": TASK_QUEUE},
    )

    client = await get_temporal_client_with_retries(temporal_endpoint)

    # Create DI container and get activity instances
    container = CeapWorkerDependencyContainer()
    activity_instances = container.create_activity_instances()

    # Automatically collect all activities from decorated instances
    activities = collect_activities_from_instances(*activity_instances)

    # Get workflow classes
    workflows = get_workflow_classes()

    logger.info(
        "Creating Temporal worker for CEAP domain",
        extra={
            "task_queue": TASK_QUEUE,
            "workflow_count": len(workflows),
            "activity_count": len(activities),
            "data_converter_type": type(client.data_converter).__name__,
        },
    )

    # Create worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=workflows,
        activities=activities,  # type: ignore[arg-type]
    )

    logger.info("Starting CEAP worker execution")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
