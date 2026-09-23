"""Tests for the file-backed repository mixin.

The point of the mixin is that the files are the record: what is written
survives the repository, and what is on disk is what a reader sees.
"""

from pathlib import Path

import pytest
from pydantic import BaseModel

from julee.repositories.file import FileRepositoryMixin

pytestmark = pytest.mark.unit


class Story(BaseModel):
    slug: str
    title: str


class StoryRepository(FileRepositoryMixin[Story]):
    """A repository of stories, one plain-text file each."""

    def __init__(self, base_path: Path) -> None:
        self.storage: dict[str, Story] = {}
        self.base_path = base_path
        self.entity_name = "Story"
        self.id_field = "slug"
        self._load_all()

    def _get_file_path(self, entity: Story) -> Path:
        return self.base_path / f"{entity.slug}.txt"

    def _serialize(self, entity: Story) -> str:
        return entity.title

    def _load_all(self) -> None:
        for path in sorted(self.base_path.glob("*.txt")):
            self.storage[path.stem] = Story(slug=path.stem, title=path.read_text())


@pytest.fixture
def repository(tmp_path: Path) -> StoryRepository:
    return StoryRepository(tmp_path)


async def test_saving_writes_the_file(repository: StoryRepository, tmp_path) -> None:
    await repository.save(Story(slug="upload", title="Upload a document"))

    assert (tmp_path / "upload.txt").read_text() == "Upload a document"


async def test_saving_creates_the_directories_it_needs(tmp_path: Path) -> None:
    class NestedRepository(StoryRepository):
        def _get_file_path(self, entity: Story) -> Path:
            return self.base_path / "stories" / "drafts" / f"{entity.slug}.txt"

    repository = NestedRepository(tmp_path)

    await repository.save(Story(slug="upload", title="Upload a document"))

    assert (tmp_path / "stories" / "drafts" / "upload.txt").exists()


async def test_what_was_saved_can_be_read_back(repository: StoryRepository) -> None:
    await repository.save(Story(slug="upload", title="Upload a document"))

    found = await repository.get("upload")

    assert found is not None
    assert found.title == "Upload a document"


async def test_an_unknown_id_is_none(repository: StoryRepository) -> None:
    assert await repository.get("nothing-here") is None


async def test_get_many_reports_the_misses_too(repository: StoryRepository) -> None:
    await repository.save(Story(slug="upload", title="Upload a document"))

    found = await repository.get_many(["upload", "missing"])

    assert found == {"upload": found["upload"], "missing": None}
    assert found["upload"] is not None


async def test_the_files_outlive_the_repository(tmp_path: Path) -> None:
    """A new repository over the same directory finds what the last one wrote."""
    await StoryRepository(tmp_path).save(Story(slug="upload", title="Upload"))

    reopened = await StoryRepository(tmp_path).get("upload")

    assert reopened is not None
    assert reopened.title == "Upload"


async def test_deleting_removes_the_file(
    repository: StoryRepository, tmp_path: Path
) -> None:
    await repository.save(Story(slug="upload", title="Upload"))

    assert await repository.delete("upload") is True
    assert not (tmp_path / "upload.txt").exists()
    assert await repository.get("upload") is None


async def test_deleting_something_absent_says_so(repository: StoryRepository) -> None:
    assert await repository.delete("nothing-here") is False


async def test_clearing_empties_the_directory(
    repository: StoryRepository, tmp_path: Path
) -> None:
    await repository.save(Story(slug="one", title="One"))
    await repository.save(Story(slug="two", title="Two"))

    await repository.clear()

    assert await repository.list_all() == []
    assert list(tmp_path.glob("*.txt")) == []


async def test_an_id_field_that_is_not_a_string_is_refused(tmp_path: Path) -> None:
    """The id names a file, so it has to be a string; say so plainly."""

    class Numbered(BaseModel):
        slug: int
        title: str

    class NumberedRepository(FileRepositoryMixin[Numbered]):
        def __init__(self, base_path: Path) -> None:
            self.storage: dict[str, Numbered] = {}
            self.base_path = base_path
            self.entity_name = "Numbered"
            self.id_field = "slug"

        def _get_file_path(self, entity: Numbered) -> Path:
            return self.base_path / f"{entity.slug}.txt"

        def _serialize(self, entity: Numbered) -> str:
            return entity.title

        def _load_all(self) -> None:
            return None

    with pytest.raises(TypeError, match="an id must be a str"):
        await NumberedRepository(tmp_path).save(Numbered(slug=1, title="One"))
