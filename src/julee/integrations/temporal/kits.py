"""Resolving the activity classes the adopted kits contribute.

The counterpart of :mod:`julee.integrations.fastapi.routers`, and the
last contribution point that had no consumer: a solution adopting CEAP
still imported its activity classes by hand, which is the manifest being
a description nobody acted on.
"""

import logging
from pathlib import Path

from julee.core.kits import adopted_kits, contributed_objects

__all__ = ["CONTRIBUTION_POINT", "kit_activities"]

logger = logging.getLogger(__name__)

CONTRIBUTION_POINT = "temporal.activities"
"""Where a kit says which of its classes are activities."""


def kit_activities(solution_root: Path) -> list[type]:
    """The activity classes the adopted kits contribute, in adoption order.

    Classes, not instances, and there is no ``include_kit_activities`` to
    match ``include_kit_routers``. A router is finished when a kit hands
    it over; an activity class is not, because it takes its dependencies
    at construction and which MinIO client or database session to give it
    is the solution's decision. So the solution constructs them and
    passes the instances to
    :func:`~julee.integrations.temporal.activities.collect_activities_from_instances`::

        classes = kit_activities(SOLUTION_ROOT)
        instances = [cls(client=minio_client) for cls in classes]
        worker = Worker(client, activities=collect_activities_from_instances(*instances))

    A kit points at a tuple rather than writing one path per class, so
    eight activity classes travel as one contribution; the flattening is
    :func:`~julee.core.kits.contributed_objects`.

    Args:
        solution_root: Path to the solution root directory

    Returns:
        Whatever each kit pointed at, resolved and flattened

    Raises:
        ImportError: If a kit names a module that is not there
        AttributeError: If a kit names an attribute a module does not have
        TypeError: If a kit contributes something that is not a class
    """
    found: list[type] = []
    for kit in adopted_kits(solution_root):
        for obj in contributed_objects(kit, CONTRIBUTION_POINT):
            if not isinstance(obj, type):
                # Dropping it quietly would leave a worker missing an
                # activity, and the workflow calling it waiting for a
                # timeout — the failure this whole contribution point
                # exists to make impossible.
                raise TypeError(
                    f"{kit.slug} contributes {obj!r} at {CONTRIBUTION_POINT}, "
                    f"which is not a class. A kit contributes the classes "
                    f"themselves, or a tuple of them, so the solution can "
                    f"construct each with its own dependencies."
                )
            found.append(obj)
    logger.debug("Resolved %d kit activity classes", len(found))
    return found
