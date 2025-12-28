"""Migrate Gherkin feature files to individual RST story files.

Converts multi-story .feature files to one-story-per-RST-file format,
enabling the RST repository backend.

Usage:
    # Dry run (preview changes)
    python -m julee.docs.sphinx_hcd.scripts.migrate_stories \\
        --feature-dir tests/e2e \\
        --output-dir docs/users/stories

    # Execute migration
    python -m julee.docs.sphinx_hcd.scripts.migrate_stories \\
        --feature-dir tests/e2e \\
        --output-dir docs/users/stories \\
        --execute
"""

import argparse
import logging
import sys
from pathlib import Path

from ..parsers.gherkin import scan_feature_directory
from ..templates.rendering import render_entity

logger = logging.getLogger(__name__)


def migrate_stories(
    feature_dir: Path,
    output_dir: Path,
    project_root: Path,
    dry_run: bool = True,
) -> dict[str, int]:
    """Convert Gherkin feature files to individual RST files.

    Args:
        feature_dir: Directory containing .feature files
        output_dir: Directory to write RST files
        project_root: Project root for relative path computation
        dry_run: If True, only preview changes without writing

    Returns:
        Dict with counts: stories_found, files_written, files_skipped
    """
    stats = {"stories_found": 0, "files_written": 0, "files_skipped": 0}

    # Scan for feature files
    stories = scan_feature_directory(feature_dir, project_root)
    stats["stories_found"] = len(stories)

    if not stories:
        logger.info(f"No .feature files found in {feature_dir}")
        return stats

    logger.info(f"Found {len(stories)} stories in {feature_dir}")

    # Create output directory (unless dry run)
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Generate RST files
    for story in stories:
        # Set page title for RST output
        if not story.page_title:
            story.page_title = story.feature_title

        rst_path = output_dir / f"{story.slug}.rst"
        content = render_entity("story", story)

        if dry_run:
            print(f"\n{'=' * 60}")
            print(f"Would write: {rst_path}")
            print(f"{'=' * 60}")
            print(content[:500])
            if len(content) > 500:
                print(f"... ({len(content) - 500} more characters)")
        else:
            if rst_path.exists():
                logger.warning(f"Skipping existing file: {rst_path}")
                stats["files_skipped"] += 1
                continue

            rst_path.write_text(content)
            logger.info(f"Wrote: {rst_path}")
            stats["files_written"] += 1

    return stats


def main(args: list[str] | None = None) -> int:
    """CLI entry point for story migration."""
    parser = argparse.ArgumentParser(
        description="Migrate Gherkin feature files to RST story files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--feature-dir",
        type=Path,
        required=True,
        help="Directory containing .feature files (e.g., tests/e2e)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for RST output files (e.g., docs/users/stories)",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write files (default is dry-run)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing RST files",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parsed = parser.parse_args(args)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if parsed.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Resolve paths
    project_root = parsed.project_root or Path.cwd()
    feature_dir = (
        parsed.feature_dir
        if parsed.feature_dir.is_absolute()
        else project_root / parsed.feature_dir
    )
    output_dir = (
        parsed.output_dir
        if parsed.output_dir.is_absolute()
        else project_root / parsed.output_dir
    )

    dry_run = not parsed.execute

    if dry_run:
        print("\n*** DRY RUN - No files will be written ***")
        print("*** Use --execute to write files ***\n")

    stats = migrate_stories(
        feature_dir=feature_dir,
        output_dir=output_dir,
        project_root=project_root,
        dry_run=dry_run,
    )

    # Print summary
    print(f"\n{'=' * 60}")
    print("Migration Summary")
    print(f"{'=' * 60}")
    print(f"Stories found: {stats['stories_found']}")
    if not dry_run:
        print(f"Files written: {stats['files_written']}")
        print(f"Files skipped: {stats['files_skipped']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
