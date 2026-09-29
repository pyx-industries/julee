"""Entity and repositories the generator tests generate CRUD against.

They live in a module of their own because the generator emits import
statements naming the module its entity came from, so the test's fakes have
to be importable by a dotted path.

There are two repositories because there are two ways an entity comes by its
identity: one the repository mints, and one the caller already knows.

Every entity is a frozen dataclass, because that is what an entity is in
this framework and the generator now reads its fields to write a message.
Two of these were pydantic models, the last anywhere in the estate, and
the generator accepted them because it never looked.
"""

from dataclasses import dataclass
from typing import cast

from julee.core.entities.text import Name, NonEmptyText, Slug


@dataclass(frozen=True)
class Widget:
    """A thing with more than one field, so an update can leave one alone."""

    slug: str
    name: str = ""
    colour: str = ""
    notes: str | None = None


class WidgetRepository:
    """A repository for widgets keyed by a slug the caller chooses.

    It has no generate_id, which is the point: there is no ID here for a
    repository to decide, so a create that reached for one would fail.
    """

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, Widget] = {}

    async def get(self, entity_id: str) -> Widget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: Widget) -> None:
        """Store the widget under its slug."""
        self.storage[entity.slug] = entity


class MintingWidgetRepository(WidgetRepository):
    """A repository that decides the key itself."""

    async def generate_id(self) -> str:
        """Mint an ID, distinctive so a test can tell it was used."""
        return "generated-id"


class DeletableWidgetRepository(WidgetRepository):
    """A repository whose widgets can be removed.

    Separate from WidgetRepository because delete is opt-in: ceap and
    polling keep the record of what they processed and have no delete
    across nine repository protocols, so a fixture where every repository
    deletes would not describe the world the generator emits into.
    """

    async def delete(self, entity_id: str) -> bool:
        """Remove the widget, saying whether there was one to remove."""
        return self.storage.pop(entity_id, None) is not None


DERIVE_IT = cast("Slug", "")
"""The slug default, meaning "name it after the widget".

The same kludge the kits use, and for the same reason: a dataclass
default cannot read the other fields, and Slug refuses an empty string,
so the field holds a bare str until __post_init__ replaces it.
"""


@dataclass(frozen=True)
class SelfNamingWidget:
    """A widget that works out its own slug when nobody supplies one.

    Shaped like c4's Relationship and DynamicStep, which are the real
    cases: a relationship is identified by its two ends and a step by
    its sequence and number, so there is nothing for a caller to
    choose and nothing for a repository to mint.

    The Slug type is what makes this bite. Slug refuses an empty
    string, so handing the field over empty fails before anything can
    derive it. That is exactly what the kits hit.
    """

    name: str
    slug: Slug = DERIVE_IT

    def __post_init__(self) -> None:
        """Name it after its name, unless it was named."""
        if not self.slug:
            object.__setattr__(self, "slug", Slug(f"{self.name}-derived"))


class SelfNamingWidgetRepository:
    """A repository for widgets that name themselves."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, SelfNamingWidget] = {}

    async def get(self, entity_id: str) -> SelfNamingWidget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: SelfNamingWidget) -> None:
        """Store the widget under its slug."""
        self.storage[entity.slug] = entity


@dataclass(frozen=True)
class DerivedIdWidget:
    """A widget whose identity is not a field at all.

    c4's Relationship is the real case: it is named after its two
    ends, so there is nothing to choose, nothing to mint, and nothing
    to store. A property says that where a field with a default only
    implies it.
    """

    left: str
    right: str

    @property
    def slug(self) -> Slug:
        """Name it after what it joins."""
        return Slug(f"{self.left}-to-{self.right}")


class DerivedIdWidgetRepository:
    """A repository with no generate_id, because nothing mints here."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, DerivedIdWidget] = {}

    async def get(self, entity_id: str) -> DerivedIdWidget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: DerivedIdWidget) -> None:
        """Store the widget under the slug it works out."""
        self.storage[entity.slug] = entity


@dataclass(frozen=True)
class CheckedWidget:
    """A widget with a rule of its own, checked on construction."""

    slug: str
    name: str = ""

    def __post_init__(self) -> None:
        """Refuse a widget with no name."""
        if not self.name:
            raise ValueError("a widget's name may not be blank")


class CheckedWidgetRepository:
    """A repository for widgets that check themselves."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, CheckedWidget] = {}

    async def get(self, entity_id: str) -> CheckedWidget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: CheckedWidget) -> None:
        """Store the widget under its slug."""
        self.storage[entity.slug] = entity


@dataclass(frozen=True)
class NamedWidget:
    """A widget whose name is a value object, like its slug.

    The id is not the only field an entity declares as something
    stronger than a str. hcd has five entities with a Name, a
    NonEmptyText or a tuple of Slugs among their ordinary fields, and a
    request says str for every one of them because that is what crosses
    the wire.
    """

    slug: Slug
    name: Name
    title: NonEmptyText
    note: str = ""


class NamedWidgetRepository:
    """A repository for widgets with value objects in them."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, NamedWidget] = {}

    async def get(self, entity_id: str) -> NamedWidget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: NamedWidget) -> None:
        """Store the widget under its slug."""
        self.storage[entity.slug] = entity
