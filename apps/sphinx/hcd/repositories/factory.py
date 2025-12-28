"""Factory for creating SphinxEnv repository classes.

Provides utilities to reduce boilerplate when creating Sphinx environment
repositories for HCD entities.
"""

from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment

T = TypeVar("T", bound=BaseModel)


def pluralize(name: str) -> str:
    """Pluralize entity name for storage key.

    Args:
        name: Lowercase entity name

    Returns:
        Pluralized name for use as storage key
    """
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        # story -> stories, journey -> journeys (not journeies)
        return name[:-1] + "ies"
    elif name.endswith("s") or name.endswith("x") or name.endswith("ch"):
        return name + "es"
    else:
        return name + "s"


def derive_entity_config(entity_class: type[T], entity_key: str | None = None) -> dict:
    """Derive repository configuration from entity class.

    Args:
        entity_class: Pydantic model class for the entity
        entity_key: Optional explicit storage key override

    Returns:
        Dict with entity_name, entity_key, id_field
    """
    name = entity_class.__name__
    return {
        "entity_name": name,
        "entity_key": entity_key or pluralize(name.lower()),
        "id_field": "slug",
        "entity_class": entity_class,
    }


def create_sphinx_env_repository(
    entity_class: type[T],
    protocol_class: type,
    entity_key: str | None = None,
) -> type:
    """Create a SphinxEnv repository class for an entity type.

    Creates a minimal repository class that only provides CRUD operations
    from SphinxEnvRepositoryMixin. Use this for entities that don't need
    custom query methods.

    For entities requiring custom queries, define the class explicitly
    and inherit from SphinxEnvRepositoryMixin.

    Args:
        entity_class: Pydantic model class for the entity
        protocol_class: Repository protocol to implement
        entity_key: Optional storage key override (default: pluralized class name)

    Returns:
        New repository class

    Example:
        SphinxEnvMyEntityRepository = create_sphinx_env_repository(
            MyEntity, MyEntityRepository
        )
    """
    from .base import SphinxEnvRepositoryMixin

    config = derive_entity_config(entity_class, entity_key)

    class SphinxEnvRepository(SphinxEnvRepositoryMixin[entity_class], protocol_class):
        __doc__ = f"""Sphinx env-backed implementation of {protocol_class.__name__}.

        Stores {config['entity_key']} in env.hcd_storage["{config['entity_key']}"]
        for parallel-safe Sphinx builds.
        """
        entity_class = config["entity_class"]
        entity_name = config["entity_name"]
        entity_key = config["entity_key"]
        id_field = config["id_field"]

        def __init__(self, env: "BuildEnvironment") -> None:
            self.env = env

    # Set meaningful class name
    SphinxEnvRepository.__name__ = f"SphinxEnv{config['entity_name']}Repository"
    SphinxEnvRepository.__qualname__ = SphinxEnvRepository.__name__

    return SphinxEnvRepository
