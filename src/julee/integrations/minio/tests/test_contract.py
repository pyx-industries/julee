"""What MinIO does, asserted against MinIO and against the double.

A double is only worth having if it fails where the real thing fails.
These assertions ran against :class:`FakeMinioClient` alone until #298,
and the double had drifted four times without any of them noticing:
#124 (one response handed to two readers), #90 (a rewind that works on
BytesIO and raises on a socket), #285 (put_object rewinding its input,
stat_object answering with the caller's own dict, remove_object raising
where S3 is idempotent, list_objects yielding Mocks) and #287
(list_objects ignoring `recursive`). Every one was found by a downstream
deployment.

So each test runs twice, over the same assertions: once against the
double, once against a real MinIO when one is reachable. Whatever the
double is allowed to get away with here, it is allowed to get away with
in every kit and solution that tests against it.

The `client` fixture, and how the real half is required rather than
skipped in CI, are in conftest.py.
"""

import io
from typing import BinaryIO, cast

import pytest
from minio.datatypes import Object
from minio.error import S3Error

from julee.core.entities.content_stream import ContentStream
from julee.integrations.minio.client import MinioClient

from .conftest import CONTENT


class TestReadingAResponse:
    def test_the_first_read_returns_the_object(
        self, client: MinioClient, bucket: str
    ) -> None:
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        assert response.read() == CONTENT

    def test_a_second_read_returns_nothing(
        self, client: MinioClient, bucket: str
    ) -> None:
        """As a real HTTP response does. A double that answered with the
        object again would hide every bug about handing one response to
        two readers — which is what it did, and julee#124 is what got
        through (a downstream deployment served empty content for the
        second of two documents with identical bytes)."""
        response = client.get_object(bucket_name=bucket, object_name="an-object")
        response.read()

        assert response.read() == b""

    def test_a_size_takes_only_that_many_bytes(
        self, client: MinioClient, bucket: str
    ) -> None:
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        assert response.read(4) == CONTENT[:4]

    def test_reading_in_pieces_gives_the_whole_object(
        self, client: MinioClient, bucket: str
    ) -> None:
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        pieces = [response.read(7) for _ in range(10)]

        assert b"".join(pieces) == CONTENT

    def test_a_negative_size_takes_the_rest(
        self, client: MinioClient, bucket: str
    ) -> None:
        response = client.get_object(bucket_name=bucket, object_name="an-object")
        response.read(4)

        assert response.read(-1) == CONTENT[4:]

    def test_each_call_to_get_object_starts_a_new_response(
        self, client: MinioClient, bucket: str
    ) -> None:
        """Consuming one does not consume the stored object — asking
        again is how a caller reads the same content twice."""
        client.get_object(bucket_name=bucket, object_name="an-object").read()

        second = client.get_object(bucket_name=bucket, object_name="an-object")

        assert second.read() == CONTENT

    def test_two_responses_for_one_object_are_independent(
        self, client: MinioClient, bucket: str
    ) -> None:
        first = client.get_object(bucket_name=bucket, object_name="an-object")
        second = client.get_object(bucket_name=bucket, object_name="an-object")

        first.read()

        assert second.read() == CONTENT

    def test_an_empty_object_reads_empty(
        self, client: MinioClient, bucket: str
    ) -> None:
        client.put_object(
            bucket_name=bucket,
            object_name="nothing",
            data=io.BytesIO(b""),
            length=0,
        )

        response = client.get_object(bucket_name=bucket, object_name="nothing")

        assert response.read() == b""

    def test_a_response_can_be_closed(self, client: MinioClient, bucket: str) -> None:
        """Callers close and release; both have to be there to be called."""
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        response.close()
        response.release_conn()


class TestBeingTheRightKindOfStream:
    """Properties ContentStream and its callers rely on."""

    def test_the_response_is_an_io_stream(
        self, client: MinioClient, bucket: str
    ) -> None:
        """ContentStream refuses anything that is not, and urllib3's
        BaseHTTPResponse is one. The old Mock passed this through its
        spec — right by accident."""
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        assert isinstance(response, io.IOBase)

    def test_a_content_stream_can_wrap_it(
        self, client: MinioClient, bucket: str
    ) -> None:
        """The thing every binary read in this integration does."""
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        assert ContentStream(response).read() == CONTENT

    def test_the_response_is_not_seekable(
        self, client: MinioClient, bucket: str
    ) -> None:
        """A response streamed off a socket is not, and a double that
        allowed rewinding would pass a caller that raises
        io.UnsupportedOperation against real MinIO (#90)."""
        response = client.get_object(bucket_name=bucket, object_name="an-object")

        assert not response.seekable()

    def test_rewinding_it_raises(self, client: MinioClient, bucket: str) -> None:
        response = client.get_object(bucket_name=bucket, object_name="an-object")
        response.read()

        with pytest.raises(io.UnsupportedOperation):
            response.seek(0)


