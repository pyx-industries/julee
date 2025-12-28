"""Acknowledgement entity for handler responses.

Standard return type for handlers. Indicates handoff status using radio
communication semantics.

Roger vs Wilco:
- "Roger" = I received and understood your message
- "Wilco" = Will comply (I'll do it)

If errors is empty, the acknowledgement is implicitly "wilco" - the handler
will do what was asked. If errors is not empty, the will_comply property
disambiguates whether the handler will still attempt to comply despite errors
(wilco with issues) or is just acknowledging receipt without compliance (roger).
"""

from pydantic import BaseModel, Field, model_validator


class Acknowledgement(BaseModel):
    """Response from a handler indicating handoff status.

    Handlers return Acknowledgement to indicate whether they will comply with
    the handoff request. The use case may inspect this for errors or notes,
    but doesn't know or care how the entity was handled.

    Message properties mirror logging semantics: errors, warnings, info, debug.
    """

    will_comply: bool = True
    """Whether the handler will comply with the request.

    If True with no errors: wilco (will do it)
    If True with errors: wilco with issues (will do it, but problems encountered)
    If False with errors: roger (received but won't comply, here's why)
    """

    errors: list[str] = Field(default_factory=list)
    """Error messages indicating problems."""

    warnings: list[str] = Field(default_factory=list)
    """Warning messages about potential issues."""

    info: list[str] = Field(default_factory=list)
    """Informational messages about the handoff."""

    debug: list[str] = Field(default_factory=list)
    """Debug messages for troubleshooting."""

    @model_validator(mode="after")
    def non_compliance_requires_error(self) -> "Acknowledgement":
        """Ensure non-compliance has at least one error message."""
        if not self.will_comply and not self.errors:
            raise ValueError("Non-compliance must have at least one error")
        return self

    @classmethod
    def wilco(
        cls,
        *,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        info: list[str] | None = None,
        debug: list[str] | None = None,
    ) -> "Acknowledgement":
        """Create a 'will comply' acknowledgement."""
        return cls(
            will_comply=True,
            errors=errors or [],
            warnings=warnings or [],
            info=info or [],
            debug=debug or [],
        )

    @classmethod
    def roger(
        cls,
        reason: str,
        *,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        info: list[str] | None = None,
        debug: list[str] | None = None,
    ) -> "Acknowledgement":
        """Create a 'received but won't comply' acknowledgement with reason."""
        all_errors = [reason] + (errors or [])
        return cls(
            will_comply=False,
            errors=all_errors,
            warnings=warnings or [],
            info=info or [],
            debug=debug or [],
        )
