APIs
====

API applications expose Julee use cases via REST endpoints using FastAPI.

APIs execute use cases directly for synchronous operations, or trigger pipelines via Temporal client for asynchronous operations. Use cases receive dependencies (repositories, services) via FastAPI's dependency injection. Request and response models are Pydantic models separate from domain models, providing API contracts that can evolve independently.
