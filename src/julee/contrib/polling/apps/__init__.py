"""
Application entry points for the polling contrib module.

This module contains the application-layer components that provide entry points
for the polling contrib module, including worker pipelines, API routes, and
CLI commands.

Following the ADR contrib module structure, this layer wires together domain
services and infrastructure implementations into runnable applications.

No re-exports to avoid import chains that pull non-deterministic code
into Temporal workflows. Import directly from specific modules:

- from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
"""
