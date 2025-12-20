"""docutils-based RST parser.

Parses RST files using docutils AST traversal instead of regex.
Extracts entity data and document structure (page_title, preamble, epilogue)
for lossless round-trip: RST → Domain Entity → RST.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive, directives
from docutils.utils import Reporter

from .directive_specs import DIRECTIVE_SPECS, get_option_spec

logger = logging.getLogger(__name__)


# =============================================================================
# Data Collection Directive
# =============================================================================


class DataCollectorDirective(Directive):
    """Base directive that collects data without rendering.

    Instead of producing docutils nodes, this directive stores its data
    in the document settings for later extraction.
    """

    required_arguments = 1
    optional_arguments = 0
    has_content = True
    final_argument_whitespace = False

    def run(self) -> list:
        """Collect directive data and return empty node list."""
        # Initialize collected_entities if needed
        if not hasattr(self.state.document.settings, "collected_entities"):
            self.state.document.settings.collected_entities = []

        # Store directive data
        self.state.document.settings.collected_entities.append({
            "directive_type": self.name,
            "slug": self.arguments[0] if self.arguments else "",
            "options": dict(self.options),
            "content": "\n".join(self.content),
            "lineno": self.lineno,
            "content_offset": self.content_offset,
        })

        return []


def _make_collector_class(directive_name: str, option_spec: dict) -> type:
    """Create a DataCollectorDirective subclass for a specific directive.

    Args:
        directive_name: Name to use for the directive
        option_spec: Dict of option names to validator functions

    Returns:
        Directive class configured for this directive type
    """
    class_name = directive_name.replace("-", "_").title().replace("_", "") + "Collector"
    return type(
        class_name,
        (DataCollectorDirective,),
        {"option_spec": option_spec},
    )


_registered = False


def register_collector_directives() -> None:
    """Register data-collecting versions of all HCD directives.

    These directives collect data during parsing but produce no output.
    """
    global _registered
    if _registered:
        return

    for name, spec in DIRECTIVE_SPECS.items():
        option_spec = spec.get("options", {})
        collector = _make_collector_class(name, option_spec)
        directives.register_directive(name, collector)

    _registered = True


# =============================================================================
# Document Structure Extraction
# =============================================================================


@dataclass
class ParsedDocument:
    """Parsed RST document with extracted structure and entities.

    Attributes:
        title: Page title (first H1 heading)
        preamble: Content before the first directive
        epilogue: Content after the last directive
        entities: List of collected entity data
        raw_content: Original RST content
    """

    title: str = ""
    preamble: str = ""
    epilogue: str = ""
    entities: list[dict] = field(default_factory=list)
    raw_content: str = ""


def _extract_title_from_doctree(doctree: nodes.document) -> str:
    """Extract the page title from a docutils document tree.

    Args:
        doctree: Parsed docutils document

    Returns:
        Title text if found, empty string otherwise
    """
    for node in doctree.traverse(nodes.title):
        return node.astext()
    return ""


def _find_title_block_end(content: str) -> int:
    """Find the end position of the title/header block in RST content.

    The title block includes:
    - The title line
    - The underline (=== or ---)
    - Any blank lines immediately after

    Args:
        content: RST content

    Returns:
        Character position after the title block
    """
    lines = content.split("\n")
    title_end = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for title underline patterns
        if re.match(r"^[=\-~^\"\'`]+$", line) and len(line) >= 3:
            # This is an underline - title block ends after this
            title_end = sum(len(lines[j]) + 1 for j in range(i + 1))
            # Skip any blank lines after underline
            i += 1
            while i < len(lines) and not lines[i].strip():
                title_end = sum(len(lines[j]) + 1 for j in range(i + 1))
                i += 1
            break
        elif line.strip() and i + 1 < len(lines):
            # Check if next line is underline (overline style)
            next_line = lines[i + 1]
            if re.match(r"^[=\-~^\"\'`]+$", next_line) and len(next_line) >= len(line.rstrip()):
                i += 1
                continue
        i += 1

    return title_end


def _find_first_directive_position(content: str, entities: list[dict]) -> int | None:
    """Find the character position of the first directive in content.

    Args:
        content: RST content
        entities: Collected entity data with line numbers

    Returns:
        Character position or None if no directives
    """
    if not entities:
        return None

    # Find minimum line number
    first_lineno = min(e["lineno"] for e in entities)

    # Convert line number to character position
    lines = content.split("\n")
    pos = 0
    for i in range(first_lineno - 1):
        if i < len(lines):
            pos += len(lines[i]) + 1  # +1 for newline

    return pos


def _find_last_directive_end(content: str, entities: list[dict]) -> int | None:
    """Find the character position after the last directive in content.

    This is tricky because we need to find where the directive content ends,
    not just where it starts.

    Args:
        content: RST content
        entities: Collected entity data

    Returns:
        Character position or None if no directives
    """
    if not entities:
        return None

    # Find the directive with the highest line number
    last_entity = max(entities, key=lambda e: e["lineno"])

    lines = content.split("\n")

    # Start from the directive line
    start_line = last_entity["lineno"] - 1

    # Find the end of the directive content (indented block)
    end_line = start_line + 1
    in_directive = True

    while end_line < len(lines) and in_directive:
        line = lines[end_line]

        # Empty lines are OK within directive content
        if not line.strip():
            end_line += 1
            continue

        # Check if line is indented (part of directive) or starts new content
        if line.startswith("   ") or line.startswith("\t"):
            end_line += 1
        elif line.startswith(".. "):
            # Another directive - could be nested or sibling
            # Check if it's a nested directive (step-*, epic-story)
            if any(line.startswith(f".. {nested}::") for nested in
                   ["step-story", "step-epic", "step-phase", "epic-story"]):
                end_line += 1
            else:
                in_directive = False
        else:
            in_directive = False

    # Convert line number to character position
    pos = sum(len(lines[i]) + 1 for i in range(end_line))

    return pos


def _extract_preamble(
    content: str,
    title_end: int,
    first_directive_pos: int | None,
) -> str:
    """Extract preamble content (between title and first directive).

    Args:
        content: RST content
        title_end: Position after title block
        first_directive_pos: Position of first directive

    Returns:
        Preamble text
    """
    if first_directive_pos is None:
        return ""

    preamble = content[title_end:first_directive_pos]
    return preamble.strip()


def _extract_epilogue(
    content: str,
    last_directive_end: int | None,
) -> str:
    """Extract epilogue content (after last directive).

    Args:
        content: RST content
        last_directive_end: Position after last directive

    Returns:
        Epilogue text
    """
    if last_directive_end is None:
        return ""

    epilogue = content[last_directive_end:]
    return epilogue.strip()


# =============================================================================
# Main Parsing API
# =============================================================================


def parse_rst_content(content: str) -> ParsedDocument:
    """Parse RST content and extract structure + entity data.

    Args:
        content: RST file content

    Returns:
        ParsedDocument with extracted data
    """
    register_collector_directives()

    # Configure docutils settings to suppress warnings
    settings_overrides = {
        "report_level": Reporter.SEVERE_LEVEL,
        "halt_level": Reporter.SEVERE_LEVEL,
        "collected_entities": [],
    }

    # Parse with docutils
    try:
        doctree = publish_doctree(
            content,
            settings_overrides=settings_overrides,
        )
    except Exception as e:
        logger.warning(f"Failed to parse RST content: {e}")
        return ParsedDocument(raw_content=content)

    # Extract collected entities
    entities = getattr(doctree.settings, "collected_entities", [])

    # Extract document structure
    title = _extract_title_from_doctree(doctree)
    title_end = _find_title_block_end(content) if title else 0
    first_pos = _find_first_directive_position(content, entities)
    last_end = _find_last_directive_end(content, entities)

    preamble = _extract_preamble(content, title_end, first_pos)
    epilogue = _extract_epilogue(content, last_end)

    return ParsedDocument(
        title=title,
        preamble=preamble,
        epilogue=epilogue,
        entities=entities,
        raw_content=content,
    )


def parse_rst_file(path: Path) -> ParsedDocument:
    """Parse an RST file and extract structure + entity data.

    Args:
        path: Path to RST file

    Returns:
        ParsedDocument with extracted data
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not read {path}: {e}")
        return ParsedDocument()

    result = parse_rst_content(content)
    return result


