"""Tests for the MinIO double.

A double earns its keep by failing where the real thing fails. These say
what a response does as it is read, because that is the property the
double used not to have and the reason julee#124 could not be caught by
any test over the code that had the bug.
"""

import io

import pytest

from julee.core.entities.content_stream import ContentStream
from julee.integrations.minio.testing import FakeMinioClient

pytestmark = pytest.mark.unit

CONTENT = b"a pdf, or something like one"


@pytest.fixture
def client() -> FakeMinioClient:
    fake = FakeMinioClient()
    fake.make_bucket("content")
    fake.put_object(
        bucket_name="content",
        object_name="an-object",
        data=io.BytesIO(CONTENT),
        length=len(CONTENT),
    )
    return fake


class TestReadingAResponse:
    def test_the_first_read_returns_the_object(self, client: FakeMinioClient) -> None:
        response = client.get_object(bucket_name="content", object_name="an-object")

        assert response.read() == CONTENT

    def test_a_second_read_returns_nothing(self, client: FakeMinioClient) -> None:
        """As a real HTTP response does. A double that answered with the
        object again would hide every bug about handing one response to
        two readers — which is what it did, and julee#124 is what got
        through (a downstream deployment served empty content for the
        second of two documents with identical bytes)."""
        response = client.get_object(bucket_name="content", object_name="an-object")
        response.read()

        assert response.read() == b""

    def test_a_size_takes_only_that_many_bytes(self, client: FakeMinioClient) -> None:
        response = client.get_object(bucket_name="content", object_name="an-object")

        assert response.read(4) == CONTENT[:4]

    def test_reading_in_pieces_gives_the_whole_object(
        self, client: FakeMinioClient
    ) -> None:
        response = client.get_object(bucket_name="content", object_name="an-object")

        pieces = [response.read(7) for _ in range(10)]

        assert b"".join(pieces) == CONTENT

    def test_a_negative_size_takes_the_rest(self, client: FakeMinioClient) -> None:
        response = client.get_object(bucket_name="content", object_name="an-object")
        response.read(4)

        assert response.read(-1) == CONTENT[4:]

    def test_each_call_to_get_object_starts_a_new_response(
        self, client: FakeMinioClient
    ) -> None:
        """Consuming one does not consume the stored object — asking
        again is how a caller reads the same content twice."""
        client.get_object(bucket_name="content", object_name="an-object").read()

        second = client.get_object(bucket_name="content", object_name="an-object")

        assert second.read() == CONTENT

    def test_two_responses_for_one_object_are_independent(
        self, client: FakeMinioClient
    ) -> None:
        first = client.get_object(bucket_name="content", object_name="an-object")
        second = client.get_object(bucket_name="content", object_name="an-object")

        first.read()

        assert second.read() == CONTENT

    def test_an_empty_object_reads_empty(self, client: FakeMinioClient) -> None:
        client.put_object(
            bucket_name="content",
            object_name="nothing",
            data=io.BytesIO(b""),
            length=0,
        )

        response = client.get_object(bucket_name="content", object_name="nothing")

        assert response.read() == b""

    def test_a_response_can_be_closed(self, client: FakeMinioClient) -> None:
        """Callers close and release; both have to be there to be called."""
        response = client.get_object(bucket_name="content", object_name="an-object")

        response.close()
        response.release_conn()


class TestBeingTheRightKindOfStream:
    """Properties ContentStream and its callers rely on."""

    def test_the_response_is_an_io_stream(self, client: FakeMinioClient) -> None:
        """ContentStream refuses anything that is not, and urllib3's
        BaseHTTPResponse is one. The old Mock passed this through its
        spec — right by accident."""
        response = client.get_object(bucket_name="content", object_name="an-object")

        assert isinstance(response, io.IOBase)

    def test_a_content_stream_can_wrap_it(self, client: FakeMinioClient) -> None:
        """The thing every binary read in this integration does."""
        response = client.get_object(bucket_name="content", object_name="an-object")

        assert ContentStream(response).read() == CONTENT

    def test_the_response_is_not_seekable(self, client: FakeMinioClient) -> None:
        """A response streamed off a socket is not, and a double that
        allowed rewinding would pass a caller that raises
        io.UnsupportedOperation against real MinIO (#90)."""
        response = client.get_object(bucket_name="content", object_name="an-object")

        assert not response.seekable()

    def test_rewinding_it_raises(self, client: FakeMinioClient) -> None:
        response = client.get_object(bucket_name="content", object_name="an-object")
        response.read()

        with pytest.raises(io.UnsupportedOperation):
            response.seek(0)
