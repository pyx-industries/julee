Installation
============

Prerequisites
-------------

- Python 3.10 or higher
- Docker and Docker Compose
- API keys for knowledge services

Development Installation
-------------------------

1. Clone the repository::

    git clone <repository-url>
    cd julee

2. Create a virtual environment::

    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

3. Install dependencies::

    # Install all dependencies including dev and docs
    pip install -e ".[dev,docs]"

    # Or just core dependencies
    pip install -e .

4. Set up environment variables::

    cp .env.example .env
    # Edit .env and add your API keys

Docker Installation
-------------------

The easiest way to run Julee is using Docker Compose::

    docker-compose --profile julee up --build -d

This will start all required services:

- FastAPI server (port 8000)
- React UI (port 3000)
- Temporal worker
- Temporal server (port 7233)
- MinIO storage (port 9000)
- PostgreSQL database

Verifying Installation
----------------------

Once running, access:

- **Web UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Temporal UI**: http://localhost:8001
- **MinIO Console**: http://localhost:9001

Configuration
-------------

See :doc:`configuration` for detailed configuration options.
