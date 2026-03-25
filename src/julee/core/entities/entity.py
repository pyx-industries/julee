"""Entity base class for julee domain models.

Domain models in julee are immutable records — they represent a snapshot of
business state at a point in time. "Changing" an entity means constructing a
new instance via model_copy(update={...}) and saving it to the repository;
the old Python object is discarded.

This is the canonical definition of what an Entity IS in julee. The doctrine
tests in test_entity.py enforce it across all bounded contexts.
"""

from pydantic import BaseModel


class Entity(BaseModel, frozen=True):
    """An immutable domain record.

    Entities represent snapshots of business state. They are constructed
    once and never mutated. When state must change, create a new instance
    via model_copy(update={...}) and persist it via the repository.

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

        # Correct: creates a new snapshot, saves it
        assembly = assembly.model_copy(update={"status": AssemblyStatus.COMPLETED})
        await assembly_repo.save(assembly)
    """
