"""PipelineRoute doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

A PipelineRoute is a declarative routing rule that maps a response type + condition
to a target pipeline + request type. Routes are introspectable and can be
used to generate PlantUML visualizations.

See: docs/architecture/proposals/pipeline_router_design.md
"""


from pydantic import BaseModel

# =============================================================================
# DOCTRINE: Operator
# =============================================================================


class TestOperatorDoctrine:
    """Doctrine about comparison operators for field conditions."""

    def test_operator_MUST_support_equality(self):
        """Operator MUST support equality comparison (eq)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.EQ == "eq"

    def test_operator_MUST_support_inequality(self):
        """Operator MUST support inequality comparison (ne)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.NE == "ne"

    def test_operator_MUST_support_is_true(self):
        """Operator MUST support boolean true check (is_true)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.IS_TRUE == "is_true"

    def test_operator_MUST_support_is_false(self):
        """Operator MUST support boolean false check (is_false)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.IS_FALSE == "is_false"

    def test_operator_MUST_support_is_none(self):
        """Operator MUST support None check (is_none)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.IS_NONE == "is_none"

    def test_operator_MUST_support_is_not_none(self):
        """Operator MUST support not-None check (is_not_none)."""
        from julee.shared.domain.models.pipeline_route import Operator

        assert Operator.IS_NOT_NONE == "is_not_none"


# =============================================================================
# DOCTRINE: FieldCondition
# =============================================================================


class TestFieldConditionDoctrine:
    """Doctrine about field conditions."""

    def test_field_condition_MUST_have_field_name(self):
        """A FieldCondition MUST specify the field to evaluate."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        condition = FieldCondition(field="has_new_data", operator=Operator.IS_TRUE)
        assert condition.field == "has_new_data"

    def test_field_condition_MUST_have_operator(self):
        """A FieldCondition MUST specify the comparison operator."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        condition = FieldCondition(field="status", operator=Operator.EQ, value="active")
        assert condition.operator == Operator.EQ

    def test_field_condition_MUST_evaluate_against_response(self):
        """A FieldCondition MUST be able to evaluate against a response object."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        class MockResponse(BaseModel):
            has_new_data: bool = True

        condition = FieldCondition(field="has_new_data", operator=Operator.IS_TRUE)
        assert condition.evaluate(MockResponse()) is True
        assert condition.evaluate(MockResponse(has_new_data=False)) is False

    def test_field_condition_MUST_support_dot_notation(self):
        """A FieldCondition MUST support nested field access via dot notation."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        class NestedData(BaseModel):
            status: str = "active"

        class MockResponse(BaseModel):
            result: NestedData = NestedData()

        condition = FieldCondition(
            field="result.status", operator=Operator.EQ, value="active"
        )
        assert condition.evaluate(MockResponse()) is True

    def test_field_condition_MUST_have_string_representation(self):
        """A FieldCondition MUST have a human-readable string representation for visualization."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        condition = FieldCondition(field="has_new_data", operator=Operator.IS_TRUE)
        assert "has_new_data" in str(condition)

    def test_field_condition_eq_MUST_compare_value(self):
        """FieldCondition with EQ operator MUST compare field to value."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        class MockResponse(BaseModel):
            status: str = "active"

        condition = FieldCondition(field="status", operator=Operator.EQ, value="active")
        assert condition.evaluate(MockResponse()) is True
        assert condition.evaluate(MockResponse(status="inactive")) is False

    def test_field_condition_is_not_none_MUST_check_not_none(self):
        """FieldCondition with IS_NOT_NONE operator MUST check field is not None."""
        from julee.shared.domain.models.pipeline_route import FieldCondition, Operator

        class MockResponse(BaseModel):
            error: str | None = None

        condition = FieldCondition(field="error", operator=Operator.IS_NOT_NONE)
        assert condition.evaluate(MockResponse()) is False
        assert condition.evaluate(MockResponse(error="something went wrong")) is True


# =============================================================================
# DOCTRINE: Condition
# =============================================================================


class TestConditionDoctrine:
    """Doctrine about compound conditions."""

    def test_condition_MUST_support_and_logic(self):
        """A PipelineCondition MUST support AND logic via all_of list."""
        from julee.shared.domain.models.pipeline_route import (
            FieldCondition,
            Operator,
            PipelineCondition,
        )

        class MockResponse(BaseModel):
            has_new_data: bool = True
            is_valid: bool = True

        condition = PipelineCondition(
            all_of=[
                FieldCondition(field="has_new_data", operator=Operator.IS_TRUE),
                FieldCondition(field="is_valid", operator=Operator.IS_TRUE),
            ]
        )

        # Both true -> True
        assert condition.evaluate(MockResponse()) is True
        # One false -> False
        assert condition.evaluate(MockResponse(has_new_data=False)) is False
        assert condition.evaluate(MockResponse(is_valid=False)) is False

    def test_condition_MUST_have_factory_is_true(self):
        """PipelineCondition MUST have is_true() factory for simple boolean checks."""
        from julee.shared.domain.models.pipeline_route import PipelineCondition

        condition = PipelineCondition.is_true("has_new_data")
        assert len(condition.all_of) == 1
        assert condition.all_of[0].field == "has_new_data"

    def test_condition_MUST_have_factory_is_not_none(self):
        """PipelineCondition MUST have is_not_none() factory for null checks."""
        from julee.shared.domain.models.pipeline_route import PipelineCondition

        condition = PipelineCondition.is_not_none("error")
        assert len(condition.all_of) == 1
        assert condition.all_of[0].field == "error"

    def test_condition_MUST_have_string_representation(self):
        """A PipelineCondition MUST have a human-readable string representation."""
        from julee.shared.domain.models.pipeline_route import PipelineCondition

        condition = PipelineCondition.is_true("has_new_data")
        assert "has_new_data" in str(condition)


# =============================================================================
# DOCTRINE: PipelineRoute
# =============================================================================


class TestPipelineRouteDoctrine:
    """Doctrine about pipeline routing rules."""

    def test_route_MUST_have_response_type(self):
        """A PipelineRoute MUST specify which response type it handles."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="NextPipeline",
            request_type="NextRequest",
        )
        assert route.response_type == "MyResponse"

    def test_route_MUST_have_condition(self):
        """A PipelineRoute MUST have a condition to evaluate."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="NextPipeline",
            request_type="NextRequest",
        )
        assert route.condition is not None

    def test_route_MUST_have_target_pipeline(self):
        """A PipelineRoute MUST specify the target pipeline to dispatch to."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="DocumentProcessingPipeline",
            request_type="ProcessDocumentRequest",
        )
        assert route.pipeline == "DocumentProcessingPipeline"

    def test_route_MUST_have_request_type(self):
        """A PipelineRoute MUST specify the request type for the target pipeline."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="NextPipeline",
            request_type="ProcessDocumentRequest",
        )
        assert route.request_type == "ProcessDocumentRequest"

    def test_route_MUST_match_response_by_type_and_condition(self):
        """A PipelineRoute MUST match responses by type AND condition evaluation."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        class MyResponse(BaseModel):
            has_new_data: bool = True

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="NextPipeline",
            request_type="NextRequest",
        )

        # Matches: correct type and condition true
        assert route.matches(MyResponse()) is True

        # Does not match: condition false
        assert route.matches(MyResponse(has_new_data=False)) is False

    def test_route_MAY_have_description(self):
        """A PipelineRoute MAY have a human-readable description."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )

        route = PipelineRoute(
            response_type="MyResponse",
            condition=PipelineCondition.is_true("has_new_data"),
            pipeline="NextPipeline",
            request_type="NextRequest",
            description="When new data detected, process document",
        )
        assert route.description == "When new data detected, process document"


# =============================================================================
# DOCTRINE: PipelineRouter
# =============================================================================


class TestPipelineRouterDoctrine:
    """Doctrine about pipeline routing."""

    def test_router_MUST_return_all_matching_routes(self):
        """A PipelineRouter MUST return ALL routes that match a response (multiplex)."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.shared.domain.models.pipeline_router import PipelineRouter

        class MyResponse(BaseModel):
            has_new_data: bool = True
            needs_notification: bool = True

        router = PipelineRouter(
            name="Test Router",
            routes=[
                PipelineRoute(
                    response_type="MyResponse",
                    condition=PipelineCondition.is_true("has_new_data"),
                    pipeline="ProcessingPipeline",
                    request_type="ProcessRequest",
                ),
                PipelineRoute(
                    response_type="MyResponse",
                    condition=PipelineCondition.is_true("needs_notification"),
                    pipeline="NotificationPipeline",
                    request_type="NotifyRequest",
                ),
            ],
        )

        matched = router.route(MyResponse())
        assert len(matched) == 2  # Both routes match

    def test_router_MUST_return_empty_list_when_no_match(self):
        """A PipelineRouter MUST return empty list when no routes match."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.shared.domain.models.pipeline_router import PipelineRouter

        class MyResponse(BaseModel):
            has_new_data: bool = False

        router = PipelineRouter(
            name="Test Router",
            routes=[
                PipelineRoute(
                    response_type="MyResponse",
                    condition=PipelineCondition.is_true("has_new_data"),
                    pipeline="ProcessingPipeline",
                    request_type="ProcessRequest",
                ),
            ],
        )

        matched = router.route(MyResponse())
        assert matched == []

    def test_router_MUST_have_name(self):
        """A PipelineRouter MUST have a name for identification."""
        from julee.shared.domain.models.pipeline_router import PipelineRouter

        router = PipelineRouter(name="Polling Router", routes=[])
        assert router.name == "Polling Router"

    def test_router_MUST_support_plantuml_generation(self):
        """A PipelineRouter MUST support PlantUML diagram generation."""
        from julee.shared.domain.models.pipeline_route import (
            PipelineCondition,
            PipelineRoute,
        )
        from julee.shared.domain.models.pipeline_router import PipelineRouter

        router = PipelineRouter(
            name="Test Router",
            routes=[
                PipelineRoute(
                    response_type="MyResponse",
                    condition=PipelineCondition.is_true("has_new_data"),
                    pipeline="ProcessingPipeline",
                    request_type="ProcessRequest",
                ),
            ],
        )

        plantuml = router.to_plantuml()
        assert "@startuml" in plantuml
        assert "@enduml" in plantuml
        assert "has_new_data" in plantuml
