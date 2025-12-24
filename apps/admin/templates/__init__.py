"""Jinja2 templates for admin CLI output.

Provides template-based rendering for doctrine verification
and other admin command output formatting.
"""

from jinja2 import Environment, PackageLoader

# Create Jinja2 environment
_env = Environment(
    loader=PackageLoader("apps.admin", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)


def get_template(name: str):
    """Get a template by name.

    Args:
        name: Template filename (e.g., 'doctrine_verify_summary.txt.j2')

    Returns:
        Jinja2 Template object
    """
    return _env.get_template(name)


def render_doctrine_verify(
    results: dict,
    verbose: bool = False,
) -> str:
    """Render doctrine verification results.

    Args:
        results: Dict mapping area to list of categories with rule results
        verbose: If True, use summary format; otherwise use table format

    Returns:
        Formatted output string
    """
    # Calculate summary statistics
    total_tests = 0
    passed_count = 0
    failed_count = 0

    for categories in results.values():
        for category in categories:
            for rule in category["rules"]:
                total_tests += 1
                if rule["passed"]:
                    passed_count += 1
                else:
                    failed_count += 1

    template_name = "doctrine_verify_summary.txt.j2" if verbose else "doctrine_verify_table.txt.j2"
    template = _env.get_template(template_name)

    return template.render(
        results=results,
        total_tests=total_tests,
        passed_count=passed_count,
        failed_count=failed_count,
        all_passed=(failed_count == 0),
    )
