"""The two clients the contract suite runs against.

A double is only worth having if it fails where the real thing fails,
and the only way to know is to ask both the same questions. Every test
in test_contract.py takes the ``client`` fixture, which is parametrised
over :class:`~julee.integrations.minio.testing.FakeMinioClient` and a
real ``Minio``.

The real half runs when ``MINIO_ENDPOINT`` names a server. Without one
it skips, so a developer with no MinIO still gets the suite — and CI
sets ``JULEE_REQUIRE_MINIO`` so that a job which loses its service
container fails instead of skipping. A contract suite that quietly runs
against one implementation is the shape of every bug it exists to catch.
"""

import io
import os
import uuid
from collections.abc import Iterator

import pytest
from minio import Minio

from julee.integrations.minio.client import MinioClient
from julee.integrations.minio.testing import FakeMinioClient

CONTENT = b"a pdf, or something like one"


def _real_client() -> Minio:
    """A client for the MinIO named by the environment.

    Raises:
        pytest.skip.Exception: when no server is named and CI has not
            said there must be one
    """
    endpoint = os.environ.get("MINIO_ENDPOINT")
    if not endpoint:
        if os.environ.get("JULEE_REQUIRE_MINIO"):
            raise AssertionError(
                "JULEE_REQUIRE_MINIO is set and MINIO_ENDPOINT is not. "
                "This job exists to run these assertions against MinIO; "
                "skipping them would report success for doing nothing."
            )
        pytest.skip("No MINIO_ENDPOINT — set one to check the double against it")

    return Minio(
        endpoint,
        access_key=os.environ.get("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.environ.get("MINIO_SECRET_KEY", "minioadmin"),
        secure=os.environ.get("MINIO_SECURE", "").lower() == "true",
    )


def _empty(client: MinioClient, bucket: str) -> None:
    """Remove every object in a bucket, so the bucket can go."""
    for obj in list(client.list_objects(bucket, recursive=True)):
        if obj.object_name is not None:
            client.remove_object(bucket, obj.object_name)


@pytest.fixture
def bucket() -> str:
    """A bucket name of this test's own.

    Unique because the real half shares one server across a parallel
    run, and because a test that cleans up after another test's failure
    is a test that reports the wrong thing.
    """
    return f"contract-{uuid.uuid4().hex[:12]}"


@pytest.fixture(
    params=[
        pytest.param("fake", id="fake"),
        pytest.param("real", id="real", marks=pytest.mark.contract),
    ]
)
def client(request: pytest.FixtureRequest, bucket: str) -> Iterator[MinioClient]:
    """A MinIO client with ``bucket`` made and one object in it.

    Yields:
        The double, then a real client if one is reachable
    """
    made: MinioClient = FakeMinioClient() if request.param == "fake" else _real_client()

    made.make_bucket(bucket)
    made.put_object(
        bucket_name=bucket,
        object_name="an-object",
        data=io.BytesIO(CONTENT),
        length=len(CONTENT),
    )

    try:
        yield made
    finally:
        if isinstance(made, Minio):
            # A real server keeps what it is given. remove_bucket is not
            # on MinioClient because julee never calls it; tidying up
            # after a test is not a reason to widen a protocol.
            _empty(made, bucket)
            made.remove_bucket(bucket)
