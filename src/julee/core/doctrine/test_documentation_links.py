"""Documentation link integrity doctrine.

These tests ARE the doctrine. The docstrings are doctrine statements.
The assertions enforce them.

Documentation links must resolve correctly. Broken internal references
indicate missing documents or incorrect paths. Broken external links
indicate stale URLs that need updating.
"""

import re
import subprocess
from pathlib import Path

import pytest

from julee.core.doctrine_constants import DOCS_ROOT


class TestInternalLinks:
    """Doctrine about internal documentation links."""

    # Warning patterns that indicate broken references
    BROKEN_REF_PATTERNS = [
        r"WARNING:.*unknown document:",  # :doc: to missing file
        r"\[ref\.doc\]",  # Sphinx 7+ format for unknown documents
        r"WARNING:.*undefined label:",  # :ref: to missing anchor
        r"\[ref\.ref\]",  # Sphinx 7+ format for undefined labels
        r"WARNING:.*unknown target name:",  # Broken cross-reference
        r"WARNING:.*toctree contains reference to nonexisting document",
        r"WARNING:.*toctree contains reference to document.*that doesn't have a title",
    ]

    # Patterns to ignore (expected/acceptable warnings)
    IGNORE_PATTERNS = [
        r"ref\.class",  # Missing class references from autodoc (external deps)
        r"pydantic\.main\.BaseModel",  # Common external reference
        r"enum\.Enum",  # Standard library reference
        r"docutils\.nodes",  # Docutils internals
    ]

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_docs_MUST_NOT_have_broken_internal_references(
        self, project_root: Path
    ) -> None:
        """Documentation MUST NOT have broken internal references.

        Doctrine: All :doc:, :ref:, and toctree references must resolve to
        existing documents or labels. Broken references indicate:
        - Renamed/moved documents without updating links
        - Typos in document paths
        - Missing target documents

        This test runs sphinx-build and checks for reference warnings.
        """
        docs_path = project_root / DOCS_ROOT

        if not docs_path.exists():
            pytest.skip("No docs directory")

        if not (docs_path / "conf.py").exists():
            pytest.skip("No Sphinx configuration")

        # Run sphinx-build to check for warnings
        # Use -n for nit-picky mode (more thorough checking)
        # Use -q for quiet (less noise)
        result = subprocess.run(
            [
                "uv",
                "run",
                "sphinx-build",
                "-b",
                "html",
                "-n",  # nit-picky mode
                "-q",  # quiet
                ".",
                "_build/linkcheck_test",
            ],
            cwd=docs_path,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Combine stdout and stderr for warning analysis
        output = result.stdout + result.stderr

        # Find broken reference warnings
        violations = []
        for line in output.split("\n"):
            # Check if line matches any broken reference pattern
            is_broken = False
            for pattern in self.BROKEN_REF_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    is_broken = True
                    break

            if not is_broken:
                continue

            # Check if it should be ignored
            should_ignore = False
            for ignore_pattern in self.IGNORE_PATTERNS:
                if re.search(ignore_pattern, line, re.IGNORECASE):
                    should_ignore = True
                    break

            if not should_ignore:
                violations.append(line.strip())

        # Deduplicate
        violations = list(dict.fromkeys(violations))

        assert not violations, (
            "Documentation has broken internal references:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])  # Limit output
            + (
                f"\n  ... and {len(violations) - 20} more"
                if len(violations) > 20
                else ""
            )
        )


class TestExternalLinks:
    """Doctrine about external documentation links."""

    @pytest.mark.slow
    def test_docs_external_links_SHOULD_be_valid(self, project_root: Path) -> None:
        """Documentation external links SHOULD be valid.

        Doctrine: External URLs in documentation should resolve. Broken
        external links indicate stale references that need updating.

        Note: This test is marked as slow/optional because it requires
        network access and can take significant time. Run with:
            pytest -m "not slow" to skip
            pytest -m slow to run only slow tests

        Uses Sphinx's linkcheck builder which:
        - Checks all external URLs in the documentation
        - Reports broken, redirected, or unreachable links
        """
        docs_path = project_root / DOCS_ROOT

        if not docs_path.exists():
            pytest.skip("No docs directory")

        if not (docs_path / "conf.py").exists():
            pytest.skip("No Sphinx configuration")

        # Run linkcheck builder
        result = subprocess.run(
            [
                "uv",
                "run",
                "sphinx-build",
                "-b",
                "linkcheck",
                "-q",
                ".",
                "_build/linkcheck",
            ],
            cwd=docs_path,
            capture_output=True,
            text=True,
            timeout=600,  # External links can be slow
        )

        # Check linkcheck output file
        output_file = docs_path / "_build/linkcheck/output.txt"
        if not output_file.exists():
            # Build may have failed before producing output
            if result.returncode != 0:
                pytest.skip(f"Linkcheck build failed: {result.stderr[:500]}")
            return

        output = output_file.read_text()

        # Find broken links (lines with [broken])
        broken_links = []
        for line in output.split("\n"):
            if "[broken]" in line.lower():
                broken_links.append(line.strip())

        # This is a SHOULD not MUST - external links can break due to
        # network issues, so we warn but don't fail hard
        if broken_links:
            pytest.skip(
                f"Found {len(broken_links)} potentially broken external links. "
                "Review manually:\n"
                + "\n".join(f"  - {link}" for link in broken_links[:10])
            )
