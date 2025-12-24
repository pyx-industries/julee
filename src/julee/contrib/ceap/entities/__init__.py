"""
Domain models for julee.

This package contains all the domain entities and value objects following
Clean Architecture principles. These models are framework-independent and
contain only business logic.

Re-exports commonly used models for convenient importing:
    from julee.contrib.ceap.entities import Document, Assembly, Policy
"""

# Document models
# Assembly models
# Custom field types (ContentStream moved to core)
from julee.core.entities.content_stream import ContentStream

from .assembly import Assembly, AssemblyStatus
from .assembly_specification import (
    AssemblySpecification,
    AssemblySpecificationStatus,
)
from .document import Document, DocumentStatus
from .document_policy_validation import (
    DocumentPolicyValidation,
    DocumentPolicyValidationStatus,
)

# Configuration models
from .knowledge_service_config import KnowledgeServiceConfig
from .knowledge_service_query import KnowledgeServiceQuery

# Policy models
from .policy import Policy, PolicyStatus

__all__ = [
    # Document models
    "Document",
    "DocumentStatus",
    "ContentStream",
    # Assembly models
    "Assembly",
    "AssemblyStatus",
    "AssemblySpecification",
    "AssemblySpecificationStatus",
    "KnowledgeServiceQuery",
    # Configuration models
    "KnowledgeServiceConfig",
    # Policy models
    "Policy",
    "PolicyStatus",
    "DocumentPolicyValidation",
    "DocumentPolicyValidationStatus",
]
