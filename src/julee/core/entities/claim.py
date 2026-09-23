"""What one kit says about how its terms line up with another's.

Two bounded contexts do not share meaning. A Story in one and a UseCase
in another are different models, and neither owns the other. But somebody
looking at both can say they are the same event told from two sides, and
a solution's documentation is poorer if nobody says it.

So a kit publishes claims: this is how I see my neighbours, from where I
stand. A claim is an assertion, not a fact. It names a class the kit owns
and a class it does not, and the far end may belong to something nobody
has installed — the claim is simply unresolvable until a solution adopts
both.

A solution decides what is true for it. It reads the claims of the kits
it has adopted, accepts, rejects or replaces them, and adds its own. That
resolved set is the solution's semantics; nothing merges automatically.

What a claim may not do is create a dependency. Both ends are dotted
paths, never imports, so a kit naming another kit's class does not reach
for it — and doctrine checks the names resolve rather than trusting them,
which is the failure the decorators this replaces never caught.
"""

from enum import StrEnum

from pydantic import Field, field_validator

from julee.core.entities.entity import Entity


class ClaimKind(StrEnum):
    """The ways one class can be said to line up with another.

    Five, because five were ever used. The vocabulary grows when
    something needs it to, not in advance.
    """

    IS_A = "is_a"
    """The source is a kind of the target.

    A solution's CustomerSegment is_a Persona: the solution has its own
    word for something the framework already describes.
    """

    PROJECTS = "projects"
    """The source is a view of the target, from another vantage.

    A Story projects a UseCase: the same event, told by whoever wanted it
    rather than by the system that does it.
    """

    PART_OF = "part_of"
    """The source belongs to the target, which is the larger thing."""

    CONTAINS = "contains"
    """The source is the larger thing, and the target belongs to it."""

    REFERENCES = "references"
    """The source points at the target without owning it."""


class Claim(Entity):
    """One kit's assertion about how a class of its own relates to another.

    Both ends are dotted paths to classes, for example
    ``julee_hcd.domain.models.story.Story``. Names rather than imports:
    a claim is read from a data file without loading the code it talks
    about, so nothing here can create a dependency.
    """

    id: str = Field(
        description='Identifier within its file, e.g. "story-projects-usecase"'
    )
    source: str = Field(description="Dotted path to the class making the claim")
    kind: ClaimKind = Field(description="How the source lines up with the target")
    target: str = Field(description="Dotted path to the class being claimed about")
    note: str = Field(
        default="",
        description="Why this is so, in a sentence or two, for the reader",
    )

    @field_validator("id", "source", "target", mode="before")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """A claim with a blank end says nothing and cannot be checked."""
        if not v or not v.strip():
            raise ValueError("a claim needs an id, a source and a target")
        return v.strip()
