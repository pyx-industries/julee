"""What the generated responses carry, and what they do not.

Every generated response used to hold the entity: ``story: Story``. A
response is a message, and a message built around an entity is the
entity's shape under another name, so a client of the use case depended
on the domain and the domain could not change without breaking it. It
did, twice, in ceap — over HTTP and into Temporal history — and 99
generated fields across c4 and hcd were waiting to do the same.

These tests import what the generator wrote and ask it, rather than
reading the text, because a name in a string does not say what a thing
is. That means the fixture solution has to be importable, which the
doctrine tests beside this never needed: they run in a subprocess with
PYTHONPATH set. Here ``src/`` goes on this process's path, and the
modules come off it again afterwards so the next test's ``acme`` is its
own.
"""

import ast
import importlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from julee.core.usecases.generate_crud import generate

from .harness import a_julee_solution, importable

pytestmark = pytest.mark.unit

ENTITY = '''"""The Story entity, with one of every shape a field takes."""

from dataclasses import dataclass
from enum import StrEnum

from julee.core.entities.text import Name, Slug

from acme.stories.domain.values.step import Step


class Mood(StrEnum):
    """How a story feels."""

    CALM = "calm"
    TENSE = "tense"


@dataclass(frozen=True)
class Story:
    """A unit of work."""

    slug: Slug
    name: Name
    mood: Mood = Mood.CALM
    tags: tuple[str, ...] = ()
    steps: tuple[Step, ...] = ()
    parent: Slug | None = None
'''

VALUE = '''"""A step of a story, which has no identity of its own."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    """One thing that happens."""

    ref: str
    note: str = ""
'''

REPOSITORY = '''"""Where stories are kept."""

from typing import Protocol

from acme.stories.domain.models.story import Story


class StoryRepository(Protocol):
    """Stories, stored somewhere."""

    async def get(self, entity_id: str) -> Story | None: ...

    async def save(self, entity: Story) -> None: ...

    async def list_all(self) -> list[Story]: ...

    async def delete(self, entity_id: str) -> bool: ...
'''


def a_solution_with_a_story(root: Path) -> Path:
    """Write a solution with the fixture entity and generate its CRUD.

    Args:
        root: The solution root to write into

    Returns:
        The root, whose src/ is what to import from
    """
    context = a_julee_solution(root)
    for package in ("domain", "domain/models", "domain/values", "domain/repositories"):
        (context / package).mkdir(parents=True, exist_ok=True)
        (context / package / "__init__.py").write_text("")
    (context / "domain" / "models" / "story.py").write_text(ENTITY)
    (context / "domain" / "values" / "step.py").write_text(VALUE)
    (context / "domain" / "repositories" / "story.py").write_text(REPOSITORY)
    return root


@pytest.fixture
def generated(tmp_path: Path) -> Iterator[Path]:
    """The generated CRUD for the fixture entity, importable as acme.stories.

    Yields:
        The solution root
    """
    root = a_solution_with_a_story(tmp_path / "solution")
    with importable(root):
        generate(
            entity="Story",
            entity_module="acme.stories.domain.models.story",
            repo="StoryRepository",
            repo_module="acme.stories.domain.repositories.story",
            id_field="slug",
            create_fields=[
                ("slug", "str"),
                ("name", "str"),
                ("tags", "tuple[str, ...]=()"),
                # A request naming a value that lives in domain/values/,
                # which the entity's module imports and does not define.
                ("steps", "tuple[Step, ...]=()"),
            ],
            update_fields=[("name", "str"), ("tags", "tuple[str, ...]")],
            include_delete=True,
            out_dir=root / "src" / "acme" / "stories",
        )
        yield root


def names_in(annotation: ast.expr) -> set[str]:
    """Every bare name an annotation mentions.

    Args:
        annotation: The annotation's AST

    Returns:
        The names, so ``tuple[Step, ...]`` gives {"tuple", "Step"}
    """
    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}


class TestWhatAResponseCarries:
    """The fields, not the entity."""

    def test_no_message_field_is_annotated_with_the_entity(
        self, generated: Path
    ) -> None:
        """The defect, stated as a test.

        Read off the AST rather than pydantic so that a field pydantic
        would happily accept — it serialises dataclasses without
        complaint — is still refused.
        """
        emitted = (
            generated / "src" / "acme" / "stories" / "dtos" / "crud_story.py"
        ).read_text()
        offending = [
            f"{cls.name}.{ast.unparse(field.target)}: {ast.unparse(field.annotation)}"
            for cls in ast.parse(emitted).body
            if isinstance(cls, ast.ClassDef)
            for field in cls.body
            if isinstance(field, ast.AnnAssign)
            and "Story" in names_in(field.annotation)
        ]

        assert not offending, "a generated message carries the entity:\n" + "\n".join(
            offending
        )

    def test_the_message_names_every_field_the_entity_has(
        self, generated: Path
    ) -> None:
        """One message per entity, with the entity's fields."""
        dtos = importlib.import_module("acme.stories.dtos.crud_story")

        assert tuple(dtos.StoryMessage.model_fields) == (
            "slug",
            "name",
            "mood",
            "tags",
            "steps",
            "parent",
        )

    def test_a_checked_string_goes_out_as_a_plain_one(self, generated: Path) -> None:
        """Slug and Name are how the domain says a str was checked.

        A reader of the message is not the one checking, so it is
        handed a str — on the annotation and in the value.
        """
        dtos = importlib.import_module("acme.stories.dtos.crud_story")
        models = importlib.import_module("acme.stories.domain.models.story")
        Slug = importlib.import_module("julee.core.entities.text").Slug
        Name = importlib.import_module("julee.core.entities.text").Name

        message = dtos.StoryMessage.of(models.Story(slug=Slug("a"), name=Name("A")))

        assert dtos.StoryMessage.model_fields["slug"].annotation is str
        assert type(message.slug) is str
        assert message.slug == "a"

    def test_a_value_rides_inside_its_entity(self, generated: Path) -> None:
        """A Step has no identity, so its shape on the wire is its shape.

        The Story is the thing with identity; the steps are values of
        it, and they are serialised in it as they are.
        """
        dtos = importlib.import_module("acme.stories.dtos.crud_story")
        models = importlib.import_module("acme.stories.domain.models.story")
        values = importlib.import_module("acme.stories.domain.values.step")
        text = importlib.import_module("julee.core.entities.text")

        story = models.Story(
            slug=text.Slug("a"),
            name=text.Name("A"),
            steps=(values.Step(ref="first"), values.Step(ref="second", note="n")),
        )

        assert dtos.StoryMessage.of(story).steps == story.steps

    def test_an_enum_stays_an_enum(self, generated: Path) -> None:
        """It was never the domain's private vocabulary."""
        dtos = importlib.import_module("acme.stories.dtos.crud_story")
        models = importlib.import_module("acme.stories.domain.models.story")
        text = importlib.import_module("julee.core.entities.text")

        message = dtos.StoryMessage.of(
            models.Story(
                slug=text.Slug("a"), name=text.Name("A"), mood=models.Mood.TENSE
            )
        )

        assert message.mood is models.Mood.TENSE

    def test_a_list_response_carries_no_count(self, generated: Path) -> None:
        """Paging is the router's; the use case returns the list."""
        dtos = importlib.import_module("acme.stories.dtos.crud_story")

        assert tuple(dtos.ListStoriesResponse.model_fields) == ("stories",)


