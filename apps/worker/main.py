"""
Composite Temporal worker entry point.

This module provides a composite worker that handles workflows from multiple
contrib modules on a single task queue. It is a true composition - the worker
has its own identity (queue) and composes functionality from contrib modules.

For independent scaling and failure isolation, use the standalone workers:
- julee.contrib.ceap.apps.worker.main (julee-contrib-ceap-queue)
- julee.contrib.polling.apps.worker.main (julee-contrib-polling-queue)

Usage:
    python -m apps.worker.main

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

from temporalio.worker import Worker

from julee.contrib.ceap.apps.worker import get_workflow_classes as ceap_workflows
from julee.contrib.polling.apps.worker import get_workflow_classes as polling_workflows
from julee.core.infrastructure.temporal.activities import (
    collect_activities_from_instances,
)

from .dependencies import WorkerDependencyContainer

logger = logging.getLogger(__name__)

# Composite worker has its own queue identity
TASK_QUEUE = "julee-worker-queue"


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


async def run_worker() -> None:
    """Run the composite Temporal worker.

    This is a true composition: a single worker with its own queue that
    combines workflows and activities from all contrib modules. The DI
    container owns the wiring of all dependencies.

    For production deployments requiring independent scaling, use the
    standalone workers instead (each contrib has its own queue).
    """
    # Setup logging first
    setup_logging()

    logger.info(
        "Starting composite Temporal worker",
        extra={"task_queue": TASK_QUEUE},
    )

    # Create DI container - owns all dependency wiring
    container = WorkerDependencyContainer()

    # Get Temporal client
    client = await container.get_temporal_client()

    # Compose workflows from all contrib modules
    workflows = ceap_workflows() + polling_workflows()

    # Create all activity instances via DI container
    activity_instances = container.create_all_activity_instances()
    activities = collect_activities_from_instances(*activity_instances)

    logger.info(
        "Creating composite worker",
        extra={
            "task_queue": TASK_QUEUE,
            "workflow_count": len(workflows),
            "activity_count": len(activities),
            "data_converter_type": type(client.data_converter).__name__,
        },
    )

    # Single worker, single queue, composed functionality
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=workflows,
        activities=activities,  # type: ignore[arg-type]
    )

    logger.info("Starting composite worker execution")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
