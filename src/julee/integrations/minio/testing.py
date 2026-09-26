"""Testing support for the MinIO integration.

FakeMinioClient implements the same interface as a real MinIO client and
keeps objects in memory, so a test can assert on what was stored rather
than on which methods were called.

This is public API. Any kit or solution with MinIO repositories needs it
to test them, which is why it lives here rather than in julee's own test
tree.

A double is only worth having if it fails where the real thing fails.
``get_object`` used to answer with ``Mock(read=Mock(return_value=data))``
— a read that returned the whole object however many times it was
called, ignored its ``size`` argument, and never ran out. Real MinIO
answers with an HTTP response that is consumed as it is read, so a bug
that hands one response to two readers could not be written a test for:
the second reader got the content here and an empty bytestring in
production. That was julee#124, found in a downstream deployment rather
than by any of the tests over this.
"""

import hashlib
import io
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from functools import wraps
from typing import Any, BinaryIO, cast
from unittest.mock import Mock

from minio.api import ObjectWriteResult
from minio.datatypes import Object
from minio.error import S3Error
from urllib3 import HTTPHeaderDict
from urllib3.response import BaseHTTPResponse

from julee.integrations.minio.client import MinioClient


class _ConsumedOnRead(io.RawIOBase):
    """A response whose bytes are read once, as MinIO's is.

    Subclasses ``io.RawIOBase`` because urllib3's ``BaseHTTPResponse``
    does, and :class:`~julee.core.entities.content_stream.ContentStream`
    checks for it. The old Mock satisfied that check through its spec,
    which is the kind of thing a Mock gets right by accident and a class
    has to be told.

    Not a ``BytesIO`` either: that is seekable and a response is not, so
    a caller that rewinds would pass here and raise
    ``io.UnsupportedOperation`` against real MinIO.

    Not a Mock, because the behaviour under test is what successive
    reads return, and a Mock configured to remember that is a second
    implementation of it.
    """

    def __init__(self, data: bytes) -> None:
        super().__init__()
        self._remaining = data

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        """False, as a response streamed off a socket is."""
        return False

    def read(self, size: int | None = -1) -> bytes:
        """Take bytes off the front, as a socket would.

        Args:
            size: How many bytes, or None or -1 for the rest

        Returns:
            The bytes taken, empty once the response is spent
        """
        if size is None or size < 0:
            size = len(self._remaining)
        taken, self._remaining = self._remaining[:size], self._remaining[size:]
        return taken

    def readall(self) -> bytes:
        return self.read(-1)

    def release_conn(self) -> None:
        """What a caller calls after close(); real responses have it."""


def _as_response_headers(
    metadata: dict[str, str | list[str] | tuple[str]] | None,
    content_type: str,
    size: int,
) -> HTTPHeaderDict:
    """User metadata as MinIO gives it back: among the response headers.

    The real client passes ``response.headers`` straight through as an
    Object's metadata, so what went in as ``filename`` comes back as
    ``x-amz-meta-filename`` next to content-type and the rest.
    """
    headers = HTTPHeaderDict()
    headers["content-type"] = content_type
    headers["content-length"] = str(size)
    for key, value in (metadata or {}).items():
        if isinstance(value, list | tuple):
            value = ",".join(str(each) for each in value)
        headers[f"x-amz-meta-{key}"] = str(value)
    return headers


def requires_bucket(func: Callable) -> Callable:
    """Decorator to check if bucket exists before method execution."""

    @wraps(func)
    def wrapper(self: Any, bucket_name: str, *args: Any, **kwargs: Any) -> Any:
        if bucket_name not in self._buckets:
            raise S3Error(
                code="NoSuchBucket",
                message="Bucket does not exist",
                resource=bucket_name,
                request_id="req123",
                host_id="host123",
                response=Mock(),
            )
        return func(self, bucket_name, *args, **kwargs)

    return wrapper