class TestStoringAnObject:
    """put_object reads forward, and reads what it was told to (#285)."""

    def test_it_reads_from_where_the_stream_is(
        self, client: MinioClient, bucket: str
    ) -> None:
        """It used to rewind first. Real MinIO cannot — a stream may be
        a socket — so a caller handing over a half-read stream stored
        the whole object here and a truncated one in production."""
        stream = io.BytesIO(b"0123456789")
        stream.read(6)

        client.put_object(bucket_name=bucket, object_name="tail", data=stream, length=4)

        response = client.get_object(bucket_name=bucket, object_name="tail")
        assert response.read() == b"6789"

    def test_it_stores_exactly_the_length_it_was_given(
        self, client: MinioClient, bucket: str
    ) -> None:
        stream = io.BytesIO(b"0123456789")

        client.put_object(bucket_name=bucket, object_name="head", data=stream, length=4)

        response = client.get_object(bucket_name=bucket, object_name="head")
        assert response.read() == b"0123"

    def test_a_stream_shorter_than_its_length_is_objected_to(
        self, client: MinioClient, bucket: str
    ) -> None:
        """Real MinIO raises 'expected: N'. Saying nothing let a caller
        whose length disagreed with its data pass here and fail there."""
        with pytest.raises(OSError, match="expected: 10"):
            client.put_object(
                bucket_name=bucket,
                object_name="short",
                data=io.BytesIO(b"four"),
                length=10,
            )

    def test_a_stream_that_cannot_be_rewound_is_accepted(
        self, client: MinioClient, bucket: str
    ) -> None:
        """It only ever reads forward, so there is nothing to object to.
        The old implementation called seek() on anything that had the
        method — which a non-seekable stream does, raising."""
        source = client.get_object(bucket_name=bucket, object_name="an-object")

        client.put_object(
            bucket_name=bucket,
            object_name="copied",
            # A response is what a caller copying between buckets has to
            # hand over, and it is a readable binary stream. The
            # protocol says BinaryIO, which a urllib3 response does not
            # nominally satisfy and does structurally.
            data=cast(BinaryIO, source),
            length=len(CONTENT),
        )

        response = client.get_object(bucket_name=bucket, object_name="copied")
        assert response.read() == CONTENT

    def test_the_stored_object_can_be_stat_ed(
        self, client: MinioClient, bucket: str
    ) -> None:
        stat = client.stat_object(bucket_name=bucket, object_name="an-object")

        assert stat.size == len(CONTENT)


class TestListingObjects:
    """list_objects is a generator of Objects (#285)."""

    def test_it_is_consumed_by_whoever_iterates_it(
        self, client: MinioClient, bucket: str
    ) -> None:
        """A generator, as the real one is. Returning a list let a
        caller iterate twice and get two full passes here and
        one-then-empty in production."""
        listing = client.list_objects(bucket_name=bucket)

        assert len(list(listing)) == 1
        assert list(listing) == []

    def test_each_call_starts_a_new_listing(
        self, client: MinioClient, bucket: str
    ) -> None:
        assert len(list(client.list_objects(bucket_name=bucket))) == 1
        assert len(list(client.list_objects(bucket_name=bucket))) == 1

    def test_it_yields_objects_not_mocks(
        self, client: MinioClient, bucket: str
    ) -> None:
        """A Mock answers every attribute plausibly, so is_dir came back
        truthy and a caller filtering on it skipped everything here and
        nothing in production."""
        (listed,) = client.list_objects(bucket_name=bucket)

        assert isinstance(listed, Object)
        assert listed.object_name == "an-object"
        assert listed.size == len(CONTENT)
        assert listed.last_modified is not None
        assert not listed.is_dir

    def test_a_prefix_selects(self, client: MinioClient, bucket: str) -> None:
        client.put_object(
            bucket_name=bucket,
            object_name="other",
            data=io.BytesIO(b"x"),
            length=1,
        )

        names = [o.object_name for o in client.list_objects(bucket, prefix="an-")]

        assert names == ["an-object"]

    def test_a_bucket_that_does_not_exist_raises(
        self, client: MinioClient, bucket: str
    ) -> None:
        """It used to list nothing, so a typo'd bucket name passed. The
        protocol says raise, and a rule that finds nothing passing is
        the failure this estate keeps closing."""
        with pytest.raises(S3Error):
            list(client.list_objects(bucket_name="not-a-bucket"))


