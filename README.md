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

Full documentation at [julee.readthedocs.io](https://julee.readthedocs.io), package on [PyPI](https://pypi.org/project/julee/).

## Example

This repository includes a Docker Compose example demonstrating a meeting minutes extraction system:

```bash
cp .env.example .env  # Add your ANTHROPIC_API_KEY
docker compose up --build
```

See the `demo-ui/` directory for the UI source.

## License

GPL-3.0 — see [LICENSE](LICENSE) for details.
