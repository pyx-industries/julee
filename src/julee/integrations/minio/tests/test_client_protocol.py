"""
Tests to verify protocol compatibility between real Minio client and protocol.

This module tests that the real minio.Minio client properly implements our
MinioClient protocol, ensuring that our protocol definition matches the
actual interface.
"""

import io
import logging

import pytest
from minio import Minio

from ..client import MinioClient, MinioRepositoryMixin
from ..testing import FakeMinioClient

pytestmark = pytest.mark.unit


class TestMinioClientProtocol:
    """Test that the real Minio client implements our protocol."""

    def test_real_minio_client_implements_protocol(self) -> None:
        """Test that minio.Minio implements MinioClient protocol."""
        # Create a real Minio client (doesn't need to connect)
        real_client = Minio("localhost:9000")

        # This should pass if the protocol is correctly defined
        assert isinstance(real_client, MinioClient)

    def test_protocol_method_signatures_match_real_client(self) -> None:
        """Test that protocol method signatures match the real client."""
        real_client = Minio("localhost:9000")

        # Test that all protocol methods exist on the real client
        assert hasattr(real_client, "bucket_exists")
        assert hasattr(real_client, "make_bucket")
        assert hasattr(real_client, "put_object")
        assert hasattr(real_client, "get_object")
        assert hasattr(real_client, "stat_object")

        # Test that methods are callable
        assert callable(real_client.bucket_exists)
        assert callable(real_client.make_bucket)
        assert callable(real_client.put_object)
        assert callable(real_client.get_object)
        assert callable(real_client.stat_object)

    def test_protocol_accepts_real_minio_client(self) -> None:
        """A repository built on the protocol accepts a real MinIO client.

        The repository stands in for whatever a kit writes: all the
        protocol asks of it is that the client it stores satisfies
        MinioClient.
        """

        class Repository:
            def __init__(self, client: MinioClient) -> None:
                self.client = client

        # No connection is attempted in the constructor, and nothing here
        # calls a method that would reach the network.
        real_client = Minio("localhost:9000")

        repository = Repository(real_client)

        assert repository.client is real_client
        assert isinstance(repository.client, MinioClient)


class TestExtractingIdsFromAListing:
    """What list_objects_with_prefix_extract_ids asks the client for.

    It reads an id off the end of each object name, so it needs objects
    and not directories. Against a client listing one level, a key like
    spec/<tenant>/<id> comes back as spec/<tenant>/ and the id extracted
    from it is "<tenant>/" — not a short answer, a wrong one shaped like
    an id (#287).
    """

    class _Repository(MinioRepositoryMixin):
        def __init__(self, client: FakeMinioClient) -> None:
            self.client = client
            self.logger = logging.getLogger("test")

    @pytest.fixture
    def repository(self) -> "_Repository":
        client = FakeMinioClient()
        client.make_bucket("specs")
        for name in ("spec/t1/a", "spec/t1/b", "spec/plain"):
            client.put_object(
                bucket_name="specs",
                object_name=name,
                data=io.BytesIO(b"x"),
                length=1,
            )
        return TestExtractingIdsFromAListing._Repository(client)

    def test_it_reaches_ids_below_a_directory(self, repository: "_Repository") -> None:
        """Would be ['plain', 't1/'] if it listed one level."""
        found = repository.list_objects_with_prefix_extract_ids(
            bucket_name="specs", prefix="spec/", entity_type_name="specs"
        )

        assert sorted(found) == ["plain", "t1/a", "t1/b"]

    def test_no_id_is_a_directory(self, repository: "_Repository") -> None:
        """The property that matters, said without depending on the
        particular keys above."""
        found = repository.list_objects_with_prefix_extract_ids(
            bucket_name="specs", prefix="spec/", entity_type_name="specs"
        )

        assert not any(entity_id.endswith("/") for entity_id in found)