class TestRemovingAnObject:
    def test_removing_one_that_is_there_removes_it(
        self, client: MinioClient, bucket: str
    ) -> None:
        client.remove_object(bucket_name=bucket, object_name="an-object")

        assert list(client.list_objects(bucket_name=bucket)) == []

    def test_removing_one_that_is_not_there_is_not_an_error(
        self, client: MinioClient, bucket: str
    ) -> None:
        """S3's DELETE is idempotent. Raising NoSuchKey failed code that
        works in production (#285)."""
        client.remove_object(bucket_name=bucket, object_name="never-existed")

    def test_removing_from_a_bucket_that_is_not_there_raises(
        self, client: MinioClient, bucket: str
    ) -> None:
        with pytest.raises(S3Error):
            client.remove_object(bucket_name="not-a-bucket", object_name="x")


class TestObjectMetadata:
    """stat_object answers with response headers, as the real one does."""

    def test_user_metadata_comes_back_prefixed(
        self, client: MinioClient, bucket: str
    ) -> None:
        """Real MinIO passes response.headers straight through, so what
        went in as 'filename' comes back as 'x-amz-meta-filename'.
        julee.integrations.minio.file_storage already reads it that way,
        and the old double could never produce that key (#285)."""
        client.put_object(
            bucket_name=bucket,
            object_name="described",
            data=io.BytesIO(b"x"),
            length=1,
            metadata={"filename": "spec.pdf"},
        )

        stat = client.stat_object(bucket_name=bucket, object_name="described")

        assert stat.metadata is not None
        assert stat.metadata["x-amz-meta-filename"] == "spec.pdf"

    def test_the_headers_carry_the_content_type(
        self, client: MinioClient, bucket: str
    ) -> None:
        client.put_object(
            bucket_name=bucket,
            object_name="typed",
            data=io.BytesIO(b"x"),
            length=1,
            content_type="application/pdf",
        )

        stat = client.stat_object(bucket_name=bucket, object_name="typed")

        assert stat.content_type == "application/pdf"

    def test_the_etag_distinguishes_different_content(
        self, client: MinioClient, bucket: str
    ) -> None:
        """It was the constant "fake-etag" for every object."""
        client.put_object(
            bucket_name=bucket,
            object_name="other",
            data=io.BytesIO(b"different"),
            length=9,
        )

        first = client.stat_object(bucket_name=bucket, object_name="an-object")
        second = client.stat_object(bucket_name=bucket, object_name="other")

        assert first.etag != second.etag


class TestListingWithoutRecursion:
    """The delimiter S3 applies when recursive is False (#287).

    `recursive` maps to `delimiter=None if recursive else "/"`. With a
    delimiter, anything more than one level below the prefix comes back
    as a single common-prefix entry instead of the objects under it.

    The double listed everything whatever was asked, which is minio's
    recursive=True — so a caller that nested its keys got every object
    here and one entry per directory in production.
    """

    @pytest.fixture
    def nested(self, client: MinioClient, bucket: str) -> MinioClient:
        for name in ("spec/flat", "spec/t1/a", "spec/t1/b", "spec/t2/c"):
            client.put_object(
                bucket_name=bucket,
                object_name=name,
                data=io.BytesIO(b"x"),
                length=1,
            )
        return client

    def test_a_deeper_key_comes_back_as_its_common_prefix(
        self, nested: MinioClient, bucket: str
    ) -> None:
        names = [o.object_name for o in nested.list_objects(bucket, "spec/")]

        assert names == ["spec/flat", "spec/t1/", "spec/t2/"]

    def test_the_common_prefix_says_it_is_one(
        self, nested: MinioClient, bucket: str
    ) -> None:
        """is_dir is what a caller would have to check, and it is derived
        from the trailing slash rather than asserted by this double."""
        by_name = {o.object_name: o for o in nested.list_objects(bucket, "spec/")}

        assert by_name["spec/t1/"].is_dir
        assert not by_name["spec/flat"].is_dir

    def test_each_directory_is_reported_once(
        self, nested: MinioClient, bucket: str
    ) -> None:
        """Two objects under spec/t1/ are one entry, not two."""
        names = [o.object_name for o in nested.list_objects(bucket, "spec/")]

        assert names.count("spec/t1/") == 1

    def test_recursive_gives_every_object(
        self, nested: MinioClient, bucket: str
    ) -> None:
        names = [
            o.object_name for o in nested.list_objects(bucket, "spec/", recursive=True)
        ]

        assert names == ["spec/flat", "spec/t1/a", "spec/t1/b", "spec/t2/c"]

    def test_one_level_of_nesting_is_unaffected(
        self, client: MinioClient, bucket: str
    ) -> None:
        """Which is why nothing in the estate is broken: every prefix in
        use is exactly one level deep."""
        for name in ("query/q1", "query/q2"):
            client.put_object(
                bucket_name=bucket,
                object_name=name,
                data=io.BytesIO(b"x"),
                length=1,
            )

        names = [o.object_name for o in client.list_objects(bucket, "query/")]

        assert names == ["query/q1", "query/q2"]
