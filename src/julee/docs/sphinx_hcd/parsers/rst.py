"""RST directive parser.

Parses RST files containing define-epic, define-journey, and define-accelerator
directives to extract entity data. Uses regex-based parsing (not full RST).
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.models.accelerator import Accelerator, IntegrationReference
from ..domain.models.epic import Epic
from ..domain.models.journey import Journey, JourneyStep, StepType

logger = logging.getLogger(__name__)


# =============================================================================
# Parsed Data Classes
# =============================================================================


@dataclass
class ParsedEpic:
    """Raw parsed data from an epic RST directive."""

    slug: str
    description: str = ""
    story_refs: list[str] = field(default_factory=list)


@dataclass
class ParsedJourney:
    """Raw parsed data from a journey RST directive."""

    slug: str
    persona: str = ""
    intent: str = ""
    outcome: str = ""
    goal: str = ""
    depends_on: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    steps: list[JourneyStep] = field(default_factory=list)


@dataclass
class ParsedAccelerator:
    """Raw parsed data from an accelerator RST directive."""

    slug: str
    status: str = ""
    milestone: str = ""
    acceptance: str = ""
    objective: str = ""
    sources_from: list[str] = field(default_factory=list)
    publishes_to: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    feeds_into: list[str] = field(default_factory=list)


# =============================================================================
# Regex Patterns
# =============================================================================

# Directive patterns - match directive name and argument
DEFINE_EPIC_PATTERN = re.compile(r"^\.\.\s+define-epic::\s*(\S+)", re.MULTILINE)
DEFINE_JOURNEY_PATTERN = re.compile(r"^\.\.\s+define-journey::\s*(\S+)", re.MULTILINE)
DEFINE_ACCELERATOR_PATTERN = re.compile(
    r"^\.\.\s+define-accelerator::\s*(\S+)", re.MULTILINE
)

# Child directive patterns
EPIC_STORY_PATTERN = re.compile(r"^\.\.\s+epic-story::\s*(.+)$", re.MULTILINE)
STEP_PHASE_PATTERN = re.compile(r"^\.\.\s+step-phase::\s*(.+)$", re.MULTILINE)
STEP_STORY_PATTERN = re.compile(r"^\.\.\s+step-story::\s*(.+)$", re.MULTILINE)
STEP_EPIC_PATTERN = re.compile(r"^\.\.\s+step-epic::\s*(.+)$", re.MULTILINE)

# Option pattern - matches :key: value
OPTION_PATTERN = re.compile(r"^\s+:([a-z-]+):\s*(.*)$", re.MULTILINE)


# =============================================================================
# Parsing Helpers
# =============================================================================


def _extract_options(content: str) -> dict[str, str]:
    """Extract RST directive options from content.

    Options are lines like:
        :persona: New User
        :depends-on: journey-1, journey-2

    Args:
        content: RST content after the directive line

    Returns:
        Dict of option name to value
    """
    options = {}
    lines = content.split("\n")
    current_key = None
    current_value: list[str] = []
    found_any_option = False

    for line in lines:
        # Check for new option
        match = re.match(r"^\s{3}:([a-z-]+):\s*(.*)$", line)
        if match:
            # Save previous option if any
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            current_key = match.group(1)
            current_value = [match.group(2)] if match.group(2) else []
            found_any_option = True
        elif current_key and line.startswith("       ") and line.strip():
            # Continuation line for multi-line option (7 spaces)
            current_value.append(line.strip())
        elif line.strip() == "":
            # Empty line - only break if we've found options (end of options block)
            if found_any_option:
                if current_key:
                    options[current_key] = "\n".join(current_value).strip()
                break
            # Otherwise skip leading empty lines
        elif not line.startswith("   "):
            # Non-indented content - end of directive
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            break
        elif line.startswith("   ") and not line.startswith("   :"):
            # Content line (not option) - end options parsing
            if current_key:
                options[current_key] = "\n".join(current_value).strip()
            break

    # Handle final option
    if current_key and current_key not in options:
        options[current_key] = "\n".join(current_value).strip()

    return options


def _extract_content(content: str, after_options: bool = True) -> str:
    """Extract directive body content (indented text after options).

    Args:
        content: RST content after the directive line
        after_options: Whether to skip option lines first

    Returns:
        Extracted content text
    """
    lines = content.split("\n")
    content_lines: list[str] = []
    in_options = after_options
    found_option = False
    found_content = False

    for line in lines:
        # Skip option lines
        if in_options:
            if re.match(r"^\s{3}:[a-z-]+:", line):
                found_option = True
                continue
            elif line.startswith("       ") and found_option and not found_content:
                # Continuation of option (7 spaces)
                continue
            elif line.strip() == "":
                # Empty line - only exit options mode if we've seen options
                if found_option:
                    in_options = False
                continue
            elif line.startswith("   ") and not line.startswith("   :"):
                # Content line (not option) - exit options mode
                in_options = False
                found_content = True

        # Check for end of content (new directive)
        if line.startswith(".. ") and not line.startswith("   "):
            break

        # Extract content (remove 3-space indent)
        if line.startswith("   "):
            content_lines.append(line[3:])
        elif line.strip() == "":
            content_lines.append("")
        elif found_content:
            break

    # Strip trailing empty lines
    while content_lines and content_lines[-1].strip() == "":
        content_lines.pop()

    return "\n".join(content_lines)


def _parse_comma_list(value: str) -> list[str]:
    """Parse a comma-separated list of values.

    Args:
        value: Comma-separated string

    Returns:
        List of stripped values
    """
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_multiline_list(value: str) -> list[str]:
    """Parse a multi-line list (newline separated).

    Args:
        value: Newline-separated string

    Returns:
        List of stripped values
    """
    if not value:
        return []
    return [v.strip() for v in value.split("\n") if v.strip()]


# =============================================================================
# Epic Parsing
# =============================================================================


def parse_epic_content(content: str) -> ParsedEpic | None:
    """Parse RST content containing a define-epic directive.

    Args:
        content: Full RST file content

    Returns:
        ParsedEpic or None if no epic directive found
    """
    match = DEFINE_EPIC_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()

    # Get content after directive
    directive_end = match.end()
    remaining = content[directive_end:]

    # Extract description (content before any epic-story directives)
    description_lines = []
    for line in remaining.split("\n"):
        if line.startswith(".. epic-story::"):
            break
        if line.startswith("   ") and line.strip():
            description_lines.append(line[3:])
        elif line.strip() == "" and description_lines:
            description_lines.append("")

    # Strip trailing empty lines
    while description_lines and description_lines[-1].strip() == "":
        description_lines.pop()

    description = "\n".join(description_lines)

    # Extract story references
    story_refs = [m.group(1).strip() for m in EPIC_STORY_PATTERN.finditer(content)]

    return ParsedEpic(
        slug=slug,
        description=description,
        story_refs=story_refs,
    )


def parse_epic_file(file_path: Path) -> Epic | None:
    """Parse an RST file containing an epic directive.

    Args:
        file_path: Path to the RST file

    Returns:
        Epic entity or None if parsing fails
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_epic_content(content)
    if not parsed:
        logger.debug(f"No define-epic directive found in {file_path}")
        return None

    return Epic(
        slug=parsed.slug,
        description=parsed.description,
        story_refs=parsed.story_refs,
    )


