"""Policy commands.

Commands for managing adoptable policies. Policies are strategic choices
that solutions can make, unlike doctrine (axiomatic, universal).

See ADR 005: Doctrine and Policy Separation.
"""

import asyncio
import os
from pathlib import Path

import click

# Project root and policy compliance test locations
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
POLICY_COMPLIANCE_DIR = PROJECT_ROOT / "src" / "julee" / "core" / "infrastructure" / "policy_compliance"


@click.group(name="policy")
def policy_group() -> None:
    """Manage adoptable policies."""
    pass


@policy_group.command(name="list")
@click.option("--adopted", is_flag=True, help="Show only adopted policies for this solution")
@click.option(
    "--target",
    "-t",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Target solution directory (default: current project)",
)
def list_policies_cmd(adopted: bool, target: str | None) -> None:
    """List available policies.

    Policies are strategic choices that solutions can adopt. Framework-default
    policies apply automatically to solutions with [tool.julee] in pyproject.toml.

    Use --adopted to see which policies are in effect for the current solution.
    """
    from apps.admin.dependencies import (
        find_project_root,
        get_effective_policies_use_case,
        get_list_policies_use_case,
    )

    from julee.core.use_cases.policy.get_effective import GetEffectivePoliciesRequest
    from julee.core.use_cases.policy.list import ListPoliciesRequest

    if adopted:
        # Show policies for a specific solution
        target_path = Path(target) if target else find_project_root()
        use_case = get_effective_policies_use_case()
        response = asyncio.run(
            use_case.execute(GetEffectivePoliciesRequest(solution_root=target_path))
        )

        click.echo(f"Target: {target_path}")

        if not response.config.is_julee_solution:
            click.echo("\nNot a julee solution (no [tool.julee] in pyproject.toml).")
            click.echo("No policies apply.")
            return

        click.echo("\nAdopted Policies:\n")
        for policy in response.policies_to_verify:
            adoption = next(
                (a for a in response.adoptions if a.policy_slug == policy.slug), None
            )
            source = f"[{adoption.source}]" if adoption else ""
            click.echo(f"  {policy.slug} {source}")
            click.echo(f"    {policy.description}\n")

        if response.skipped_policies:
            click.echo("Skipped Policies:\n")
            for policy in response.skipped_policies:
                click.echo(f"  {policy.slug} [skipped]")
    else:
        # Show all available policies
        use_case = get_list_policies_use_case()
        response = asyncio.run(use_case.execute(ListPoliciesRequest()))

        if not response.policies:
            click.echo("No policies found.")
            return

        click.echo("Available Policies:\n")
        for policy in response.policies:
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

    By default, verifies only adopted policies (framework defaults + explicit).
    Use --all to verify all policies (informational for non-adopted policies).

    Use --target to verify an external solution:

        julee-admin policy verify --target /path/to/solution
    """
    from apps.admin.commands.doctrine_plugin import run_doctrine_verification
    from apps.admin.dependencies import (
        find_project_root,
        get_effective_policies_use_case,
        get_list_policies_use_case,
        get_policy_repository,
    )

    from julee.core.use_cases.policy.get_effective import GetEffectivePoliciesRequest
    from julee.core.use_cases.policy.list import ListPoliciesRequest

    # Determine target path
    target_path = Path(target) if target else find_project_root()
    os.environ["JULEE_TARGET"] = str(target_path)
    click.echo(f"Target: {target_path}\n")

    # Determine which policies to verify
    if verify_all:
        # Verify all available policies
        list_use_case = get_list_policies_use_case()
        response = asyncio.run(list_use_case.execute(ListPoliciesRequest()))
        policies_to_verify = response.policies
    else:
        # Verify only adopted policies for this solution
        effective_use_case = get_effective_policies_use_case()
        response = asyncio.run(
            effective_use_case.execute(GetEffectivePoliciesRequest(solution_root=target_path))
        )
        policies_to_verify = response.policies_to_verify

    # Filter to specific policy if requested
    if policy_filter:
        from julee.core.use_cases.policy import GetPolicyRequest, GetPolicyUseCase

        policy_repo = get_policy_repository()
        get_use_case = GetPolicyUseCase(policy_repo)
        get_response = asyncio.run(get_use_case.execute(GetPolicyRequest(slug=policy_filter)))
        policy = get_response.policy
        if not policy:
            list_use_case = get_list_policies_use_case()
            list_response = asyncio.run(list_use_case.execute(ListPoliciesRequest()))
            click.echo(f"Policy '{policy_filter}' not found.")
            click.echo(f"Available: {', '.join(p.slug for p in list_response.policies)}")
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
        policy_dir = POLICY_COMPLIANCE_DIR / policy.slug.replace("-", "_")
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
