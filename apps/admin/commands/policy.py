"""Policy commands.

Commands for managing adoptable policies. Policies are strategic choices
that solutions can make, unlike doctrine (axiomatic, universal).

See ADR 005: Doctrine and Policy Separation.
"""

import os
from pathlib import Path

import click

# Project root and policy locations
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
POLICIES_DIR = PROJECT_ROOT / "src" / "julee" / "core" / "policies"


@click.group(name="policy")
def policy_group() -> None:
    """Manage adoptable policies."""
    pass


@policy_group.command(name="list")
@click.option("--adopted", is_flag=True, help="Show only adopted policies")
@click.option("--all", "show_all", is_flag=True, help="Show all policies with status")
def list_policies(adopted: bool, show_all: bool) -> None:
    """List available policies.

    Policies are strategic choices that solutions can adopt. Framework-default
    policies apply automatically to solutions with [tool.julee] in pyproject.toml.

    Use --adopted to see which policies are in effect for the current solution.
    """
    from julee.core.policies import get_framework_default_policies, list_policies

    all_policies = list_policies()

    if not all_policies:
        click.echo("No policies found.")
        return

    if adopted:
        # Show only framework defaults for now
        # TODO: Read pyproject.toml to get adopted/skipped policies
        click.echo("Adopted Policies (framework defaults):\n")
        for policy in get_framework_default_policies():
            click.echo(f"  {policy.slug}")
            click.echo(f"    {policy.description}\n")
    else:
        click.echo("Available Policies:\n")
        for policy in all_policies:
            marker = "[default]" if policy.framework_default else "[opt-in]"
            click.echo(f"  {policy.slug} {marker}")
            click.echo(f"    {policy.description}\n")


@policy_group.command(name="verify")
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed verification report"
)
@click.option("--policy", "-p", "policy_filter", help="Filter to specific policy")
@click.option(
    "--all", "verify_all", is_flag=True, help="Verify all policies (informational)"
)
@click.option(
    "--target",
    "-t",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Target directory to verify (default: current project)",
)
def verify_policies(
    verbose: bool,
    policy_filter: str | None,
    verify_all: bool,
    target: str | None,
) -> None:
    """Verify compliance with adopted policies.

    By default, verifies only framework-default policies. Use --all to verify
    all policies (informational for non-adopted policies).

    Use --target to verify an external solution:

        julee-admin policy verify --target /path/to/solution
    """
    from apps.admin.commands.doctrine_plugin import run_doctrine_verification

    from julee.core.policies import get_framework_default_policies, get_policy, list_policies

    # Set JULEE_TARGET environment variable if target specified
    if target:
        os.environ["JULEE_TARGET"] = target
        click.echo(f"Target: {target}\n")

    # Determine which policies to verify
    if verify_all:
        policies_to_verify = list_policies()
    else:
        # Only framework defaults
        # TODO: Also include explicitly adopted policies from pyproject.toml
        policies_to_verify = get_framework_default_policies()

    if policy_filter:
        policy = get_policy(policy_filter)
        if not policy:
            click.echo(f"Policy '{policy_filter}' not found.")
            click.echo(f"Available: {', '.join(p.slug for p in list_policies())}")
            raise SystemExit(1)
        policies_to_verify = [policy]

    if not policies_to_verify:
        click.echo("No policies to verify.")
        return

    click.echo(f"Verifying {len(policies_to_verify)} policies...\n")

    all_passed = True
    results = []

    for policy in policies_to_verify:
        # Find the test module for this policy
        policy_dir = POLICIES_DIR / policy.slug.replace("-", "_")
        test_file = policy_dir / "test_compliance.py"

        if not test_file.exists():
            results.append((policy.slug, "skipped", "No compliance tests found"))
            continue

        # Run the policy's compliance tests
        test_results, exit_code = run_doctrine_verification(policy_dir)

        if exit_code == 0:
            results.append((policy.slug, "passed", ""))
        else:
            all_passed = False
            # Extract failure details
            failures = []
            for area, rules in test_results.items():
                for rule in rules:
                    if rule.get("status") == "failed":
                        failures.append(rule.get("name", "unknown"))
            results.append((policy.slug, "FAILED", ", ".join(failures)))

    # Display results
    click.echo("=" * 60)
    click.echo("POLICY VERIFICATION RESULTS")
    click.echo("=" * 60)
    click.echo("")

    for slug, status, details in results:
        if status == "passed":
            click.echo(f"  {slug} ... passed")
        elif status == "skipped":
            click.echo(f"  {slug} ... skipped ({details})")
        else:
            click.echo(f"  {slug} ... FAILED")
            if verbose and details:
                click.echo(f"    Failures: {details}")

    click.echo("")

    if all_passed:
        click.echo("All policies passed.")
    else:
        click.echo("Some policies failed. Use --verbose for details.")
        raise SystemExit(1)
