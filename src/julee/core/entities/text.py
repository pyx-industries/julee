"""Text that normalises itself: non-empty text, names and slugs.

Three value objects, each a ``str`` subclass whose constructor decides
what the value is. ``Slug("My System")`` is ``"my-system"``, and there
is no second way to get one.

They were field validators. Sixty-two of them across the kits, of which
fifty-nine returned a changed value rather than raising — which is not
validation. It is a constructor, written in the entity and copied. The
most common body, thirty-seven times, was ``v.strip()``.

Copying is what made them wrong, not what made them tedious. A slug
field ran :func:`~julee.core.utils.slugify`; a field *naming* that slug
ran ``strip``. So a container stored as ``"web-application"`` could be
named by a component as ``"Web Application"``, and the lookup came back
empty rather than wrong — no exception, no log line, no failing test
(julee-kits#70). Declaring both ends :class:`Slug` is what stops that:
one implementation of what a slug is, and every route reaches it.

**Why the kernel.** :func:`~julee.core.utils.slugify` and
:func:`~julee.core.utils.normalize_name` are already here, for the
reason their module gives: the rules have to be the same everywhere or
the references stop matching. These types are those functions'
constructors, so they belong in the same place. Three kits wanted them
independently (julee-kits#71), which is the Rule of 3 met rather than
anticipated.

**Why ``str`` subclasses.** Being strings is what makes them free to
adopt: they serialise as strings, key dictionaries, format into
f-strings and compare equal to plain strings, so nothing downstream
unwraps anything and no stored data changes shape. The alternative
considered was ``Annotated[str, BeforeValidator(...)]``, which costs no
call-site churn at all — and was rejected because it does not survive
#307. With no pydantic running the validator, nothing normalises;
normalising in ``__new__`` keeps working when entities become frozen
dataclasses.

They are not entities and not driven ports. There is nothing to inject
and no composition root involved: a value object is constructed inline,
where text becomes domain.
:func:`julee.core.entities.kernel_entity_names` does not collect them,
because a record is what a repository is bound to and these are values
a record is made of.
"""

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from julee.core.utils import normalize_name, slugify

__all__ = ["Name", "NonEmptyText", "Slug"]


class NonEmptyText(str):
    """Text a caller has to actually supply.

    Stripped of the whitespace around it, and refused if that leaves
    nothing. The stripping is what makes the refusal mean anything:
    without it ``"   "`` is a value and ``""`` is not, which is a
    distinction no domain wants to carry.

    The base of :class:`Name` and :class:`Slug`, and useful on its own
    for a field whose only rule is that it is there — an entity
    identifier, a prompt, a description.
    """

    __slots__ = ()

    _what = "value"
    """What to call this in the error, so the message reads as English."""

    def __new__(cls, value: str) -> "NonEmptyText":
        text = str(value).strip()
        if not text:
            raise ValueError(f"a {cls._what} cannot be empty")
        return super().__new__(cls, text)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Validate by constructing, serialise as the string it is.

        Validation is the constructor, so pydantic reaches the one
        implementation the same way a direct call does. Serialisation is
        ``str``, so what goes on the wire is a plain JSON string,
        unchanged from before these types existed.
        """
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                str, return_schema=core_schema.str_schema(), when_used="json"
            ),
        )


class Name(NonEmptyText):
    """Text a person wrote, kept as they wrote it.

    Unlike a :class:`Slug`, a name is for reading, so the only thing
    done to it is stripping the whitespace around it.

    :attr:`normalized` is how names are compared — case-insensitively,
    with hyphens and underscores read as spaces — so "Data Steward",
    "data-steward" and "data_steward" are one name. A property rather
    than a second field, because it is not separate information: hcd
    stores it as a field on two entities, computed by a validator and
    then recomputed in ``model_post_init`` in case the validator did
    not run.
    """

    __slots__ = ()

    _what = "name"

    @property
    def normalized(self) -> str:
        """This name in the form names are compared in."""
        return normalize_name(self)


class Slug(NonEmptyText):
    """A URL-safe identifier, normalised on the way in.

    Entities refer to each other by slug, so the two sides of a
    reference have to agree. Declaring both sides ``Slug`` is what makes
    them agree; the alternative — remembering to call
    :func:`~julee.core.utils.slugify` at each end — is what c4 was doing
    and got wrong in eight of twelve places.

    Text with nothing slug-shaped in it is refused rather than turned
    into an empty slug, because an empty identifier names everything and
    nothing.
    """

    __slots__ = ()

    def __new__(cls, value: str) -> "Slug":
        slug = slugify(str(value).strip())
        if not slug:
            raise ValueError(
                f"{value!r} has nothing in it that can be a slug. A slug "
                f"needs at least one letter or digit"
            )
        return str.__new__(cls, slug)
