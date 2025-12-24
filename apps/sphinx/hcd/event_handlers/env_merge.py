"""Environment merge handler for parallel builds.

When Sphinx runs with parallel_read_safe=True, each worker process gets
a copy of the environment. After workers finish, Sphinx calls env-merge-info
to merge worker data back into the main environment.
"""

import logging

logger = logging.getLogger(__name__)


def on_env_merge_info(app, env, docnames, other):
    """Merge HCD storage from worker environment into main environment.

    Called after each parallel read worker completes. Merges data from
    the worker's environment back into the main environment.

    Args:
        app: Sphinx application instance
        env: Main build environment (destination)
        docnames: Set of document names processed by this worker
        other: Worker's build environment (source)
    """
    # Ensure hcd_storage exists on both envs
    if not hasattr(other, "hcd_storage"):
        return  # Worker didn't add any HCD data

    if not hasattr(env, "hcd_storage"):
        env.hcd_storage = {}

    # Merge each entity type's storage
    for entity_key, other_storage in other.hcd_storage.items():
        if entity_key not in env.hcd_storage:
            env.hcd_storage[entity_key] = {}

        main_storage = env.hcd_storage[entity_key]

        # Only merge data from documents this worker processed
        for entity_id, data in other_storage.items():
            entity_docname = data.get("docname")
            if entity_docname in docnames:
                main_storage[entity_id] = data

    if other.hcd_storage:
        total_merged = sum(
            sum(1 for d in storage.values() if d.get("docname") in docnames)
            for storage in other.hcd_storage.values()
        )
        logger.debug(
            f"HCD: Merged {total_merged} entities from worker "
            f"({len(docnames)} docs)"
        )
