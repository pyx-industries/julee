"""UN Transparency Protocol (UNTP) projection layer.

This contrib module provides UNTP vocabulary entities and projection use cases
for mapping julee pipeline execution to W3C Verifiable Credentials.

Key insight: UNTP is not the domain model - it's a standardized vocabulary
for expressing what julee pipelines do. Core produces execution records;
contrib/untp projects them to UNTP credentials.

Architecture:
- julee/core: UseCaseExecution with operation_records (knows nothing about UNTP)
- julee/supply_chain: Service protocol decorators (@transformation, @transaction, etc.)
- julee/contrib/untp: Projects operation_records to UNTP events

UNTP Credential Types:
- DPP (Digital Product Passport): Projects from PipelineOutput
- DCC (Digital Conformity Credential): Projects from validation operations
- DFR (Digital Facility Record): Facility information and compliance
- DTE (Digital Traceability Event): Projects from OperationRecord
- DIA (Digital Identity Attestation): Organization identity verification

Import from submodules directly:
    from julee.contrib.untp.entities.credential import DigitalProductPassport
    from julee.contrib.untp.entities.event import TransformationEvent

.. seealso::

   `UNTP Specification <https://uncefact.github.io/spec-untp/>`_
       Complete UN Transparency Protocol specification.

   `W3C VC Data Model <https://www.w3.org/TR/vc-data-model-2.0/>`_
       Verifiable Credentials specification that UNTP builds upon.
"""
