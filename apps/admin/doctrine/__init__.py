"""Admin CLI app instance doctrine.

This package contains doctrine tests specific to the admin CLI application.
These tests supplement (not replace) the core doctrine and CLI app-type doctrine.

Doctrine hierarchy:
1. Core Doctrine - applies to all code (entities, use cases, etc.)
2. App Type Doctrine - applies to all apps of a type (CLI, REST-API, etc.)
3. App Instance Doctrine - applies to this specific app (admin)

The admin CLI is the primary tool for introspecting and managing julee solutions.
Its instance doctrine ensures it provides adequate coverage of core entities.
"""
