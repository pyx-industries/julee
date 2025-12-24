"""Gherkin feature file parser.

Parses .feature files to extract user story information.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from ..domain.models.story import Story

logger = logging.getLogger(__name__)


@dataclass
class ParsedFeature:
    """Raw parsed data from a feature file.

    This intermediate representation holds the extracted values
    before creating a Story entity.
    """

    feature_title: str
    persona: str
    i_want: str
    so_that: str
    gherkin_snippet: str


def parse_feature_content(content: str) -> ParsedFeature:
    """Parse the content of a Gherkin feature file.

    Extracts:
    - Feature: <title>
    - As a <persona>
    - I want to <action>
    - So that <benefit>
    - The story header (everything before Scenario/Background)

    Args:
        content: The full text content of a .feature file

    Returns:
        ParsedFeature with extracted values (defaults for missing fields)
    """
    # Extract header components using regex
    feature_match = re.search(r"^Feature:\s*(.+)$", content, re.MULTILINE)
    as_a_match = re.search(r"^\s*As an?\s+(.+)$", content, re.MULTILINE)
    i_want_match = re.search(r"^\s*I want to\s+(.+)$", content, re.MULTILINE)
    so_that_match = re.search(r"^\s*So that\s+(.+)$", content, re.MULTILINE)

    # Extract Gherkin snippet (story header only, stop before scenarios)
    lines = content.split("\n")
    snippet_lines = []
    for line in lines:
        stripped = line.strip()
        # Stop at scenario markers or step keywords at start of line
        if stripped.startswith(
            ("Scenario", "Background", "@", "Given", "When", "Then", "And", "But")
        ):
            break
        if stripped:
            snippet_lines.append(line)
    gherkin_snippet = "\n".join(snippet_lines)

    return ParsedFeature(
        feature_title=feature_match.group(1).strip() if feature_match else "Unknown",
        persona=as_a_match.group(1).strip() if as_a_match else "unknown",
        i_want=i_want_match.group(1).strip() if i_want_match else "do something",
        so_that=so_that_match.group(1).strip() if so_that_match else "achieve a goal",
        gherkin_snippet=gherkin_snippet,
    )


def parse_feature_file(
    file_path: Path,
    project_root: Path,
    app_slug: str | None = None,
) -> Story | None:
    """Parse a single feature file and return a Story.

    Args:
        file_path: Absolute path to the .feature file
        project_root: Project root for computing relative paths
        app_slug: Optional app slug override. If None, extracted from path.

    Returns:
        Story entity, or None if parsing fails
    """
    try:
        content = file_path.read_text()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return None

    # Parse the content
    parsed = parse_feature_content(content)

    # Compute relative path
    try:
        rel_path = file_path.relative_to(project_root)
    except ValueError:
        rel_path = file_path
        logger.warning(f"Feature file {file_path} is not under project root")

    # Extract app slug from path if not provided
    # Expected: tests/e2e/{app}/features/{name}.feature
    if app_slug is None:
        parts = rel_path.parts
        if len(parts) >= 4 and parts[2] != "features":
            app_slug = parts[2]
        else:
            app_slug = "unknown"

    return Story.from_feature_file(
        feature_title=parsed.feature_title,
        persona=parsed.persona,
        i_want=parsed.i_want,
        so_that=parsed.so_that,
        app_slug=app_slug,
        file_path=str(rel_path),
        abs_path=str(file_path),
        gherkin_snippet=parsed.gherkin_snippet,
    )


def scan_feature_directory(
    feature_dir: Path,
    project_root: Path,
) -> list[Story]:
    """Scan a directory tree for .feature files and parse them.

    Args:
        feature_dir: Root directory to scan (e.g., tests/e2e/)
        project_root: Project root for computing relative paths

    Returns:
        List of parsed Story entities
    """
    stories = []

    if not feature_dir.exists():
        logger.info(
            f"Feature files directory not found at {feature_dir} - no stories to index"
        )
        return stories

    for feature_file in feature_dir.rglob("*.feature"):
        story = parse_feature_file(feature_file, project_root)
        if story:
            stories.append(story)

    logger.info(f"Indexed {len(stories)} Gherkin stories from {feature_dir}")
    return stories
