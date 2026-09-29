"""Bounded context introspection model.

Summarises the Clean Architecture layers found in one bounded context,
in terms of the code models in :mod:`julee.core.entities.code_info` and
the pipelines in :mod:`julee.core.entities.pipeline`. It lives in its
own module because ``Pipeline`` itself depends on ``code_info``.
"""

from dataclasses import dataclass

from julee.core.entities.code_info import ClassInfo
from julee.core.entities.pipeline import Pipeline


@dataclass(frozen=True)
class BoundedContextInfo:
    """Information about a bounded context's code structure.

    Represents the Clean Architecture layers present in a bounded context:
    - entities (domain/models/)
    - use_cases (domain/usecases/)
    - repository_protocols (domain/repositories/)
    - service_protocols and handler_protocols (domain/services/)
    - oracle_protocols (domain/oracles/)
    - calculator_protocols (domain/calculators/)
    - witness_protocols (domain/witnesses/)

    The last five are the driven ports of ADR 016, each found by the
    directory it sits in rather than by what it is called.

    This is a foundational model that viewpoint accelerators project onto.
    For example, HCD's Accelerator model is ontologically bound to this.
    """

    slug: str
    entities: tuple[ClassInfo, ...] = ()
    """What this context keeps under an id."""

    values: tuple[ClassInfo, ...] = ()
    """What this context is made of but does not keep.

    A value object has no identity, so no repository is bound to one and
    no port can be bound to one either (ADR 018). Read from
    domain/values/, which is the declaration.
    """
    use_cases: tuple[ClassInfo, ...] = ()
    requests: tuple[ClassInfo, ...] = ()
    responses: tuple[ClassInfo, ...] = ()
    repository_protocols: tuple[ClassInfo, ...] = ()
    service_protocols: tuple[ClassInfo, ...] = ()
    handler_protocols: tuple[ClassInfo, ...] = ()
    oracle_protocols: tuple[ClassInfo, ...] = ()
    calculator_protocols: tuple[ClassInfo, ...] = ()
    witness_protocols: tuple[ClassInfo, ...] = ()
    pipelines: tuple[Pipeline, ...] = ()
    has_infrastructure: bool = False
    code_dir: str = ""
    objective: str | None = None
    docstring: str | None = None

    def __post_init__(self) -> None:
        """Check the slug and trim it.

        Raises:
            ValueError: If the slug is empty or only whitespace
        """
        if not self.slug or not self.slug.strip():
            raise ValueError("slug cannot be empty")
        object.__setattr__(self, "slug", self.slug.strip())

    @property
    def entity_count(self) -> int:
        """Get number of domain entities."""
        return len(self.entities)

    @property
    def use_case_count(self) -> int:
        """Get number of use cases."""
        return len(self.use_cases)

    @property
    def driven_ports(self) -> list[ClassInfo]:
        """Every driven port this context declares, in ADR 016's order."""
        return [
            *self.repository_protocols,
            *self.service_protocols,
            *self.oracle_protocols,
            *self.calculator_protocols,
            *self.witness_protocols,
            *self.handler_protocols,
        ]

    @property
    def protocol_count(self) -> int:
        """Get total number of driven ports across all six kinds."""
        return len(self.driven_ports)

    @property
    def pipeline_count(self) -> int:
        """Get number of pipelines."""
        return len(self.pipelines)

    @property
    def has_entities(self) -> bool:
        """Check if bounded context has any entities."""
        return len(self.entities) > 0

    @property
    def has_use_cases(self) -> bool:
        """Check if bounded context has any use cases."""
        return len(self.use_cases) > 0

    @property
    def has_protocols(self) -> bool:
        """Check if bounded context has any protocols."""
        return self.protocol_count > 0

    def get_entity_names(self) -> list[str]:
        """Get list of entity class names."""
        return [e.name for e in self.entities]

    def get_use_case_names(self) -> list[str]:
        """Get list of use case class names."""
        return [u.name for u in self.use_cases]

    def summary(self) -> str:
        """Get a brief summary of the bounded context.

        Returns:
            Summary string like "3 entities, 2 use cases"
        """
        parts = []
        if self.entities:
            parts.append(f"{len(self.entities)} entities")
        if self.use_cases:
            parts.append(f"{len(self.use_cases)} use cases")
        if self.repository_protocols:
            parts.append(f"{len(self.repository_protocols)} repository protocols")
        if self.service_protocols:
            parts.append(f"{len(self.service_protocols)} service protocols")
        if self.handler_protocols:
            parts.append(f"{len(self.handler_protocols)} handler protocols")
        if self.pipelines:
            parts.append(f"{len(self.pipelines)} pipelines")
        return ", ".join(parts) if parts else "empty"
