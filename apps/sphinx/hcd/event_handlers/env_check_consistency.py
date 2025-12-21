"""Env-check-consistency event handler for sphinx_hcd.

Validates accelerators against code structure after all documents are read.
"""

import asyncio
import logging

from julee.hcd.domain.use_cases.requests import ValidateAcceleratorsRequest
from julee.hcd.domain.use_cases.queries import ValidateAcceleratorsUseCase
from ..context import get_hcd_context

logger = logging.getLogger(__name__)


def on_env_check_consistency(app, env):
    """Validate accelerators after all documents are read.

    This handler runs after ALL documents have been read and before
    the write phase begins. It validates that documented accelerators
    match discovered bounded contexts.

    Args:
        app: Sphinx application instance
        env: Sphinx build environment
    """
    try:
        context = get_hcd_context(app)
    except AttributeError:
        logger.debug("HCDContext not initialized - skipping accelerator validation")
        return

    # Get the underlying async repositories from the sync adapters
    accelerator_repo = context.accelerator_repo.async_repo
    code_info_repo = context.code_info_repo.async_repo

    # Create and run the validation use case
    use_case = ValidateAcceleratorsUseCase(
        accelerator_repo=accelerator_repo,
        code_info_repo=code_info_repo,
    )

    request = ValidateAcceleratorsRequest()
    response = asyncio.run(use_case.execute(request))

    # Log results
    if response.is_valid:
        logger.info(
            f"Accelerator validation passed: {len(response.matched_slugs)} "
            "accelerators match code"
        )
    else:
        # Emit warnings for each issue
        for issue in response.issues:
            if issue.issue_type == "undocumented":
                logger.warning(issue.message)
            elif issue.issue_type == "no_code":
                logger.warning(issue.message)
            else:
                logger.info(issue.message)

        logger.warning(
            f"Accelerator validation: {len(response.issues)} issues found. "
            f"Documented: {len(response.documented_slugs)}, "
            f"Discovered: {len(response.discovered_slugs)}, "
            f"Matched: {len(response.matched_slugs)}"
        )