# =============================================================================
# Utility Functions
# =============================================================================


def parse_comma_list(value: str) -> list[str]:
    """Parse a comma-separated list of values.

    Args:
        value: Comma-separated string

    Returns:
        List of stripped values
    """
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_multiline_list(value: str) -> list[str]:
    """Parse a multi-line list (newline separated).

    Args:
        value: Newline-separated string

    Returns:
        List of stripped values
    """
    if not value:
        return []
    return [v.strip() for v in value.split("\n") if v.strip()]


def find_entity_by_type(
    parsed: ParsedDocument,
    directive_type: str,
) -> dict | None:
    """Find the first entity of a given type in a parsed document.

    Args:
        parsed: ParsedDocument result
        directive_type: Directive name (e.g., 'define-journey')

    Returns:
        Entity data dict or None
    """
    for entity in parsed.entities:
        if entity["directive_type"] == directive_type:
            return entity
    return None


def find_all_entities_by_type(
    parsed: ParsedDocument,
    directive_type: str,
) -> list[dict]:
    """Find all entities of a given type in a parsed document.

    Args:
        parsed: ParsedDocument result
        directive_type: Directive name

    Returns:
        List of entity data dicts
    """
    return [e for e in parsed.entities if e["directive_type"] == directive_type]


# =============================================================================
# Nested Directive Extraction
# =============================================================================

