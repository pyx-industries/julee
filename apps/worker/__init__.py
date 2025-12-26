"""
Composite Temporal worker for julee framework.

This module provides a composite worker that handles workflows from all contrib
modules on a single task queue (julee-worker-queue). It is a true composition -
the worker has its own identity and composes functionality from contrib modules.

The composite worker imports workflow classes from:
- julee.contrib.ceap.apps.worker (CEAP document operations)
- julee.contrib.polling.apps.worker (Polling operations)

And uses its own DependencyContainer to wire all activities.

For production deployments requiring independent scaling and failure isolation,
use the standalone workers instead:
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

from .main import TASK_QUEUE

__all__ = ["TASK_QUEUE"]
