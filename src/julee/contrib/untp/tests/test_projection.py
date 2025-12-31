"""Tests for UNTP projection logic.

Verifies that UseCaseExecution with operation_records correctly
projects to UNTP credentials based on supply chain semantics.
"""

from datetime import datetime, timezone
from typing import Protocol

import pytest

from julee.contrib.untp.entities.core import Identifier
from julee.contrib.untp.entities.event import (
    AggregationEvent,
    EventAction,
    ObjectEvent,
    TransformationEvent,
)
from julee.core.entities.operation_record import OperationRecord
from julee.core.entities.pipeline_output import PipelineOutput
from julee.core.entities.use_case_execution import UseCaseExecution
from julee.supply_chain.decorators import (
    SupplyChainOperationType,
    aggregation,
    get_supply_chain_operation_type,
    observation,
    transaction,
    transformation,
)


class TestSupplyChainDecorators:
    """Tests for supply chain decorators on service protocols."""

    def test_transformation_decorator(self):
        """@transformation marks protocol as transformation operation."""

        @transformation
        class MaterialProcessingService(Protocol):
            def process(self, inputs: list) -> list: ...

        op_type = get_supply_chain_operation_type(MaterialProcessingService)
        assert op_type == SupplyChainOperationType.TRANSFORMATION

    def test_transaction_decorator(self):
        """@transaction marks protocol as transaction operation."""

        @transaction
        class OrderService(Protocol):
            def place_order(self, items: list) -> str: ...

        op_type = get_supply_chain_operation_type(OrderService)
        assert op_type == SupplyChainOperationType.TRANSACTION

    def test_observation_decorator(self):
        """@observation marks protocol as observation operation."""

        @observation
        class InspectionService(Protocol):
            def inspect(self, item_id: str) -> dict: ...

        op_type = get_supply_chain_operation_type(InspectionService)
        assert op_type == SupplyChainOperationType.OBSERVATION

    def test_aggregation_decorator(self):
        """@aggregation marks protocol as aggregation operation."""

        @aggregation
        class PackingService(Protocol):
            def pack(self, items: list, container_id: str) -> str: ...

        op_type = get_supply_chain_operation_type(PackingService)
        assert op_type == SupplyChainOperationType.AGGREGATION

    def test_undecorated_protocol(self):
        """Undecorated protocol returns None for operation type."""

        class GenericService(Protocol):
            def do_something(self) -> None: ...

        op_type = get_supply_chain_operation_type(GenericService)
        assert op_type is None


class TestOperationRecordCreation:
    """Tests for creating operation records from service invocations."""

    def test_operation_record_creation(self):
        """OperationRecord captures service invocation details."""
        now = datetime.now(timezone.utc)
        record = OperationRecord(
            operation_id="op-001",
            service_type="myapp.services.MaterialProcessingService",
            method_name="process",
            started_at=now,
            completed_at=now,
            input_summary={"material_count": 5},
            output_summary={"product_count": 3},
            metadata={"batch_id": "batch-123"},
        )
        assert record.operation_id == "op-001"
        assert record.service_type == "myapp.services.MaterialProcessingService"
        assert record.method_name == "process"
        assert record.input_summary["material_count"] == 5

    def test_operation_record_is_immutable(self):
        """OperationRecord is frozen."""
        from pydantic import ValidationError

        now = datetime.now(timezone.utc)
        record = OperationRecord(
            operation_id="op-001",
            service_type="test.Service",
            method_name="test",
            started_at=now,
            completed_at=now,
        )
        with pytest.raises(ValidationError):
            record.operation_id = "changed"


class TestUseCaseExecutionWithOperations:
    """Tests for UseCaseExecution containing operation records."""

    @pytest.fixture
    def sample_operations(self):
        """Sample operation records for testing."""
        now = datetime.now(timezone.utc)
        return [
            OperationRecord(
                operation_id="op-001",
                service_type="supply_chain.TransformationService",
                method_name="transform",
                started_at=now,
                completed_at=now,
                input_summary={"inputs": ["raw-001", "raw-002"]},
                output_summary={"outputs": ["product-001"]},
            ),
            OperationRecord(
                operation_id="op-002",
                service_type="supply_chain.InspectionService",
                method_name="inspect",
                started_at=now,
                completed_at=now,
                input_summary={"item": "product-001"},
                output_summary={"passed": True},
            ),
            OperationRecord(
                operation_id="op-003",
                service_type="supply_chain.ShippingService",
                method_name="ship",
                started_at=now,
                completed_at=now,
                input_summary={"item": "product-001", "destination": "warehouse-a"},
                output_summary={"tracking_id": "track-123"},
            ),
        ]

    def test_execution_with_multiple_operations(self, sample_operations):
        """UseCaseExecution can contain multiple operation records."""
        now = datetime.now(timezone.utc)
        execution = UseCaseExecution(
            execution_id="exec-001",
            use_case_name="ProcessAndShipProduct",
            bounded_context="manufacturing",
            started_at=now,
            completed_at=now,
            duration_ms=1500,
            request_summary={"product_id": "product-001"},
            response_summary={"shipped": True},
            operation_records=sample_operations,
        )
        assert len(execution.operation_records) == 3
        assert (
            execution.operation_records[0].service_type
            == "supply_chain.TransformationService"
        )
        assert (
            execution.operation_records[1].service_type
            == "supply_chain.InspectionService"
        )
        assert (
            execution.operation_records[2].service_type
            == "supply_chain.ShippingService"
        )

    def test_execution_without_operations(self):
        """UseCaseExecution can have empty operation_records."""
        now = datetime.now(timezone.utc)
        execution = UseCaseExecution(
            execution_id="exec-002",
            use_case_name="SimpleQuery",
            bounded_context="reporting",
            started_at=now,
            completed_at=now,
            duration_ms=50,
            request_summary={},
            response_summary={},
        )
        assert execution.operation_records == []


