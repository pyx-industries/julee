"""Pytest-based doctrine verifier.

Runs doctrine tests via pytest and collects structured results.
This is an infrastructure concern - the use case just calls verify().
"""

import sys
from io import StringIO
from pathlib import Path

from julee.core.entities.doctrine import (
    DoctrineRule,
    DoctrineVerificationReport,
    DoctrineVerificationResult,
)

__all__ = ["PytestDoctrineVerifier"]


class PytestDoctrineVerifier:
    """Verifies doctrine compliance by running pytest.

    This service wraps pytest execution and transforms raw test
    results into DoctrineVerificationReport entities.
    """

    def __init__(self, doctrine_dir: Path, entities_dir: Path) -> None:
        """Initialize verifier.

        Args:
            doctrine_dir: Directory containing doctrine test files
            entities_dir: Directory containing entity definitions
        """
        self.doctrine_dir = doctrine_dir
        self.entities_dir = entities_dir

    async def verify(
        self,
        target: Path,
        area: str | None = None,
    ) -> DoctrineVerificationReport:
        """Verify a solution's compliance with doctrine.

        Runs pytest on doctrine test files and collects results.

        Args:
            target: Path to the solution to verify (set as JULEE_TARGET)
            area: Optional area to filter verification

        Returns:
            Complete verification report with pass/fail for each rule
        """
        import os

        import pytest

        # Set target for doctrine tests
        os.environ["JULEE_TARGET"] = str(target)

        # Build test path
        test_path = self.doctrine_dir
        if area:
            # Try to find specific test file for area
            area_slug = area.lower().replace(" ", "_").replace("-", "_")
            specific_test = test_path / f"test_{area_slug}.py"
            if specific_test.exists():
                test_path = specific_test

        # Create collector plugin
        collector = _DoctrineResultCollector(self.entities_dir)

        # Capture pytest output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            exit_code = pytest.main(
                [
                    str(test_path),
                    "-o", "addopts=",  # Clear default addopts
                    "--tb=short",
                    "-q",
                ],
                plugins=[collector],
            )
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        return DoctrineVerificationReport(
            target=target,
            results=tuple(collector.results),
            scope="all",
        )


class _DoctrineResultCollector:
    """Pytest plugin that collects doctrine test results.

    Hooks into pytest to capture test docstrings (rules) and
    execution results (pass/fail).
    """

    def __init__(self, entities_dir: Path) -> None:
        self.entities_dir = entities_dir
        self.results: list[DoctrineVerificationResult] = []
        self._test_map: dict[str, DoctrineVerificationResult] = {}

    def pytest_collection_modifyitems(self, items):
        """Capture test docstrings during collection."""
        for item in items:
            filepath = Path(item.fspath)
            filename = filepath.name

            # Only process doctrine tests
            in_doctrine_dir = filepath.parent.name == "doctrine"
            has_doctrine_in_name = "_doctrine" in filename or "doctrine_" in filename
            if not in_doctrine_dir and not has_doctrine_in_name:
                continue

            # Get class info
            if hasattr(item, "cls") and item.cls is not None:
                class_name = item.cls.__name__

                # Make category name readable
                category_name = class_name[4:] if class_name.startswith("Test") else class_name
                readable_category = ""
                for char in category_name:
                    if char.isupper() and readable_category:
                        readable_category += " "
                    readable_category += char

                # Get area name from filename
                area_slug = filename.replace("test_", "").replace("_doctrine.py", "").replace(".py", "")
                area_name = area_slug.replace("_", " ").title()

                # Extract test docstring
                test_doc = item.function.__doc__ or ""
                if test_doc:
                    first_line = test_doc.split("\n")[0].strip()

                    rule = DoctrineRule(
                        statement=first_line,
                        test_name=item.name,
                        test_file=filepath,
                        category=readable_category,
                        area=area_name,
                    )

                    result = DoctrineVerificationResult(
                        rule=rule,
                        passed=True,  # Will be updated after test runs
                        error_message=None,
                    )

                    self.results.append(result)
                    self._test_map[item.nodeid] = result

    def pytest_runtest_logreport(self, report):
        """Capture pass/fail status after each test runs."""
        if report.when == "call":
            if report.nodeid in self._test_map:
                old_result = self._test_map[report.nodeid]
                idx = self.results.index(old_result)

                error_message = None
                if not report.passed and report.longrepr:
                    longrepr_str = str(report.longrepr)
                    lines = longrepr_str.split("\n")
                    for line in lines:
                        if "AssertionError" in line or "assert " in line:
                            error_message = line.strip()[:200]
                            break
                    else:
                        for line in reversed(lines):
                            if line.strip():
                                error_message = line.strip()[:200]
                                break

                # Replace with updated result (frozen model)
                new_result = DoctrineVerificationResult(
                    rule=old_result.rule,
                    passed=report.passed,
                    error_message=error_message,
                )
                self.results[idx] = new_result
                self._test_map[report.nodeid] = new_result