def scan_epic_directory(epic_dir: Path) -> list[Epic]:
    """Scan a directory for RST files containing epic directives.

    Args:
        epic_dir: Directory to scan

    Returns:
        List of parsed Epic entities
    """
    epics = []

    if not epic_dir.exists():
        logger.debug(f"Epic directory not found: {epic_dir}")
        return epics

    for rst_file in epic_dir.glob("*.rst"):
        epic = parse_epic_file(rst_file)
        if epic:
            epics.append(epic)

    logger.info(f"Parsed {len(epics)} epics from {epic_dir}")
    return epics


# =============================================================================
# Journey Parsing
# =============================================================================


def parse_journey_content(content: str) -> ParsedJourney | None:
    """Parse RST content containing a define-journey directive.

    Args:
        content: Full RST file content

    Returns:
        ParsedJourney or None if no journey directive found
    """
    match = DEFINE_JOURNEY_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()

    # Get content after directive
    directive_end = match.end()
    remaining = content[directive_end:]

    # Extract options
    options = _extract_options(remaining)

    # Extract goal (content after options)
    goal = _extract_content(remaining)

    # Parse steps from the full content
    steps = []

    # Find all step directives and their positions
    step_patterns = [
        (STEP_PHASE_PATTERN, StepType.PHASE),
        (STEP_STORY_PATTERN, StepType.STORY),
        (STEP_EPIC_PATTERN, StepType.EPIC),
    ]

    step_matches = []
    for pattern, step_type in step_patterns:
        for m in pattern.finditer(content):
            step_matches.append((m.start(), m.end(), step_type, m.group(1).strip()))

    # Sort by position
    step_matches.sort(key=lambda x: x[0])

    # Create steps with descriptions for phases
    for i, (start, end, step_type, ref) in enumerate(step_matches):
        description = ""
        if step_type == StepType.PHASE:
            # Extract phase description (content until next directive)
            next_start = (
                step_matches[i + 1][0] if i + 1 < len(step_matches) else len(content)
            )
            phase_content = content[end:next_start]
            desc_lines = []
            for line in phase_content.split("\n"):
                if line.startswith(".. "):
                    break
                if line.startswith("   ") and line.strip():
                    desc_lines.append(line[3:])
            description = "\n".join(desc_lines)

        steps.append(JourneyStep(step_type=step_type, ref=ref, description=description))

    return ParsedJourney(
        slug=slug,
        persona=options.get("persona", ""),
        intent=options.get("intent", ""),
        outcome=options.get("outcome", ""),
        goal=goal,
        depends_on=_parse_comma_list(options.get("depends-on", "")),
        preconditions=_parse_multiline_list(options.get("preconditions", "")),
        postconditions=_parse_multiline_list(options.get("postconditions", "")),
        steps=steps,
    )


