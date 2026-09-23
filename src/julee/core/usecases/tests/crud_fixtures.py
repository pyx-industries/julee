"""Entity and repository the generator tests generate CRUD against.

They live in a module of their own because the generator emits import
statements naming the module its entity came from, so the test's fakes have
to be importable by a dotted path.
"""

from pydantic import BaseModel


class Widget(BaseModel):
    """A thing with more than one field, so an update can leave one alone."""

    slug: str
    name: str = ""
    colour: str = ""
    notes: str | None = None


class WidgetRepository:
    """In-memory repository satisfying what the generated use cases call."""

    def __init__(self) -> None:
        """Start empty."""
        self.storage: dict[str, Widget] = {}

    async def generate_id(self) -> str:
        """Mint a surrogate id, distinctive so a test can tell it was used."""
        return "generated-id"

    async def get(self, entity_id: str) -> Widget | None:
        """Return the widget with this slug, or None."""
        return self.storage.get(entity_id)

    async def save(self, entity: Widget) -> None:
        """Store the widget under its slug."""
        self.storage[entity.slug] = entity
