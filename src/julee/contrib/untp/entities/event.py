"""UNTP traceability event definitions.

Supply chain event types based on GS1 EPCIS 2.0, used within Digital
Traceability Event (DTE) credentials:

- **TransformationEvent**: Manufacturing, processing, assembly
- **TransactionEvent**: Business transactions (purchase, sale, shipment)
- **ObjectEvent**: Observations, inspections, status changes
- **AggregationEvent**: Packaging, palletizing, container operations

These events are projected from OperationRecords based on the supply chain
operation type of the service that was invoked:

- @transformation service → TransformationEvent
- @transaction service → TransactionEvent
- @observation service → ObjectEvent
- @aggregation service → AggregationEvent

.. seealso::

   `GS1 EPCIS 2.0 <https://ref.gs1.org/standards/epcis/>`_
       Electronic Product Code Information Services standard defining
       the five event types and their semantics.

   `UNTP DTE Specification <https://uncefact.github.io/spec-untp/docs/specification/DigitalTraceabilityEvents/>`_
       How UNTP wraps EPCIS events in verifiable credentials.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from julee.contrib.untp.entities.core import Identifier, Organization, SecureLink


class EventAction(str, Enum):
    """Action type for object and aggregation events.

    .. seealso::

       `EPCIS Action <https://ref.gs1.org/cbv/Action>`_
           GS1 Core Business Vocabulary action values.
    """

    ADD = "ADD"
    OBSERVE = "OBSERVE"
    DELETE = "DELETE"


class EventDisposition(str, Enum):
    """Business disposition of objects after event.

    .. seealso::

       `EPCIS Disposition <https://ref.gs1.org/cbv/Disp>`_
           GS1 CBV disposition vocabulary.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    IN_TRANSIT = "in_transit"
    SOLD = "sold"
    DESTROYED = "destroyed"
    RETURNED = "returned"
    RECALLED = "recalled"


class QuantityElement(BaseModel):
    """Quantity of a product class.

    Used when tracking quantities by product class rather than individual
    serialized items.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    product_class: Identifier = Field(
        ...,
        alias="productClass",
        description="Product class identifier",
    )
    quantity: float = Field(
        ...,
        description="Quantity amount",
    )
    unit: str = Field(
        ...,
        description="Unit of measure",
    )


class BaseEvent(BaseModel):
    """Base class for all traceability events.

    Provides common EPCIS event dimensions: when (eventTime), where
    (readPoint, bizLocation), and who (actor).
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    event_id: str = Field(
        ...,
        alias="eventId",
        description="Unique event identifier",
    )
    event_time: datetime = Field(
        ...,
        alias="eventTime",
        description="When the event occurred",
    )
    event_timezone: str = Field(
        default="UTC",
        alias="eventTimezone",
        description="Timezone of the event",
    )
    record_time: datetime | None = Field(
        default=None,
        alias="recordTime",
        description="When the event was recorded",
    )
    location: Identifier | None = Field(
        default=None,
        alias="readPoint",
        description="Location where event occurred",
    )
    business_location: Identifier | None = Field(
        default=None,
        alias="bizLocation",
        description="Business location context",
    )
    actor: Organization | None = Field(
        default=None,
        description="Organization performing the event",
    )

    # Link back to the operation that generated this event
    operation_id: str | None = Field(
        default=None,
        alias="operationId",
        description="ID of the OperationRecord this event was projected from",
    )


class TransformationEvent(BaseEvent):
    """Records transformation of inputs into outputs.

    Used for manufacturing, processing, and assembly operations where input
    materials are consumed to produce different output products.

    Projected from services decorated with @transformation.
    """

    input_items: list[Identifier] = Field(
        default_factory=list,
        alias="inputItems",
        description="Specific input item identifiers",
    )
    input_quantities: list[QuantityElement] = Field(
        default_factory=list,
        alias="inputQuantities",
        description="Input quantities by product class",
    )
    output_items: list[Identifier] = Field(
        default_factory=list,
        alias="outputItems",
        description="Specific output item identifiers",
    )
    output_quantities: list[QuantityElement] = Field(
        default_factory=list,
        alias="outputQuantities",
        description="Output quantities by product class",
    )
    transformation_type: str | None = Field(
        default=None,
        alias="transformationType",
        description="Type of transformation (e.g., 'manufacturing', 'processing')",
    )
    conformity_evidence: list[SecureLink] = Field(
        default_factory=list,
        alias="conformityEvidence",
        description="Links to conformity credentials for this transformation",
    )

    @classmethod
    def from_operation(
        cls,
        operation_id: str,
        event_time: datetime,
        transformation_type: str | None = None,
        **kwargs,
    ) -> "TransformationEvent":
        """Create a TransformationEvent from an operation record.

        Args:
            operation_id: ID of the OperationRecord
            event_time: When the transformation occurred
            transformation_type: Type of transformation
            **kwargs: Additional event fields

        Returns:
            A new TransformationEvent
        """
        return cls(
            event_id=f"evt-{operation_id}",
            event_time=event_time,
            operation_id=operation_id,
            transformation_type=transformation_type,
            **kwargs,
        )


