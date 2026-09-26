"""Entity base class for julee domain models.

Domain models in julee are immutable records — they represent a snapshot of
business state at a point in time. "Changing" an entity means constructing a
new instance via evolve(...) and saving it to the repository; the old Python
object is discarded.

This is the canonical definition of what an Entity IS in julee. The doctrine
tests in test_entity.py enforce it across all bounded contexts.
"""

from typing import Any, Self

from pydantic import BaseModel


class Entity(BaseModel, frozen=True):
    """An immutable domain record.

    Entities represent snapshots of business state. They are constructed
    once and never mutated. When state must change, create a new instance
    via :meth:`evolve` and persist it via the repository.

    Inheriting from Entity:
    - Enforces immutability via Pydantic's frozen=True constraint
    - Prevents field reassignment after construction
    - Signals intent: this is a value/record, not a stateful object

    True immutability also requires using immutable collection types in
    field annotations. These are enforced by doctrine:
    - tuple[...] instead of list[...]
    - Mapping[K, V] instead of dict[K, V]
    - frozenset[...] instead of set[...]

    Example — updating an entity:

        # Wrong: mutates the object
        assembly.status = AssemblyStatus.COMPLETED

        # Wrong: skips the validators, quietly
        assembly = assembly.model_copy(update={"status": AssemblyStatus.COMPLETED})

        # Correct: creates a new snapshot, saves it
        assembly = assembly.evolve(status=AssemblyStatus.COMPLETED)
        await assembly_repo.save(assembly)
    """

    def evolve(self, **changes: Any) -> Self:
        """A new snapshot of this entity, with these fields changed.

        Every validator runs, which is the whole difference between this
        and ``model_copy(update=...)``. Pydantic's copy does not
        validate by design, so a field with a validator could be written
        through it with something the validator would have refused —
        or, more often, something the validator would have *changed*.

        That second case is the one that bit. A validator that returns
        ``tuple(v)`` or ``v.strip() or None`` is not checking, it is
        deciding what the field holds. Skipped, an entity ends up
        carrying a mutable list where its own annotation says tuple,
        which is what this class exists to prevent
        (julee-kits#57).

        This docstring used to recommend ``model_copy(update=...)``, and
        every place that got it wrong was following that advice.

        Implemented by reconstructing from the current field values
        rather than from ``model_dump()``. A dump drops fields marked
        ``exclude=True`` and cannot represent one holding something
        unserialisable — a document's content stream is both — so the
        obvious implementation would silently lose it.

        Args:
            **changes: Field names and their new values

        Returns:
            A new instance, validated

        Raises:
            ValueError: If the result would not be a valid entity.
                Pydantic raises ValidationError, which is one.
        """
        return type(self)(**{**self.__dict__, **changes})
