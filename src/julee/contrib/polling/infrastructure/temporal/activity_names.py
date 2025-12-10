"""
Activity name constants for the polling contrib module.

This module contains activity name base constants specific to the polling
contrib module. These constants are used for registering polling activities
and calling them from workflow proxies.

By keeping these constants within the contrib module, we maintain proper
dependency direction - contrib modules define their own temporal integration
without requiring the core framework to know about specific contrib modules.
"""

# Activity name base for polling service activities
POLLING_SERVICE_ACTIVITY_BASE = "julee.contrib.polling"


# Export all constants
__all__ = [
    "POLLING_SERVICE_ACTIVITY_BASE",
]