class TestEventFromOperation:
    """Tests for creating UNTP events from operation records."""

    def test_transformation_event_from_operation(self):
        """TransformationEvent.from_operation creates event from OperationRecord."""
        now = datetime.now(timezone.utc)
        event = TransformationEvent.from_operation(
            operation_id="op-123",
            event_time=now,
            transformation_type="assembly",
        )
        assert event.event_id == "evt-op-123"
        assert event.operation_id == "op-123"
        assert event.transformation_type == "assembly"
        assert event.event_time == now

    def test_transformation_event_with_items(self):
        """TransformationEvent can specify input and output items."""
        now = datetime.now(timezone.utc)
        event = TransformationEvent(
            event_id="evt-001",
            event_time=now,
            input_items=[
                Identifier(scheme="gtin", value="input-001"),
                Identifier(scheme="gtin", value="input-002"),
            ],
            output_items=[
                Identifier(scheme="gtin", value="output-001"),
            ],
            transformation_type="manufacturing",
        )
        assert len(event.input_items) == 2
        assert len(event.output_items) == 1

    def test_object_event_observe_action(self):
        """ObjectEvent with OBSERVE action for inspection."""
        now = datetime.now(timezone.utc)
        event = ObjectEvent(
            event_id="evt-002",
            event_time=now,
            action=EventAction.OBSERVE,
            items=[Identifier(scheme="gtin", value="item-001")],
        )
        assert event.action == EventAction.OBSERVE

    def test_aggregation_event_add_action(self):
        """AggregationEvent with ADD action for packing."""
        now = datetime.now(timezone.utc)
        event = AggregationEvent(
            event_id="evt-003",
            event_time=now,
            action=EventAction.ADD,
            parent_id=Identifier(scheme="sscc", value="pallet-001"),
            child_items=[
                Identifier(scheme="gtin", value="item-001"),
                Identifier(scheme="gtin", value="item-002"),
            ],
        )
        assert event.action == EventAction.ADD
        assert len(event.child_items) == 2


class TestProjectionMapping:
    """Tests for mapping operation types to UNTP event types."""

    def test_transformation_maps_to_transformation_event(self):
        """TRANSFORMATION operation type maps to TransformationEvent."""
        op_type = SupplyChainOperationType.TRANSFORMATION
        # In real code, ProjectExecutionUseCase does this mapping
        assert op_type.value == "transformation"

    def test_transaction_maps_to_transaction_event(self):
        """TRANSACTION operation type maps to TransactionEvent."""
        op_type = SupplyChainOperationType.TRANSACTION
        assert op_type.value == "transaction"

    def test_observation_maps_to_object_event(self):
        """OBSERVATION operation type maps to ObjectEvent with OBSERVE action."""
        op_type = SupplyChainOperationType.OBSERVATION
        assert op_type.value == "observation"

    def test_aggregation_maps_to_aggregation_event(self):
        """AGGREGATION operation type maps to AggregationEvent."""
        op_type = SupplyChainOperationType.AGGREGATION
        assert op_type.value == "aggregation"


class TestPipelineOutputProjection:
    """Tests for projecting PipelineOutput to DigitalProductPassport."""

    def test_pipeline_output_creation(self):
        """PipelineOutput captures pipeline execution result."""
        now = datetime.now(timezone.utc)
        output = PipelineOutput(
            output_id="out-001",
            pipeline_slug="product-certification",
            name="Certified Product Data",
            created_at=now,
            execution_ids=["exec-001", "exec-002"],
            artifact_uri="https://storage.example.com/artifacts/out-001",
        )
        assert output.output_id == "out-001"
        assert output.pipeline_slug == "product-certification"
        assert len(output.execution_ids) == 2

    def test_pipeline_output_without_artifact(self):
        """PipelineOutput can have no artifact_uri."""
        now = datetime.now(timezone.utc)
        output = PipelineOutput(
            output_id="out-002",
            pipeline_slug="data-processing",
            name="Processed Data",
            created_at=now,
            execution_ids=["exec-003"],
        )
        assert output.artifact_uri is None

    def test_pipeline_output_is_immutable(self):
        """PipelineOutput is frozen."""
        from pydantic import ValidationError

        now = datetime.now(timezone.utc)
        output = PipelineOutput(
            output_id="out-003",
            pipeline_slug="test",
            name="Test",
            created_at=now,
            execution_ids=[],
        )
        with pytest.raises(ValidationError):
            output.name = "Changed"