def requires_object(func: Callable) -> Callable:
    """Decorator to check if object exists before method execution."""

    @wraps(func)
    def wrapper(
        self: Any,
        bucket_name: str,
        object_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if bucket_name not in self._objects:
            raise S3Error(
                code="NoSuchBucket",
                message="Bucket does not exist",
                resource=bucket_name,
                request_id="req123",
                host_id="host123",
                response=Mock(),
            )
        if object_name not in self._objects[bucket_name]:
            raise S3Error(
                code="NoSuchKey",
                message="Object not found",
                resource=object_name,
                request_id="req123",
                host_id="host123",
                response=Mock(),
            )
        return func(self, bucket_name, object_name, *args, **kwargs)

    return wrapper


class FakeMinioClient(MinioClient):
    """
    Fake Minio client that stores objects in memory for testing.

    This client implements the MinioClient protocol and stores all data in
    memory, allowing for fast state-based testing without requiring a real
    MinIO server.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, Any]] = {}
        self._objects: dict[str, dict[str, dict[str, Any]]] = {}

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        return bucket_name in self._buckets

    def make_bucket(self, bucket_name: str) -> None:
        """Create a bucket."""
        if bucket_name in self._buckets:
            raise S3Error(
                code="BucketAlreadyExists",
                message="Bucket already exists",
                resource=bucket_name,
                request_id="req123",
                host_id="host123",
                response=Mock(),
            )
        self._buckets[bucket_name] = {}
        self._objects[bucket_name] = {}

    @requires_bucket
    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str | list[str] | tuple[str]] | None = None,
    ) -> ObjectWriteResult:
        """Store an object in the bucket.

        Reads ``length`` bytes from where the stream currently is, and
        objects if there are not that many. Both halves matter and
        neither used to hold: this rewound the caller's stream first and
        then stored however much it found.

        Real MinIO never rewinds — it cannot, since a stream may be a
        socket — and it uses ``length`` as the object size, raising if
        the body is short. So a caller that handed over a
        partially-consumed stream stored the whole object here and a
        truncated one in production, and a caller whose ``length``
        disagreed with its data was told nothing (#285).
        """
        content = data.read(length)
        if len(content) != length:
            raise OSError(
                f"stream having not enough data; expected: {length}, "
                f"got: {len(content)} bytes"
            )

        self._objects[bucket_name][object_name] = {
            "data": content,
            "metadata": _as_response_headers(metadata, content_type, len(content)),
            "user_metadata": dict(metadata or {}),
            "content_type": content_type,
            "size": len(content),
            "last_modified": datetime.now(UTC),
            "etag": hashlib.md5(content).hexdigest(),
        }

        # Return a proper ObjectWriteResult
        return ObjectWriteResult(
            bucket_name=bucket_name,
            object_name=object_name,
            version_id=None,
            etag="fake-etag",
            http_headers=HTTPHeaderDict(),
            last_modified=datetime.now(UTC),
            location=f"/{bucket_name}/{object_name}",
        )

    @requires_object
    def get_object(self, bucket_name: str, object_name: str) -> BaseHTTPResponse:
        """Retrieve an object from the bucket.

        The response is consumed as it is read, like the real one: a
        second read returns b"" rather than the object again. Anything
        that needs the bytes twice has to keep them, which is what the
        caller must do in production anyway.
        """
        obj_info = self._objects[bucket_name][object_name]
        # Structural, not nominal: callers use read/close/release_conn,
        # and BaseHTTPResponse is a urllib3 class with a constructor this
        # has no business calling.
        return cast(BaseHTTPResponse, _ConsumedOnRead(obj_info["data"]))

    @requires_object
    def stat_object(self, bucket_name: str, object_name: str) -> Object:
        """Get object metadata without retrieving the object data.

        ``metadata`` is the response headers, as the real client's is,
        so user metadata appears under ``x-amz-meta-*``. It used to be
        the dict the caller passed to put_object, which meant
        ``stat.metadata["filename"]`` worked here and returned nothing
        in production (#285).
        """
        obj_info = self._objects[bucket_name][object_name]
        return Object(
            bucket_name=bucket_name,
            object_name=object_name,
            last_modified=obj_info["last_modified"],
            etag=obj_info["etag"],
            size=obj_info["size"],
            content_type=obj_info["content_type"],
            metadata=obj_info["metadata"],
        )

    @requires_bucket
    def list_objects(self, bucket_name: str, prefix: str = "") -> Iterator[Object]:
        """List objects in a bucket with optional prefix filter.

        A generator, as the real one is, so it is consumed by whoever
        iterates it first. Returning a list let a caller iterate twice
        and get two full passes here and one-then-empty in production.

        It yields ``Object``, not ``Mock``. A Mock answers every
        attribute plausibly, so ``obj.is_dir`` was truthy and a caller
        filtering on it skipped everything here and nothing there
        (#285).

        A bucket that does not exist raises rather than listing nothing,
        which is what the protocol says and what a typo deserves.
        """
        for object_name, obj_info in sorted(self._objects[bucket_name].items()):
            if object_name.startswith(prefix):
                yield Object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    last_modified=obj_info["last_modified"],
                    etag=obj_info["etag"],
                    size=obj_info["size"],
                    content_type=obj_info["content_type"],
                    metadata=obj_info["metadata"],
                )

    @requires_bucket
    def remove_object(self, bucket_name: str, object_name: str) -> None:
        """Remove an object from the bucket.

        Idempotent, because S3's DELETE is: removing something that is
        not there is not an error. This used to raise NoSuchKey, which
        failed code that works in production (#285).
        """
        self._objects[bucket_name].pop(object_name, None)

    # Inspection methods for testing
    def get_stored_objects(self, bucket_name: str) -> dict[str, dict[str, Any]]:
        """Get all stored objects in a bucket (for testing purposes)."""
        return self._objects.get(bucket_name, {}).copy()

    def get_object_count(self, bucket_name: str) -> int:
        """Get the number of objects in a bucket (for testing purposes)."""
        return len(self._objects.get(bucket_name, {}))

    def get_total_object_count(self) -> int:
        """Get total number of objects across all buckets (for testing)."""
        return sum(len(objects) for objects in self._objects.values())

    def clear_all_data(self) -> None:
        """Clear all buckets and objects (for testing purposes)."""
        self._buckets.clear()
        self._objects.clear()
