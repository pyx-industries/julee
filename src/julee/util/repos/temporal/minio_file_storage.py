from julee.util.repos.minio.file_storage import MinioFileStorageRepository
from julee.util.temporal.decorators import temporal_activity_registration


@temporal_activity_registration("util.file_storage.minio")
class TemporalMinioFileStorageRepository(MinioFileStorageRepository):
    """
    Temporal activity wrapper for MinioFileStorageRepository.
    All async methods automatically wrapped as activities.
    """

    pass
