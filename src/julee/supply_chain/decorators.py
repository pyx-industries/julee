"""Supply chain semantic decorators for service protocols.

These decorators assert supply chain semantics on service protocol definitions.
When a service protocol is decorated, it declares that all implementations
of that service perform a specific type of supply chain operation.

This enables UNTP projection: when a use case execution records an
OperationRecord with a service_type, we can look up the service's
supply chain operation type and project to the appropriate UNTP event.

Example usage:

    from typing import Protocol
    from julee.supply_chain.decorators import transformation

    @transformation
    class MaterialProcessingService(Protocol):
        '''Service that transforms input materials to output products.'''
        def process(self, inputs: list[Material]) -> list[Product]: ...

The decorators align with EPCIS (Electronic Product Code Information Services)
event types, which are the foundation of UNTP traceability events:

- transformation: Inputs consumed, outputs produced (manufacturing, processing)
- transaction: Business exchange between parties (ship, receive, transfer)
- observation: Status check without modification (inspect, verify, audit)
- aggregation: Pack/unpack operations (palletize, depalletize)
"""

from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class SupplyChainOperationType(str, Enum):
    """EPCIS-aligned operation types for supply chain semantics.

    These types correspond to the four fundamental event types in EPCIS,
    which UNTP builds upon for supply chain traceability.
    """

    TRANSFORMATION = "transformation"
    """Inputs are consumed and outputs are produced.

    Examples: Manufacturing, processing, assembly, disassembly.
    In UNTP: Projects to TransformationEvent.
    """

    TRANSACTION = "transaction"
    """Business transaction between parties.

    Examples: Shipping, receiving, transferring ownership.
    In UNTP: Projects to TransactionEvent.
    """

    OBSERVATION = "observation"
    """Status check or inspection without modification.

    Examples: Quality inspection, compliance verification, status check.
    In UNTP: Projects to ObjectEvent with action=OBSERVE.
    """

    AGGREGATION = "aggregation"
    """Pack or unpack operations.

    Examples: Palletizing, containerizing, unpacking.
    In UNTP: Projects to AggregationEvent.
    """


def transformation(cls: T) -> T:
    """Mark a service protocol as a transformation operation.

    Use for services that consume inputs and produce outputs.
    Manufacturing, processing, assembly operations.

    Example:
        @transformation
        class AssemblyService(Protocol):
            def assemble(self, parts: list[Part]) -> Product: ...
    """
    cls.__supply_chain_operation_type__ = SupplyChainOperationType.TRANSFORMATION
    return cls


def transaction(cls: T) -> T:
    """Mark a service protocol as a transaction operation.

    Use for services that transfer items between parties.
    Shipping, receiving, ownership transfer operations.

    Example:
        @transaction
        class ShippingService(Protocol):
            def ship(self, items: list[Item], destination: Location) -> Shipment: ...
    """
    cls.__supply_chain_operation_type__ = SupplyChainOperationType.TRANSACTION
    return cls


def observation(cls: T) -> T:
    """Mark a service protocol as an observation operation.

    Use for services that check status without modifying items.
    Inspection, verification, audit operations.

    Example:
        @observation
        class QualityInspectionService(Protocol):
            def inspect(self, item: Item) -> InspectionResult: ...
    """
    cls.__supply_chain_operation_type__ = SupplyChainOperationType.OBSERVATION
    return cls


def aggregation(cls: T) -> T:
    """Mark a service protocol as an aggregation operation.

    Use for services that pack or unpack items.
    Palletizing, containerizing, unpacking operations.

    Example:
        @aggregation
        class PalletizingService(Protocol):
            def palletize(self, items: list[Item]) -> Pallet: ...
    """
    cls.__supply_chain_operation_type__ = SupplyChainOperationType.AGGREGATION
    return cls


def get_supply_chain_operation_type(cls: type) -> SupplyChainOperationType | None:
    """Get the supply chain operation type for a service, if decorated.

    Args:
        cls: The service class (protocol or implementation) to check.

    Returns:
        The SupplyChainOperationType if the class is decorated, None otherwise.

    Example:
        @transformation
        class ProcessingService(Protocol): ...

        op_type = get_supply_chain_operation_type(ProcessingService)
        # op_type == SupplyChainOperationType.TRANSFORMATION
    """
    return getattr(cls, "__supply_chain_operation_type__", None)
