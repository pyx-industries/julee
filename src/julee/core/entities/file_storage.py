"""File storage entities.

The records a file storage repository deals in: what was uploaded, and
what is known about a stored file. They are framework-level because
storing a file is not a domain concept, unlike the documents, credentials
or specifications a solution stores.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class FileMetadata:
    """Metadata about a stored file."""

    file_id: str
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    uploaded_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: Mapping[str, str] = field(default_factory=dict)