def parse_journey_file(file_path: Path) -> Journey | None:
    """Parse an RST file containing a journey directive.

    Args:
        file_path: Path to the RST file

    Returns:
        Journey entity or None if parsing fails
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_journey_content(content)
    if not parsed:
        logger.debug(f"No define-journey directive found in {file_path}")
        return None

    return Journey(
        slug=parsed.slug,
        persona=parsed.persona,
        intent=parsed.intent,
        outcome=parsed.outcome,
        goal=parsed.goal,
        depends_on=parsed.depends_on,
        preconditions=parsed.preconditions,
        postconditions=parsed.postconditions,
        steps=parsed.steps,
    )


def scan_journey_directory(journey_dir: Path) -> list[Journey]:
    """Scan a directory for RST files containing journey directives.

    Args:
        journey_dir: Directory to scan

    Returns:
        List of parsed Journey entities
    """
    journeys = []

    if not journey_dir.exists():
        logger.debug(f"Journey directory not found: {journey_dir}")
        return journeys

    for rst_file in journey_dir.glob("*.rst"):
        journey = parse_journey_file(rst_file)
        if journey:
            journeys.append(journey)

    logger.info(f"Parsed {len(journeys)} journeys from {journey_dir}")
    return journeys


# =============================================================================
# Accelerator Parsing
# =============================================================================


def parse_accelerator_content(content: str) -> ParsedAccelerator | None:
    """Parse RST content containing a define-accelerator directive.

    Args:
        content: Full RST file content

    Returns:
        ParsedAccelerator or None if no accelerator directive found
    """
    match = DEFINE_ACCELERATOR_PATTERN.search(content)
    if not match:
        return None

    slug = match.group(1).strip()

    # Get content after directive
    directive_end = match.end()
    remaining = content[directive_end:]

    # Extract options
    options = _extract_options(remaining)

    # Extract objective (content after options)
    objective = _extract_content(remaining)

    return ParsedAccelerator(
        slug=slug,
        status=options.get("status", ""),
        milestone=options.get("milestone", ""),
        acceptance=options.get("acceptance", ""),
        objective=objective,
        sources_from=_parse_comma_list(options.get("sources-from", "")),
        publishes_to=_parse_comma_list(options.get("publishes-to", "")),
        depends_on=_parse_comma_list(options.get("depends-on", "")),
        feeds_into=_parse_comma_list(options.get("feeds-into", "")),
    )


def parse_accelerator_file(file_path: Path) -> Accelerator | None:
    """Parse an RST file containing an accelerator directive.

    Args:
        file_path: Path to the RST file

    Returns:
        Accelerator entity or None if parsing fails
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    parsed = parse_accelerator_content(content)
    if not parsed:
        logger.debug(f"No define-accelerator directive found in {file_path}")
        return None

    # Convert string lists to IntegrationReference for sources_from/publishes_to
    sources_from = [IntegrationReference(slug=s) for s in parsed.sources_from]
    publishes_to = [IntegrationReference(slug=s) for s in parsed.publishes_to]

    return Accelerator(
        slug=parsed.slug,
        status=parsed.status,
        milestone=parsed.milestone or None,
        acceptance=parsed.acceptance or None,
        objective=parsed.objective,
        sources_from=sources_from,
        publishes_to=publishes_to,
        depends_on=parsed.depends_on,
        feeds_into=parsed.feeds_into,
    )


def scan_accelerator_directory(accelerator_dir: Path) -> list[Accelerator]:
    """Scan a directory for RST files containing accelerator directives.

    Args:
        accelerator_dir: Directory to scan

    Returns:
        List of parsed Accelerator entities
    """
    accelerators = []

    if not accelerator_dir.exists():
        logger.debug(f"Accelerator directory not found: {accelerator_dir}")
        return accelerators

    for rst_file in accelerator_dir.glob("*.rst"):
        accelerator = parse_accelerator_file(rst_file)
        if accelerator:
            accelerators.append(accelerator)

    logger.info(f"Parsed {len(accelerators)} accelerators from {accelerator_dir}")
    return accelerators
