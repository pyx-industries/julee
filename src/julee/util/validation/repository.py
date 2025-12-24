"""
Repository validation utilities for ensuring architectural contracts.

This module provides functions to validate repository implementations against
their defined Protocols using @runtime_checkable.
"""

import logging
from typing import TypeVar

logger = logging.getLogger(__name__)

P = TypeVar("P")


class RepositoryValidationError(Exception):
    """Raised when repository contract validation fails"""

    pass


def validate_repository_protocol(repository: object, protocol: type[P]) -> None:
    """
    Validate that a repository implementation satisfies a protocol contract.

    Uses Python's built-in isinstance() with @runtime_checkable for robust,
    idiomatic protocol validation.

    Args:
        repository: The repository implementation to validate
        protocol: The protocol class to validate against

    Raises:
        RepositoryValidationError: If validation fails

    Example:
        >>> from julee.util.validation.repository import validate_repository_protocol
        >>> from julee.contrib.ceap.repositories import DocumentRepository
        >>> repo = MinioDocumentRepository()
        >>> validate_repository_protocol(repo, DocumentRepository)
    """
    logger.debug(
        "Validating repository protocol",
        extra={
            "repository_type": type(repository).__name__,
            "protocol_name": protocol.__name__,
        },
    )

    if not isinstance(repository, protocol):
        error_message = (
            f"Repository {type(repository).__name__} does not implement "
            f"{protocol.__name__} protocol. Missing or incorrect methods."
        )

        logger.error(
            "Repository protocol validation failed",
            extra={
                "repository_type": type(repository).__name__,
                "protocol_name": protocol.__name__,
            },
        )

        raise RepositoryValidationError(error_message)

    logger.info(
        "Repository protocol validation passed",
        extra={
            "repository_type": type(repository).__name__,
            "protocol_name": protocol.__name__,
        },
    )


def ensure_repository_protocol(repository: object, protocol: type[P]) -> P:
    """
    Validate and return a repository with proper type annotation.

    This provides both runtime validation and static type checking benefits.

    Args:
        repository: The repository implementation to validate
        protocol: The protocol class to validate against

    Returns:
        The validated repository (type checker knows it satisfies the
        protocol)

    Raises:
        RepositoryValidationError: If validation fails

    Example:
        >>> from julee.util.validation.repository import ensure_repository_protocol
        >>> from julee.contrib.ceap.repositories import DocumentRepository
        >>> repo = MinioDocumentRepository()
        >>> validated_repo = ensure_repository_protocol(repo, DocumentRepository)
        >>> # Type checker now knows validated_repo satisfies DocumentRepository
    """
    validate_repository_protocol(repository, protocol)
    return repository  # type: ignore[return-value]
