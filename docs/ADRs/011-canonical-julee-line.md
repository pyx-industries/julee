# ADR 011: Master Is the Canonical Julee Line

## Status

Accepted

## Date

2026-09-21

## Context

After v0.1.6 (2025-12-18), julee development split into two lines:

- `master`, which carries the PyPI releases (v0.1.7 onwards) and the ADRs 002–010 as enforced by doctrine tests in CI.
- `docs_architecture_domain`, a re-architecture of about 230 commits. It reorganised the package into flat bounded contexts (`core`, `hcd`, `c4`, `supply_chain`, `contrib/{ceap,polling,untp}`), added a top-level `apps` package (the `julee-admin` CLI, the Sphinx extensions and MCP servers), and grew a larger doctrine and policy suite.

The branch was never merged. Master re-implemented a subset of its ideas instead, and the two lines share no patches. Some names now mean different things on each line:

- `julee.core.entities.entity.Entity` is an introspection model on the branch, and the frozen base class for domain entities on master.
- `Acknowledgement.roger()` means "won't comply" on the branch, and "no commitment" on master, which adds `unable()` for "won't comply".
- `generic_crud` offers a runtime `generate()` on the branch. On master it offers base classes and a build-time generator (ADR 008).
- `RESERVED_WORDS` differ.
- The Temporal workflow proxy retries once on the branch and four times on master.

Downstream solutions (pyx-labs, rba-pyx-labs) depend on the branch, not on a release. So "upgrading julee" is a migration rather than a version bump, and it isn't clear which line new work should target.

## Decision

1. `master` is the canonical julee line. New framework work targets master, and releases are cut only from master.

2. The `docs_architecture_domain` line is frozen at `b2af257` and archived as the tag `archive/docs_architecture_domain`. The branch receives no further commits. The tag keeps the commit reachable for solutions that pin it, even if the branch is later removed.

3. Features that exist only on the archived line are either ported to master or explicitly dropped, one decision per feature. Each port is re-implemented against master's ADRs and doctrine rather than cherry-picked. Porting also separates framework concerns, which every julee solution needs, from domain-specific concerns, which should be pluggable and may not belong in the framework at all. How to draw that line is left to a later ADR.

4. When a ported feature keeps an old name but changes its meaning (as `Acknowledgement` did), the release notes call it out as a breaking change.

## Consequences

- Solutions that currently depend on the branch should pin the archive tag or its commit, not the branch name, until they migrate to a master release.
- The archived line remains a reference for porting, not a place to fix bugs. Fixes that solutions need land on master.
- Until the port-or-drop decisions are made, solutions cannot move to master without losing functionality they use today (for example `contrib.untp`, the HCD Sphinx directives and `julee-admin`). Making those decisions is the main follow-up to this ADR.
- ADRs 001–010 are read as statements about master. Where one describes behaviour that exists only on the archived line (for example ADR 007's semantic relations), it describes intended rather than current behaviour until that feature is ported.
