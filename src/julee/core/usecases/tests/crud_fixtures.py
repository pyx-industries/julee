"""Entity and repositories the generator tests generate CRUD against.

They live in a module of their own because the generator emits import
statements naming the module its entity came from, so the test's fakes have
to be importable by a dotted path.

There are two repositories because there are two ways an entity comes by its
identity: one the repository mints, and one the caller already knows.
"""

from pydantic import BaseModel


class Widget(BaseModel):
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
