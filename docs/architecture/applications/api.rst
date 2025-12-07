APIs
====

API applications expose Julee :doc:`use cases </architecture/clean_architecture/use_cases>` via REST endpoints using FastAPI.

APIs execute use cases directly for synchronous operations, or trigger :doc:`worker <worker>` pipelines via Temporal client for asynchronous operations. Use cases receive dependencies (repositories, services) via FastAPI's dependency injection. Request and response models are Pydantic models separate from domain models, providing API contracts that can evolve independently.

:doc:`UIs <ui>` interact with the system exclusively through the API. :doc:`CLIs <cli>` can also call APIs, though they more commonly invoke use cases directly.
