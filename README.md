# Julee

Clean architecture for accountable and transparent digital supply chains.

Julee is a Python framework for building resilient, auditable business processes using Temporal workflows. Solutions are organized around your business domain—your bounded contexts become "accelerators" that speak your business language, not framework jargon.

**Use Julee when:** processes must be done correctly, may be complex or long-running, need compliance audit trails (responsible AI, algorithmic due-diligence), or depend on unreliable services that may fail, timeout, or be rate-limited.

**Core concepts:** Accelerators are collections of pipelines that automate a business area. Pipelines are use cases wrapped with Temporal, providing durability (survives crashes), reliability (automatic retries), observability (complete execution history), and supply chain provenance (audit trails that become "digital product passports").

## Installation

```bash
pip install julee
```

## Runtime Dependencies

Julee applications require: [Temporal](https://temporal.io/) (workflow orchestration), S3-compatible object storage (e.g. MinIO), PostgreSQL (for Temporal).

## Documentation

Full documentation: https://github.com/pyx-industries/julee (see `docs/`)

- [Architecture](docs/architecture/framework.rst) — framework philosophy and patterns
- [Solutions](docs/architecture/solutions/index.rst) — organizing code around business domains
- [Clean Architecture](docs/architecture/clean_architecture/index.rst) — entities, use cases, repositories, services
- [Contributing](docs/contributing.rst) — development setup and guidelines

## Example

This repository includes a Docker Compose example demonstrating a meeting minutes extraction system. See the `demo-ui/` directory and run `docker compose up --build` to explore.

## License

GPL-3.0 — see [LICENSE](LICENSE) for details.
