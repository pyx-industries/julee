"""Integrations with specific technologies.

Each subpackage connects julee to one third-party technology and holds no
domain concepts. Each has a matching extra, so a solution installs only
the integrations it uses: ``julee[temporal]``, ``julee[minio]``.

The kernel never imports from here. See docs/ADRs/012-framework-and-kits.md.
"""
