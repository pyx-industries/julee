"""Env merge event handler for sphinx_supply_chain.

Handles parallel build merging for supply chain state.
"""


def on_env_merge_info(app, env, docnames, other):
    """Merge supply chain state from parallel builds.

    Args:
        app: Sphinx application instance
        env: Main environment
        docnames: Documents being merged
        other: Other environment to merge from
    """
    # Merge documented accelerators set
    if hasattr(other, "documented_accelerators"):
        if not hasattr(env, "documented_accelerators"):
            env.documented_accelerators = set()
        env.documented_accelerators.update(other.documented_accelerators)