class TestWhatTheMessagesImport:
    """Each name once, from where it lives.

    A request field naming ``tuple[Step, ...]`` used to get ``Step``
    imported from the entity's module, on the guess that everything a
    request names lives beside the entity. It worked while the entity's
    module happened to re-export the name — and collided the moment the
    message's own fields imported the same name from where it is
    defined. hcd's JourneyStep did exactly that after ADR 018 moved it.
    """

    def imports_in(self, generated: Path) -> list[tuple[str, str]]:
        """Every (module, name) the generated messages import.

        Args:
            generated: The solution root

        Returns:
            One pair per imported name, in file order
        """
        emitted = (
            generated / "src" / "acme" / "stories" / "dtos" / "crud_story.py"
        ).read_text()
        return [
            (node.module or "", alias.name)
            for node in ast.parse(emitted).body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        ]

    def test_a_request_field_s_type_is_not_imported_from_a_module_it_passes_through(
        self, generated: Path
    ) -> None:
        """Step is defined in domain/values/step.py and imported by story.py."""
        imported = self.imports_in(generated)

        assert ("acme.stories.domain.values.step", "Step") in imported
        assert ("acme.stories.domain.models.story", "Step") not in imported

    def test_no_name_is_imported_twice(self, generated: Path) -> None:
        """A second import of a name is a redefinition ruff refuses to fix.

        _tidy only warns when ruff refuses, so the file was written and
        imported fine — and failed the lint every kit runs. Generated
        code a human has to finish is not generated.
        """
        names = [name for _, name in self.imports_in(generated)]

        assert len(set(names)) == len(names), "imported more than once: " + ", ".join(
            sorted({n for n in names if names.count(n) > 1})
        )


class TestWhatTheUseCasesAnswerWith:
    """Run, not read: the generated use cases against a stub repository."""

    async def test_create_then_get_answer_with_messages(self, generated: Path) -> None:
        """A caller of the use case gets a message and never the entity."""
        dtos = importlib.import_module("acme.stories.dtos.crud_story")
        usecases = importlib.import_module("acme.stories.usecases.crud_story")
        models = importlib.import_module("acme.stories.domain.models.story")

        class Memory:
            def __init__(self) -> None:
                self.kept: dict[str, Any] = {}

            async def get(self, entity_id: str) -> Any | None:
                return self.kept.get(entity_id)

            async def save(self, entity: Any) -> None:
                self.kept[str(entity.slug)] = entity

            async def list_all(self) -> list[Any]:
                return list(self.kept.values())

            async def delete(self, entity_id: str) -> bool:
                return self.kept.pop(entity_id, None) is not None

        repo = Memory()
        created = await usecases.CreateStoryUseCase(repo).execute(
            dtos.CreateStoryRequest(slug="a", name="A", tags=("t",))
        )
        found = await usecases.GetStoryUseCase(repo).execute(
            dtos.GetStoryRequest(slug="a")
        )
        listed = await usecases.ListStoriesUseCase(repo).execute(
            dtos.ListStoriesRequest()
        )

        assert isinstance(created.story, dtos.StoryMessage)
        assert not isinstance(found.story, models.Story)
        assert found.story.name == "A"
        assert [s.slug for s in listed.stories] == ["a"]


class TestWhenItCannotSeeTheEntity:
    """It stops, rather than writing the old shape."""

    def test_it_refuses_to_generate_blind(self, tmp_path: Path) -> None:
        """Warn-and-emit-the-entity would reintroduce the defect quietly.

        The message is built from the entity's fields, so an entity the
        generator cannot import is one it cannot write a message for.
        """
        root = a_solution_with_a_story(tmp_path / "blind")

        with pytest.raises(ImportError):
            generate(
                entity="Story",
                entity_module="acme.nowhere.story",
                repo="StoryRepository",
                repo_module="acme.stories.domain.repositories.story",
                id_field="slug",
                create_fields=[("slug", "str")],
                update_fields=[],
                out_dir=root / "src" / "acme" / "stories",
            )
