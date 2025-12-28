APIs
====

API applications expose Julee :py:class:`use cases <julee.core.entities.use_case.UseCase>` via REST endpoints using FastAPI.

APIs execute use cases directly for synchronous operations, or trigger :doc:`worker <worker>` :doc:`pipelines </architecture/solutions/pipelines>` via Temporal client for asynchronous operations. Use cases receive dependencies (:py:class:`repositories <julee.core.entities.repository_protocol.RepositoryProtocol>`, :py:class:`services <julee.core.entities.service_protocol.ServiceProtocol>`) via FastAPI's dependency injection. Request and response models are Pydantic models separate from :py:class:`domain models <julee.core.entities.entity.Entity>`, providing API contracts that can evolve independently.

:doc:`UIs <ui>` interact with the system exclusively through the API. :doc:`CLIs <cli>` can also call APIs, though they more commonly invoke use cases directly.
