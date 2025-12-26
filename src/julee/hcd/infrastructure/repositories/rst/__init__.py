"""RST file-backed repository implementations.

Provides repository implementations that use RST files as a database backend.
Supports lossless round-trip: RST → Domain Entity → RST.

Usage:
    from pathlib import Path
    from julee.hcd.infrastructure.repositories.rst import create_rst_repositories

    repos = create_rst_repositories(Path("docs/hcd"))
    journeys = await repos["journey"].list_all()
"""