# Patterns for extracting nested directives from content
# These patterns allow optional leading whitespace for nested directives
_STEP_PHASE_PATTERN = re.compile(r"^\s*\.\.\s+step-phase::\s*(.+)$", re.MULTILINE)
_STEP_STORY_PATTERN = re.compile(r"^\s*\.\.\s+step-story::\s*(.+)$", re.MULTILINE)
_STEP_EPIC_PATTERN = re.compile(r"^\s*\.\.\s+step-epic::\s*(.+)$", re.MULTILINE)
_EPIC_STORY_PATTERN = re.compile(r"^\s*\.\.\s+epic-story::\s*(.+)$", re.MULTILINE)


@dataclass
class NestedDirective:
    """A nested directive extracted from content.

    Attributes:
        directive_type: Type of directive (e.g., 'step-story')
        ref: Reference/argument value
        description: Optional description content
        position: Character position in parent content (start)
        end_position: Character position after directive line
    """

    directive_type: str
    ref: str
    description: str = ""
    position: int = 0
    end_position: int = 0


def extract_nested_directives(content: str) -> list[NestedDirective]:
    """Extract nested step-* and epic-story directives from content.

    This uses regex to find nested directives within a parent directive's
    content, since docutils doesn't parse them separately.

    Args:
        content: Directive content text

    Returns:
        List of NestedDirective in order of appearance
    """
    nested = []

    # Find all step/epic-story patterns
    patterns = [
        (_STEP_PHASE_PATTERN, "step-phase"),
        (_STEP_STORY_PATTERN, "step-story"),
        (_STEP_EPIC_PATTERN, "step-epic"),
        (_EPIC_STORY_PATTERN, "epic-story"),
    ]

    for pattern, directive_type in patterns:
        for match in pattern.finditer(content):
            nested.append(NestedDirective(
                directive_type=directive_type,
                ref=match.group(1).strip(),
                position=match.start(),
                end_position=match.end(),
            ))

    # Sort by position
    nested.sort(key=lambda x: x.position)

    # Extract descriptions for step-phase directives
    for i, item in enumerate(nested):
        if item.directive_type == "step-phase":
            # Start after the directive line
            start_pos = item.end_position
            # Find next directive or end of content
            if i + 1 < len(nested):
                end_pos = nested[i + 1].position
            else:
                end_pos = len(content)

            phase_content = content[start_pos:end_pos]

            # Extract description (indented content, skip directive lines)
            desc_lines = []
            for line in phase_content.split("\n"):
                stripped = line.strip()
                # Skip empty lines at start
                if not stripped and not desc_lines:
                    continue
                # Stop at next directive
                if stripped.startswith(".. "):
                    break
                # Collect indented content
                if stripped:
                    desc_lines.append(stripped)
                elif desc_lines:
                    # Preserve internal blank lines
                    desc_lines.append("")

            # Strip trailing empty lines
            while desc_lines and not desc_lines[-1]:
                desc_lines.pop()

            item.description = "\n".join(desc_lines)

    return nested


def extract_story_refs(content: str) -> list[str]:
    """Extract epic-story references from content.

    Args:
        content: RST content

    Returns:
        List of story titles/references
    """
    return [m.group(1).strip() for m in _EPIC_STORY_PATTERN.finditer(content)]
