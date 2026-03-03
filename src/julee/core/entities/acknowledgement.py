"""
Acknowledgement entity for handler service responses.

This module implements the Acknowledgement entity as specified in ADR 003,
providing radio communication semantics (wilco/unable/roger) for handler
service responses.
"""

from pydantic import BaseModel, Field


class Acknowledgement(BaseModel):
    """
    Acknowledgement response from handler services using radio communication semantics.

    Following radio communication conventions:
    - **Wilco** ("will comply"): Handler accepts and will process
    - **Unable**: Handler cannot comply (resource constraints, invalid state, etc.)
    - **Roger** ("received"): Handler acknowledges receipt but makes no commitment
      about whether it will act - the wilco/unable distinction is not provided
    """

    will_comply: bool | None = Field(
        default=None,
        description="None = roger (no commitment), True = wilco (will process), False = unable (cannot process)",
    )
    info: list[str] = Field(
        default_factory=list,
        description="Informational messages about handler processing",
    )

    @classmethod
    def wilco(
        cls,
        info: list[str] | None = None,
    ) -> "Acknowledgement":
        """
        Will comply - handler accepts and will process.

        Args:
            info: Optional informational messages

        Returns:
            Acknowledgement with will_comply=True
        """
        return cls(
            will_comply=True,
            info=info or [],
        )

    @classmethod
    def unable(
        cls,
        info: list[str] | None = None,
    ) -> "Acknowledgement":
        """
        Unable to comply - handler cannot process.

        Args:
            info: Optional informational messages explaining why handler cannot comply

        Returns:
            Acknowledgement with will_comply=False
        """
        return cls(
            will_comply=False,
            info=info or [],
        )

    @classmethod
    def roger(
        cls,
        info: list[str] | None = None,
    ) -> "Acknowledgement":
        """
        Received - acknowledged, no commitment about action.

        Handler acknowledges receipt but makes no commitment about whether
        it will act. This is appropriate when the handler logs or records
        the request but doesn't guarantee processing.

        Args:
            info: Optional informational messages

        Returns:
            Acknowledgement with will_comply=None
        """
        return cls(
            will_comply=None,
            info=info or [],
        )

    @property
    def is_wilco(self) -> bool:
        """True if handler will comply (will_comply=True)."""
        return self.will_comply is True

    @property
    def is_unable(self) -> bool:
        """True if handler is unable to comply (will_comply=False)."""
        return self.will_comply is False

    @property
    def is_roger(self) -> bool:
        """True if handler acknowledged with no commitment (will_comply=None)."""
        return self.will_comply is None

    @property
    def has_info(self) -> bool:
        """True if acknowledgement contains any informational messages."""
        return len(self.info) > 0

    def __str__(self) -> str:
        """String representation showing acknowledgement type and message counts."""
        ack_type = "WILCO" if self.is_wilco else "UNABLE" if self.is_unable else "ROGER"

        if self.info:
            return f"{ack_type} ({len(self.info)} info)"
        return ack_type

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"Acknowledgement(will_comply={self.will_comply}, info={len(self.info)})"
