"""What a caller asks a file store to keep.

Arguments for an upload, checked before anything is stored. Never
returned, never kept, so nothing has identity here — unlike
``FileMetadata``, which a store hands back by id and which stays an
entity (ADR 018).
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

MAX_FILE_BYTES = 50 * 1024 * 1024
"""The largest upload accepted, to keep one caller from exhausting the store."""


MAX_FILENAME_LENGTH = 255
"""What most filesystems accept in a single path component."""


DANGEROUS_IN_A_FILENAME = (
    "..",
    "~",
    "$",
    "`",
    "|",
    "&",
    ";",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
)
"""Patterns refused in a filename.

Path traversal, and shell metacharacters for the benefit of anything
downstream that hands the name to a shell.
"""


ALLOWED_CONTENT_TYPES = frozenset(
    {
        "text/plain",
        "text/csv",
        "application/json",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/zip",
        "application/octet-stream",
    }
)
"""Content types a caller may upload."""


def _a_safe_filename(name: str) -> str:
    """The filename to store, or a refusal.

    Args:
        name: What the caller asked for

    Returns:
        The name with any path components removed

    Raises:
        ValueError: If the name is empty, too long, or holds something
            dangerous
    """
    if not name or not name.strip():
        raise ValueError("Filename cannot be empty")

    # Remove any path components to prevent directory traversal
    sanitized = os.path.basename(name.strip())

    for pattern in DANGEROUS_IN_A_FILENAME:
        if pattern in sanitized:
            raise ValueError(f"Filename contains dangerous pattern: {pattern}")

    if len(sanitized) > MAX_FILENAME_LENGTH:
        raise ValueError(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")

    # Ensure filename is not empty after sanitization
    if not sanitized:
        raise ValueError("Filename is empty after sanitization")

    return str(sanitized)


@dataclass(frozen=True)
class FileUploadArgs:
    """
    Arguments for file upload with security validation.

    This model enforces security constraints at the domain level,
    ensuring that all file uploads are validated before reaching
    the repository layer.
    """

    file_id: str
    filename: str
    data: bytes
    content_type: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Check every argument, and replace the filename with a safe one.

        These were three ``field_validator`` methods. The filename one
        both refused names and rewrote them, so it has to run here and
        write its answer back rather than only raise: a caller that
        sends "../../etc/passwd" gets "passwd" stored, which is the
        point of it.

        Raises:
            ValueError: If the filename, size or content type is refused
        """
        object.__setattr__(self, "filename", _a_safe_filename(self.filename))

        if not self.data:
            raise ValueError("File cannot be empty")
        if len(self.data) > MAX_FILE_BYTES:
            raise ValueError(
                f"File size {len(self.data)} bytes exceeds maximum allowed "
                f"size of {MAX_FILE_BYTES} bytes"
            )

        if self.content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Content type '{self.content_type}' not allowed. Allowed "
                f"types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
            )
