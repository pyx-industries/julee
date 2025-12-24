"""PipelineRoute models for declarative pipeline routing.

A PipelineRoute is a declarative routing rule that maps a response type + condition
to a target pipeline + request type. Routes are introspectable and can be
used to generate PlantUML visualizations.

See: docs/architecture/proposals/pipeline_router_design.md
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class Operator(str, Enum):
    """Comparison operators for field conditions."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IS_NONE = "is_none"
    IS_NOT_NONE = "is_not_none"
    IN = "in"
    NOT_IN = "not_in"


class FieldCondition(BaseModel):
    """A single condition on a response field.

    Supports dot notation for nested field access (e.g., "result.status").
    """

    field: str
    operator: Operator
    value: Any = None

    def evaluate(self, response: BaseModel | dict) -> bool:
        """Evaluate this condition against a response object."""
        field_value = self._get_field_value(response, self.field)

        match self.operator:
            case Operator.EQ:
                return field_value == self.value
            case Operator.NE:
                return field_value != self.value
            case Operator.GT:
                return field_value > self.value
            case Operator.GE:
                return field_value >= self.value
            case Operator.LT:
                return field_value < self.value
            case Operator.LE:
                return field_value <= self.value
            case Operator.IS_TRUE:
                return field_value is True
            case Operator.IS_FALSE:
                return field_value is False
            case Operator.IS_NONE:
                return field_value is None
            case Operator.IS_NOT_NONE:
                return field_value is not None
            case Operator.IN:
                return field_value in self.value
            case Operator.NOT_IN:
                return field_value not in self.value

        return False

    def _get_field_value(self, obj: BaseModel | dict, field_path: str) -> Any:
        """Get nested field value using dot notation."""
        value = obj
        for part in field_path.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = getattr(value, part, None)
            if value is None:
                break
        return value

    def __str__(self) -> str:
        """Human-readable representation for visualization."""
        match self.operator:
            case Operator.IS_TRUE:
                return f"{self.field}"
            case Operator.IS_FALSE:
                return f"not {self.field}"
            case Operator.IS_NONE:
                return f"{self.field} is None"
            case Operator.IS_NOT_NONE:
                return f"{self.field} is not None"
            case Operator.IN:
                return f"{self.field} in {self.value}"
            case Operator.NOT_IN:
                return f"{self.field} not in {self.value}"
            case _:
                op_symbols = {
                    "eq": "==",
                    "ne": "!=",
                    "gt": ">",
                    "ge": ">=",
                    "lt": "<",
                    "le": "<=",
                }
                return f"{self.field} {op_symbols.get(self.operator.value, self.operator.value)} {self.value!r}"


class PipelineCondition(BaseModel):
    """A compound condition (AND of multiple field conditions)."""

    all_of: list[FieldCondition]

    def evaluate(self, response: BaseModel | dict) -> bool:
        """Evaluate all conditions (AND logic)."""
        return all(cond.evaluate(response) for cond in self.all_of)

    def __str__(self) -> str:
        """Human-readable representation."""
        if len(self.all_of) == 1:
            return str(self.all_of[0])
        return " AND ".join(f"({cond})" for cond in self.all_of)

    @classmethod
    def when(
        cls, field: str, operator: Operator, value: Any = None
    ) -> "PipelineCondition":
        """Factory for simple single-field conditions."""
        return cls(all_of=[FieldCondition(field=field, operator=operator, value=value)])

    @classmethod
    def is_true(cls, field: str) -> "PipelineCondition":
        """Factory: field is True."""
        return cls.when(field, Operator.IS_TRUE)

    @classmethod
    def is_false(cls, field: str) -> "PipelineCondition":
        """Factory: field is False."""
        return cls.when(field, Operator.IS_FALSE)

    @classmethod
    def is_none(cls, field: str) -> "PipelineCondition":
        """Factory: field is None."""
        return cls.when(field, Operator.IS_NONE)

    @classmethod
    def is_not_none(cls, field: str) -> "PipelineCondition":
        """Factory: field is not None."""
        return cls.when(field, Operator.IS_NOT_NONE)

    @classmethod
    def equals(cls, field: str, value: Any) -> "PipelineCondition":
        """Factory: field equals value."""
        return cls.when(field, Operator.EQ, value)


# Backwards-compatible alias
Condition = PipelineCondition


class PipelineRoute(BaseModel):
    """A pipeline routing rule: response type + condition -> pipeline + request type.

    A PipelineRoute is declarative and introspectable. It defines:
    - Which response type it handles
    - What condition must be true
    - Which pipeline to trigger
    - What request type the target pipeline expects
    """

    response_type: str
    condition: PipelineCondition
    pipeline: str
    request_type: str
    description: str = ""

    def matches(self, response: BaseModel | dict) -> bool:
        """Check if this route matches the given response.

        Matches if:
        1. Response type matches (by class name)
        2. Condition evaluates to True
        """
        # Check type match
        if isinstance(response, dict):
            # Can't check type for dict, assume it matches if condition passes
            pass
        else:
            response_class_name = response.__class__.__name__
            response_fqn = f"{response.__class__.__module__}.{response_class_name}"

            # Match by FQN or just class name
            if (
                response_fqn != self.response_type
                and response_class_name != self.response_type
                and response_class_name != self.response_type.split(".")[-1]
            ):
                return False

        # Check condition
        return self.condition.evaluate(response)


# Backwards-compatible alias
Route = PipelineRoute
