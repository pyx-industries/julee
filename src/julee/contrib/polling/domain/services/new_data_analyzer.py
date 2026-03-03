"""
NewDataAnalyzer protocol for converting raw polling bytes into item IDs.

This protocol is the counterpart to PollingResultHandler. Where the handler
decides what to *do* when new items are found, the analyzer decides *what*
items are new by comparing previous and current polling payloads.

Separating analysis from handling keeps each concern to a single class and
allows the NewDataDetectionPipeline to complete data→domain translation
before any application-level dispatch occurs.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class NewDataAnalyzer(Protocol):
    """
    Converts raw polling bytes into a list of new item identifiers.

    The analyzer is responsible for:
    - Parsing the raw bytes from the polling response
    - Comparing with the previous response (if any)
    - Returning the IDs of items that are new or changed

    The returned IDs are opaque strings from the polling system's perspective.
    Their meaning is defined by the bounded context that provides the analyzer.
    """

    async def identify_new_items(
        self,
        previous_data: bytes | None,
        new_data: bytes,
    ) -> list[str]:
        """
        Identify items that are new or changed since the previous poll.

        Args:
            previous_data: Previous polling response content.
                           None if this is the first polling run.
            new_data: Current polling response content.

        Returns:
            List of item identifier strings that are new or changed.
            Empty list if nothing is new.

        Raises:
            ValueError: If the data cannot be parsed or is in an unexpected format.
        """
        ...
