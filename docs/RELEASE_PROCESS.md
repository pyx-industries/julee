# Release Process

This document describes the complete release workflow for the Pyx Julee project, from development through testing to production release.

## Overview

The release process follows these phases:
1. Development and internal testing (alpha/test releases)
2. External validation (beta/RC releases) 
3. Production release

## Development Phase

### Creating Test Releases

During active development, create test releases to validate changes:

```bash
# Create test release
./stage-new-release.sh v2.1.0-test1 \
  orchestrator=v2.1.0 \
  policy-service=v1.4.2 \
  action-service=v2.0.1 \
  knowledge-service=v1.3.0

# Validate
./check-workspace.sh
./prepare-release.sh v2.1.0-test1

# Publish for internal testing
./publish-release.sh v2.1.0-test1
```

Test releases (-test suffix) are for internal validation only.

## Beta/RC Phase

Once features are complete, create Release Candidates:

```bash
# Create RC
./stage-new-release.sh v2.1.0-rc1 \
  orchestrator=v2.1.0 \
  policy-service=v1.4.2 \
  action-service=v2.0.1 \
  knowledge-service=v1.3.0

# Validate
./check-workspace.sh
./prepare-release.sh v2.1.0-rc1

# Publish for external testing
./publish-release.sh v2.1.0-rc1
```

RC releases are feature complete and ready for external validation.

## Production Release

After successful RC testing, create the production release:

```bash
# Create production release
./stage-new-release.sh v2.1.0 \
  orchestrator=v2.1.0 \
  policy-service=v1.4.2 \
  action-service=v2.0.1 \
  knowledge-service=v1.3.0

# Final validation
./check-workspace.sh
./prepare-release.sh v2.1.0

# Publish
./publish-release.sh v2.1.0
```

## Version Management

Query version information at any time:

```bash
# Current workspace state
./versions.sh

# List all releases
./versions.sh --releases

# Show specific release
./versions.sh v2.1.0

# Get machine-readable output
./versions.sh --format json
./versions.sh --format csv

# Sort by date or version
./versions.sh --releases --sort-by date
./versions.sh --releases --sort-by version
```

Version validation and compatibility checking is handled by the common library functions in lib.sh:
- validate_version() - Ensures version numbers follow SemVer
- compare_versions() - Compares version numbers
- check_version_compatibility() - Validates component compatibility

## Hotfix Process

For urgent fixes to production releases:

1. Create hotfix branch from production tag
2. Apply minimal fixes
3. Create and validate release (e.g. v2.1.1)
4. Merge fixes back to main branch

See BRANCHING.md for more details on branching strategy.
