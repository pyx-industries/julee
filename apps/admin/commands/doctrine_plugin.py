"""Pytest plugin for collecting doctrine test results.

This plugin captures test docstrings during collection and pass/fail
status during execution, enabling structured output of doctrine
verification results.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RuleResult:
    """Result of verifying a single doctrine rule."""

    statement: str
    test_name: str
    test_file: str
    passed: bool = True
    failure_message: str = ""


@dataclass
class CategoryResult:
    """Results for a doctrine category (test class)."""

    name: str
    description: str
    rules: list[RuleResult] = field(default_factory=list)


@dataclass
class DoctrineResults:
    """Collected doctrine verification results."""

    areas: dict[str, list[CategoryResult]] = field(default_factory=dict)


class DoctrineCollector:
    """Pytest plugin that collects doctrine test results.

    This plugin hooks into pytest's collection and test execution phases
    to capture both the doctrine rules (from docstrings) and their
    verification status (pass/fail).
    """

    def __init__(self):
        self.results = DoctrineResults()
        self._test_map: dict[str, RuleResult] = {}  # nodeid -> RuleResult

    def pytest_collection_modifyitems(self, items):
        """Capture test docstrings during collection.

        This hook is called after pytest has collected all tests but
        before execution. We extract docstrings from test methods
        and organize them by area and category.
        """
        for item in items:
            # Only process doctrine tests
            if "_doctrine" not in item.fspath.basename:
                continue

            # Extract area from filename: test_foo_doctrine.py -> Foo
            filename = Path(item.fspath).name
            area_name = filename.replace("test_", "").replace("_doctrine.py", "")
            area_name = area_name.replace("_", " ").title()

            # Get or create area
            if area_name not in self.results.areas:
                self.results.areas[area_name] = []

            # Get class info
            if hasattr(item, "cls") and item.cls is not None:
                class_name = item.cls.__name__
                class_doc = item.cls.__doc__ or ""

                # Strip "Test" prefix and make readable
                category_name = class_name[4:] if class_name.startswith("Test") else class_name
                readable_name = ""
                for char in category_name:
                    if char.isupper() and readable_name:
                        readable_name += " "
                    readable_name += char

                # Find or create category
                category = None
                for cat in self.results.areas[area_name]:
                    if cat.name == readable_name:
                        category = cat
                        break

                if category is None:
                    category = CategoryResult(
                        name=readable_name,
                        description=class_doc.split("\n")[0] if class_doc else "",
                    )
                    self.results.areas[area_name].append(category)

                # Extract test docstring
                test_doc = item.function.__doc__ or ""
                if test_doc:
                    # Only use first line for rule statement
                    first_line = test_doc.split("\n")[0].strip()

                    rule = RuleResult(
                        statement=first_line,
                        test_name=item.name,
                        test_file=filename,
                    )
                    category.rules.append(rule)
                    self._test_map[item.nodeid] = rule

    def pytest_runtest_logreport(self, report):
        """Capture pass/fail status after each test runs.

        This hook is called for each phase of test execution (setup, call, teardown).
        We capture the result from the 'call' phase.
        """
        if report.when == "call":
            if report.nodeid in self._test_map:
                rule = self._test_map[report.nodeid]
                rule.passed = report.passed
                if not report.passed and report.longrepr:
                    # Extract a concise failure message
                    longrepr_str = str(report.longrepr)
                    # Try to get just the assertion message
                    lines = longrepr_str.split("\n")
                    for line in lines:
                        if "AssertionError" in line or "assert " in line:
                            rule.failure_message = line.strip()[:200]
                            break
                    else:
                        # Fallback: use last non-empty line
                        for line in reversed(lines):
                            if line.strip():
                                rule.failure_message = line.strip()[:200]
                                break

    def get_results_dict(self) -> dict:
        """Convert results to dict format for template rendering.

        Returns:
            Dict structure suitable for Jinja2 template rendering
        """
        result = {}
        for area, categories in self.results.areas.items():
            result[area] = []
            for cat in categories:
                cat_dict = {
                    "name": cat.name,
                    "description": cat.description,
                    "rules": [
                        {
                            "statement": r.statement,
                            "test_name": r.test_name,
                            "test_file": r.test_file,
                            "passed": r.passed,
                            "failure_message": r.failure_message,
                        }
                        for r in cat.rules
                    ],
                }
                result[area].append(cat_dict)
        return result


def run_doctrine_verification(tests_dir: Path) -> tuple[dict, int]:
    """Run doctrine tests and collect results.

    Args:
        tests_dir: Directory containing doctrine test files

    Returns:
        Tuple of (results dict for template rendering, exit code)
    """
    import sys
    from io import StringIO

    import pytest

    collector = DoctrineCollector()

    # Capture pytest output so we can suppress it
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()

    try:
        # Run pytest with our plugin, collecting only doctrine tests
        # Override addopts to disable xdist and coverage from pyproject.toml
        exit_code = pytest.main(
            [
                str(tests_dir),
                "-o", "addopts=",  # Clear default addopts (disables xdist, coverage)
                "--tb=short",
                "-q",  # Quiet mode
            ],
            plugins=[collector],
        )
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return collector.get_results_dict(), exit_code
