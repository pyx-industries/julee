# Polling Contrib Module

The polling module provides endpoint polling with automatic change detection. Use it to monitor HTTP endpoints and trigger downstream pipelines when new data is detected.

## Quick Start

```python
from julee.contrib.polling.entities.polling_config import PollingConfig, PollingProtocol
from julee.contrib.polling.infrastructure.temporal.manager import PollingManager

# Create manager with your Temporal client
manager = PollingManager(temporal_client)

# Configure what to poll
config = PollingConfig(
    endpoint_identifier="my-api",
    polling_protocol=PollingProtocol.HTTP,
    connection_params={"url": "https://api.example.com/data"},
    timeout_seconds=30,
)

# Start polling every 60 seconds
await manager.start_polling("my-api", config, interval_seconds=60)
```

## How It Works

1. **Polling**: The `NewDataDetectionPipeline` polls your endpoint at the configured interval
2. **Change Detection**: Content is hashed and compared to the previous poll
3. **Routing**: When new data is detected, matching routes dispatch to downstream pipelines
4. **Durability**: Temporal provides retries, state persistence, and exactly-once execution

## Configuring Downstream Routing

Routes are configured at application startup via the `pipeline_routing_registry`. When new data is detected (`has_new_data=True`), matching routes trigger downstream pipelines.

### 1. Define Your Routes

```python
# my_solution/routes.py
from julee.shared.domain.models.pipeline_route import PipelineRoute, PipelineCondition

polling_routes = [
    PipelineRoute(
        response_type="NewDataDetectionResponse",
        condition=PipelineCondition.is_true("has_new_data"),
        pipeline="DocumentProcessingPipeline",
        request_type="ProcessDocumentRequest",
        description="Process new data when detected",
    ),
    PipelineRoute(
        response_type="NewDataDetectionResponse",
        condition=PipelineCondition.is_not_none("error"),
        pipeline="ErrorNotificationPipeline",
        request_type="NotifyErrorRequest",
        description="Notify on polling errors",
    ),
]
```

### 2. Define Your Transformers

Transformers convert the polling response into the request format your downstream pipeline expects:

```python
# my_solution/transformers.py
from julee.contrib.polling.use_cases import NewDataDetectionResponse

def polling_to_document_request(response: dict) -> ProcessDocumentRequest:
    """Transform polling response to document processing request."""
    return ProcessDocumentRequest(
        content=response["content"],
        source_id=response["endpoint_id"],
        content_hash=response["content_hash"],
    )

def polling_to_error_request(response: dict) -> NotifyErrorRequest:
    """Transform polling response to error notification request."""
    return NotifyErrorRequest(
        source="polling",
        endpoint_id=response["endpoint_id"],
        error=response["error"],
    )
```

### 3. Register at Startup

Register routes and transformers before starting your Temporal worker:

```python
# my_solution/worker.py
from julee.shared.infrastructure.pipeline_routing import pipeline_routing_registry
from my_solution.routes import polling_routes
from my_solution.transformers import (
    polling_to_document_request,
    polling_to_error_request,
)

def configure_routing():
    """Configure pipeline routing for the worker."""
    pipeline_routing_registry.register_routes(polling_routes)

    pipeline_routing_registry.register_transformer(
        "NewDataDetectionResponse",
        "ProcessDocumentRequest",
        polling_to_document_request,
    )

    pipeline_routing_registry.register_transformer(
        "NewDataDetectionResponse",
        "NotifyErrorRequest",
        polling_to_error_request,
    )

# Call before starting worker
configure_routing()
```

## Response Structure

The `NewDataDetectionResponse` contains:

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether polling succeeded |
| `content` | `bytes` | Raw content from endpoint |
| `content_hash` | `str` | SHA-256 hash of content |
| `polled_at` | `datetime` | When the poll occurred |
| `endpoint_id` | `str` | Identifier for the endpoint |
| `has_new_data` | `bool` | True if content changed |
| `is_first_poll` | `bool` | True if no previous hash |
| `previous_hash` | `str \| None` | Hash from previous poll |
| `error` | `str \| None` | Error message if failed |
| `dispatches` | `list` | Records of downstream dispatches |

### Computed Properties

- `should_process`: True when `has_new_data` and `success`
- `has_error`: True when `error` is not None

## Route Conditions

Use conditions to control when routes match:

```python
# Match when has_new_data is True
PipelineCondition.is_true("has_new_data")

# Match when error is not None
PipelineCondition.is_not_none("error")

# Match when success is False
PipelineCondition.is_false("success")

# Complex conditions (all must match)
PipelineCondition(all_of=[
    PipelineFieldCondition(field="has_new_data", operator=PipelineOperator.IS_TRUE),
    PipelineFieldCondition(field="success", operator=PipelineOperator.IS_TRUE),
])
```

## Manager Operations

```python
# Start polling
schedule_id = await manager.start_polling("endpoint-id", config, 60)

# Pause polling (keeps schedule)
await manager.pause_polling("endpoint-id")

# Resume polling
await manager.resume_polling("endpoint-id")

# Stop polling (deletes schedule)
await manager.stop_polling("endpoint-id")

# List active polls
active = await manager.list_active_polling()

# Get status
status = await manager.get_polling_status("endpoint-id")
```

## Worker Setup

Register the pipeline with your Temporal worker:

```python
from temporalio.worker import Worker
from julee.contrib.polling.apps.worker.pipelines import NewDataDetectionPipeline
from julee.contrib.polling.infrastructure.temporal.activities import poll_endpoint

worker = Worker(
    client,
    task_queue="julee-polling-queue",
    workflows=[NewDataDetectionPipeline],
    activities=[poll_endpoint],
)
```

## Custom Task Queue

Use a custom task queue if needed:

```python
manager = PollingManager(temporal_client, task_queue="my-polling-queue")
```

Make sure your worker listens on the same queue.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Temporal Schedule                            │
│                   (interval: 60 seconds)                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 NewDataDetectionPipeline                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              NewDataDetectionUseCase                      │   │
│  │  • Poll endpoint via PollerService                        │   │
│  │  • Compute content hash                                   │   │
│  │  • Compare with previous hash                             │   │
│  │  • Return NewDataDetectionResponse                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      run_next()                           │   │
│  │  • Query pipeline_routing_registry for matching routes    │   │
│  │  • Transform response to downstream requests              │   │
│  │  • Execute child workflows in parallel                    │   │
│  │  • Record dispatches in response                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │ Downstream  │  │ Downstream  │  │ Downstream  │
    │ Pipeline A  │  │ Pipeline B  │  │ Pipeline C  │
    └─────────────┘  └─────────────┘  └─────────────┘
```

## See Also

- `julee.shared.infrastructure.pipeline_routing` - Pipeline routing infrastructure
- `julee.shared.domain.models.pipeline_route` - PipelineRoute and PipelineCondition models
- `docs/architecture/proposals/pipeline_router_design.md` - Design documentation