class TransactionType(str, Enum):
    """Type of business transaction.

    .. seealso::

       `EPCIS Business Transaction <https://ref.gs1.org/cbv/BTT>`_
           GS1 CBV business transaction type vocabulary.
    """

    PURCHASE_ORDER = "purchase_order"
    DESPATCH_ADVICE = "despatch_advice"
    RECEIVING_ADVICE = "receiving_advice"
    INVOICE = "invoice"
    RETURN = "return"


class TransactionEvent(BaseEvent):
    """Records business transaction between parties.

    Links physical events to business transactions: purchases, sales,
    shipments, and receipts.

    Projected from services decorated with @transaction.
    """

    action: EventAction = Field(
        default=EventAction.ADD,
        description="Transaction action",
    )
    transaction_type: TransactionType = Field(
        ...,
        alias="bizTransactionType",
        description="Type of transaction",
    )
    transaction_id: str = Field(
        ...,
        alias="bizTransactionId",
        description="Business transaction identifier",
    )
    source_party: Organization = Field(
        ...,
        alias="sourceParty",
        description="Party sending/selling",
    )
    destination_party: Organization = Field(
        ...,
        alias="destinationParty",
        description="Party receiving/buying",
    )
    items: list[Identifier] = Field(
        default_factory=list,
        description="Specific item identifiers in transaction",
    )
    quantities: list[QuantityElement] = Field(
        default_factory=list,
        description="Quantities by product class",
    )

    @classmethod
    def from_operation(
        cls,
        operation_id: str,
        event_time: datetime,
        transaction_type: TransactionType,
        transaction_id: str,
        source_party: Organization,
        destination_party: Organization,
        **kwargs,
    ) -> "TransactionEvent":
        """Create a TransactionEvent from an operation record.

        Args:
            operation_id: ID of the OperationRecord
            event_time: When the transaction occurred
            transaction_type: Type of business transaction
            transaction_id: Business transaction identifier
            source_party: Sending party
            destination_party: Receiving party
            **kwargs: Additional event fields

        Returns:
            A new TransactionEvent
        """
        return cls(
            event_id=f"evt-{operation_id}",
            event_time=event_time,
            operation_id=operation_id,
            transaction_type=transaction_type,
            transaction_id=transaction_id,
            source_party=source_party,
            destination_party=destination_party,
            **kwargs,
        )


class ObjectEvent(BaseEvent):
    """Records observation or state change of objects.

    The most general event type: something happened to objects at a place
    and time. Used for inspections, status updates, commissioning, and
    decommissioning.

    Projected from services decorated with @observation.
    """

    action: EventAction = Field(
        ...,
        description="Type of action (ADD/OBSERVE/DELETE)",
    )
    items: list[Identifier] = Field(
        default_factory=list,
        description="Specific item identifiers",
    )
    quantities: list[QuantityElement] = Field(
        default_factory=list,
        description="Quantities by product class",
    )
    disposition: EventDisposition | None = Field(
        default=None,
        alias="bizStep",
        description="Business state after event",
    )
    sensor_data: list[dict] = Field(
        default_factory=list,
        alias="sensorData",
        description="Associated sensor readings",
    )
    conformity_evidence: list[SecureLink] = Field(
        default_factory=list,
        alias="conformityEvidence",
        description="Links to conformity credentials",
    )

    @classmethod
    def from_operation(
        cls,
        operation_id: str,
        event_time: datetime,
        action: EventAction = EventAction.OBSERVE,
        disposition: EventDisposition | None = None,
        **kwargs,
    ) -> "ObjectEvent":
        """Create an ObjectEvent from an operation record.

        Args:
            operation_id: ID of the OperationRecord
            event_time: When the observation occurred
            action: Type of action (default OBSERVE)
            disposition: Business state after event
            **kwargs: Additional event fields

        Returns:
            A new ObjectEvent
        """
        return cls(
            event_id=f"evt-{operation_id}",
            event_time=event_time,
            operation_id=operation_id,
            action=action,
            disposition=disposition,
            **kwargs,
        )


class AggregationEvent(BaseEvent):
    """Records aggregation or disaggregation of items.

    Used for packaging, palletizing, and container operations. ADD action
    packs children into parent; DELETE action unpacks.

    Projected from services decorated with @aggregation.
    """

    action: EventAction = Field(
        ...,
        description="ADD (pack) or DELETE (unpack)",
    )
    parent_id: Identifier = Field(
        ...,
        alias="parentId",
        description="Container/pallet/case identifier",
    )
    child_items: list[Identifier] = Field(
        default_factory=list,
        alias="childItems",
        description="Items being aggregated/disaggregated",
    )
    child_quantities: list[QuantityElement] = Field(
        default_factory=list,
        alias="childQuantities",
        description="Quantities by product class",
    )

    @classmethod
    def from_operation(
        cls,
        operation_id: str,
        event_time: datetime,
        action: EventAction,
        parent_id: Identifier,
        **kwargs,
    ) -> "AggregationEvent":
        """Create an AggregationEvent from an operation record.

        Args:
            operation_id: ID of the OperationRecord
            event_time: When the aggregation occurred
            action: ADD (pack) or DELETE (unpack)
            parent_id: Container identifier
            **kwargs: Additional event fields

        Returns:
            A new AggregationEvent
        """
        return cls(
            event_id=f"evt-{operation_id}",
            event_time=event_time,
            operation_id=operation_id,
            action=action,
            parent_id=parent_id,
            **kwargs,
        )
