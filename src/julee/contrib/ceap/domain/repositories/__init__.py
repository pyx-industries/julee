"""
Repository protocols for the CEAP (Capture, Extract, Assemble, Publish) domain.

This module exports all repository protocol interfaces for the CEAP workflow,
following the Clean Architecture patterns established in the Julee framework.
"""

from .assembly import AssemblyRepository
from .assembly_specification import AssemblySpecificationRepository
from .document import DocumentRepository
from .document_policy_validation import DocumentPolicyValidationRepository
from .knowledge_service_config import KnowledgeServiceConfigRepository
from .knowledge_service_query import KnowledgeServiceQueryRepository
from .policy import PolicyRepository
from .remote_schema import RemoteSchemaRepository

__all__ = [
    "DocumentRepository",
    "AssemblyRepository",
    "AssemblySpecificationRepository",
    "KnowledgeServiceConfigRepository",
    "KnowledgeServiceQueryRepository",
    "PolicyRepository",
    "DocumentPolicyValidationRepository",
    "RemoteSchemaRepository",
]
