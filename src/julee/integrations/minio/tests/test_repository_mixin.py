"""What a repository stores in MinIO, and what it gets back.

An entity goes out as JSON and comes back as an entity. The coming
back is the half worth testing hardest: it used to be
``model_class(**json_dict)``, which hands every field whatever JSON
happened to hold. Pydantic rebuilt the real types on the way in; a
frozen dataclass does not, and stores the raw JSON instead — a str
where a datetime belongs, a list where a tuple does, and a value
object's checks never run.

Nothing raises when that happens, which is why these tests ask what
came back rather than that something did.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar

import pytest

from julee.core.values.text import NonEmptyText
from julee.integrations.minio.client import MinioClient, MinioRepositoryMixin
from julee.integrations.minio.testing import FakeMinioClient

pytestmark = pytest.mark.unit

BUCKET = "widgets"

E = TypeVar("E")


@dataclass(frozen=True)
class Widget:
    """An entity with one of everything that does not survive raw JSON."""

    widget_id: NonEmptyText
    made_at: datetime
    tags: tuple[str, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Gadget:
    """A second entity, to show a bucket holds more than one kind."""

    gadget_id: str
    parts: tuple[str, ...] = field(default_factory=tuple)


class WidgetStore(MinioRepositoryMixin):
    """The least a repository has to be to use the mixin.

    The log messages the mixin asks for are supplied here rather than
    at every call, so a test reads as what it is asking about.
    """

    def __init__(self, client: MinioClient) -> None:
        """Start against a client, with the bucket made."""
        self.client = client
        self.logger = logging.getLogger("widget-store")
        self.ensure_buckets_exist(BUCKET)

    def save(self, name: str, entity: object) -> None:
        """Write one entity."""
        self.put_json_object(BUCKET, name, entity, "saved", "could not save")

    def load(self, name: str, model_class: type[E]) -> E | None:
        """Read one entity back."""
        return self.get_json_object(
            BUCKET, name, model_class, "not found", "could not read"
        )

    def load_many(self, names: list[str], model_class: type[E]) -> dict[str, E | None]:
        """Read several back."""
        return self.get_many_json_objects(
            BUCKET, names, model_class, "not found", "could not read"
        )


@pytest.fixture
def store() -> WidgetStore:
    """A repository over a fake MinIO."""
    return WidgetStore(FakeMinioClient())


def a_widget(**overrides: object) -> Widget:
    """A widget with every field populated."""
    fields: dict[str, object] = {
        "widget_id": NonEmptyText("w-1"),
        "made_at": datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
        "tags": ("blue", "small"),
    }
    fields.update(overrides)
    return Widget(**fields)  # type: ignore[arg-type]


class TestADataclassEntityComesBackWhole:
    """The silent case: nothing raises, and the values are wrong."""

    def test_it_comes_back_equal(self, store: WidgetStore) -> None:
        """The whole entity, not merely something with the same id."""
        widget = a_widget()
        store.save("w-1", widget)

        back = store.load("w-1", Widget)

        assert back == widget

    def test_a_datetime_comes_back_as_a_datetime(self, store: WidgetStore) -> None:
        """JSON has no datetime, so this is the field that rots first.

        Equality above would not catch it on its own: a str and a
        datetime are never equal, so this says which field and why.
        """
        store.save("w-1", a_widget())

        back = store.load("w-1", Widget)

        assert back is not None
        assert isinstance(back.made_at, datetime)

    def test_a_tuple_comes_back_as_a_tuple(self, store: WidgetStore) -> None:
        """JSON has only arrays.

        A list here is a mutable collection inside a frozen entity,
        which compares equal to the tuple it should have been — so
        equality alone cannot see it.
        """
        store.save("w-1", a_widget())

        back = store.load("w-1", Widget)

        assert back is not None
        assert isinstance(back.tags, tuple)

    def test_a_value_object_comes_back_as_itself(self, store: WidgetStore) -> None:
        """A NonEmptyText that arrives as a bare str was never checked.

        It also compares equal to the str it should have been built
        from, so this asks the type.
        """
        store.save("w-1", a_widget())

        back = store.load("w-1", Widget)

        assert back is not None
        assert isinstance(back.widget_id, NonEmptyText)

    def test_an_absent_object_is_None(self, store: WidgetStore) -> None:
        """Rather than raising, so a caller can ask."""
        assert store.load("nothing", Widget) is None


class TestFetchingSeveral:
    """get_many takes the same route and had the same hole."""

    def test_each_one_comes_back_whole(self, store: WidgetStore) -> None:
        """Both entities, rebuilt."""
        first, second = a_widget(), a_widget(widget_id=NonEmptyText("w-2"))
        store.save("w-1", first)
        store.save("w-2", second)

        back = store.load_many(["w-1", "w-2"], Widget)

        assert back == {"w-1": first, "w-2": second}

    def test_their_fields_are_rebuilt_too(self, store: WidgetStore) -> None:
        """The same question as the single case, asked of this route."""
        store.save("w-1", a_widget())

        back = store.load_many(["w-1"], Widget)

        assert isinstance(back["w-1"].made_at, datetime)  # type: ignore[union-attr]

    def test_one_that_is_not_there_comes_back_as_None(self, store: WidgetStore) -> None:
        """Every name asked for gets a key, so the caller can tell
        which of them was missing."""
        store.save("w-1", a_widget())

        back = store.load_many(["w-1", "gone"], Widget)

        assert back["gone"] is None
        assert back["w-1"] is not None


class TestStampingTheTimes:
    """update_timestamps rebuilds the entity, so it must know how."""

    def test_it_sets_created_at_when_there_was_none(self, store: WidgetStore) -> None:
        """A new entity gets its creation time here."""
        stamped = store.update_timestamps(a_widget())

        assert stamped.created_at is not None

    def test_it_leaves_an_existing_created_at_alone(self, store: WidgetStore) -> None:
        """An entity is created once."""
        made = datetime(2020, 1, 1, tzinfo=UTC)

        stamped = store.update_timestamps(a_widget(created_at=made))

        assert stamped.created_at == made

    def test_it_always_sets_updated_at(self, store: WidgetStore) -> None:
        """Every save is an update."""
        was = datetime(2020, 1, 1, tzinfo=UTC)

        stamped = store.update_timestamps(a_widget(updated_at=was))

        assert stamped.updated_at is not None
        assert stamped.updated_at > was

    def test_it_changes_nothing_else(self, store: WidgetStore) -> None:
        """Stamping is not an opportunity to lose a field."""
        stamped = store.update_timestamps(a_widget())

        assert stamped.tags == ("blue", "small")

    def test_an_entity_with_no_timestamps_is_returned_as_it_was(
        self, store: WidgetStore
    ) -> None:
        """Not every entity carries them, and rebuilding one that does
        not would be work for nothing."""
        gadget = Gadget(gadget_id="g-1", parts=("a",))

        assert store.update_timestamps(gadget) is gadget
