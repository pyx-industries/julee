"""What FileUploadArgs refuses, and what it quietly rewrites.

These checks are the reason the entity exists: every upload reaching a
file storage repository has been through them. Nothing exercised them
until now, so converting the entity from a pydantic model to a frozen
dataclass moved security code that no test was watching.
"""

import pytest
from temporalio.contrib.pydantic import pydantic_data_converter

from julee.core.entities.file_storage import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_BYTES,
    MAX_FILENAME_LENGTH,
    FileMetadata,
    FileUploadArgs,
)

pytestmark = pytest.mark.unit

DATA = b"some bytes"


def an_upload(**overrides: object) -> FileUploadArgs:
    """An upload that passes every check, unless overridden."""
    fields: dict[str, object] = {
        "file_id": "f-1",
        "filename": "report.pdf",
        "data": DATA,
        "content_type": "application/pdf",
    }
    fields.update(overrides)
    return FileUploadArgs(**fields)  # type: ignore[arg-type]


class TestTheFilenameIsMadeSafe:
    """A name is not only refused or accepted; it is rewritten."""

    def test_a_path_is_reduced_to_its_last_component(self) -> None:
        """The whole point: a traversal attempt stores a plain name.

        Asserting the stored value, not merely that nothing was raised.
        A check that only confirmed no exception would pass just as well
        if the sanitising were deleted.
        """
        args = an_upload(filename="/var/tmp/report.pdf")

        assert args.filename == "report.pdf"

    def test_a_name_is_trimmed(self) -> None:
        """Padding is not part of the name."""
        assert an_upload(filename="  report.pdf  ").filename == "report.pdf"

    @pytest.mark.parametrize("name", ["", "   "])
    def test_an_empty_name_is_refused(self, name: str) -> None:
        """There is nothing to store it under."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            an_upload(filename=name)

    def test_a_traversal_that_survives_basename_is_refused(self) -> None:
        """``..`` is refused even where it is not a path separator.

        ``os.path.basename`` leaves "..foo" alone, so the pattern check
        is doing work the sanitising does not.
        """
        with pytest.raises(ValueError, match=r"dangerous pattern: \.\."):
            an_upload(filename="..foo.pdf")

    @pytest.mark.parametrize("char", ["~", "$", "`", "|", "&", ";", "(", "{", "["])
    def test_a_shell_metacharacter_is_refused(self, char: str) -> None:
        """For anything downstream that hands the name to a shell."""
        with pytest.raises(ValueError, match="dangerous pattern"):
            an_upload(filename=f"report{char}.pdf")

    def test_a_name_at_the_limit_is_allowed(self) -> None:
        """The boundary is inclusive, so off-by-one is visible."""
        name = "a" * MAX_FILENAME_LENGTH

        assert an_upload(filename=name).filename == name

    def test_a_longer_name_is_refused(self) -> None:
        """One past the limit."""
        with pytest.raises(ValueError, match="Filename too long"):
            an_upload(filename="a" * (MAX_FILENAME_LENGTH + 1))


class TestTheDataIsChecked:
    """Size, at both ends."""

    def test_an_empty_file_is_refused(self) -> None:
        """Nothing to store."""
        with pytest.raises(ValueError, match="File cannot be empty"):
            an_upload(data=b"")

    def test_a_file_at_the_limit_is_allowed(self) -> None:
        """The boundary is inclusive."""
        assert len(an_upload(data=b"a" * MAX_FILE_BYTES).data) == MAX_FILE_BYTES

    def test_a_larger_file_is_refused(self) -> None:
        """One byte past the limit, so the comparison cannot be >= by mistake."""
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            an_upload(data=b"a" * (MAX_FILE_BYTES + 1))


class TestTheContentTypeIsChecked:
    """An allowlist, not a denylist."""

    @pytest.mark.parametrize("content_type", sorted(ALLOWED_CONTENT_TYPES))
    def test_an_allowed_type_is_accepted(self, content_type: str) -> None:
        """Every type the allowlist names really is accepted."""
        assert an_upload(content_type=content_type).content_type == content_type

    def test_anything_else_is_refused(self) -> None:
        """Including one that merely looks respectable."""
        with pytest.raises(ValueError, match="not allowed"):
            an_upload(content_type="application/x-msdownload")

    def test_the_refusal_says_what_is_allowed(self) -> None:
        """So the caller can fix it without reading this file."""
        with pytest.raises(ValueError, match="application/pdf"):
            an_upload(content_type="text/html")


class TestTheRecordsAreImmutable:
    """Both are entities, so neither can be changed after construction."""

    def test_an_upload_cannot_be_changed(self) -> None:
        """Rewriting the filename after the checks would undo them."""
        args = an_upload()

        with pytest.raises(AttributeError):
            args.filename = "/etc/passwd"  # type: ignore[misc]

    def test_metadata_cannot_be_changed(self) -> None:
        """A stored file's record is a fact, not a working value."""
        with pytest.raises(AttributeError):
            FileMetadata(file_id="f-1").file_id = "f-2"  # type: ignore[misc]

    def test_a_stored_file_remembers_when_it_arrived(self) -> None:
        """Defaulted rather than required, and each record gets its own."""
        assert FileMetadata(file_id="f-1").uploaded_at


class TestItSurvivesTheTemporalBoundary:
    """A file storage call is an activity, so both records are serialised.

    They used to be pydantic models, which the converter knew how to
    rebuild. As frozen dataclasses they are rebuilt by the same
    converter through a different path, and the workflow proxy now asks
    for that by passing result_type rather than reconstructing the
    record itself.
    """

    def test_a_stored_file_record_comes_back_whole(self) -> None:
        """Every field, including the mapping and the timestamp."""
        converter = pydantic_data_converter.payload_converter
        record = FileMetadata(
            file_id="f-1",
            filename="report.pdf",
            content_type="application/pdf",
            size_bytes=3,
            metadata={"origin": "upload"},
        )

        back = converter.from_payload(converter.to_payload(record), FileMetadata)

        assert back == record

    def test_it_comes_back_as_the_entity_not_a_dict(self) -> None:
        """Equality alone would not notice a dict that merely compares.

        The proxy returns what the converter gives it, so if this were a
        dict every caller would get one where the signature promises an
        entity.
        """
        converter = pydantic_data_converter.payload_converter
        record = FileMetadata(file_id="f-1")

        back = converter.from_payload(converter.to_payload(record), FileMetadata)

        assert isinstance(back, FileMetadata)

    def test_an_upload_comes_back_whole(self) -> None:
        """The arguments travel the other way, and carry bytes."""
        converter = pydantic_data_converter.payload_converter
        args = an_upload(metadata={"origin": "test"})

        back = converter.from_payload(converter.to_payload(args), FileUploadArgs)

        assert back == args
        assert back.data == DATA
