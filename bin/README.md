# Release Management Scripts

This directory contains scripts that implement
release management processes for the Pyx Julee project.

Maintain these scripts rather than detailed documentation,
the scripts are the documentation.

These scripts currently seem to work:

- `versions.sh` - Unified interface for querying version information
  ```bash
  # Show current workspace state
  ./versions.sh
  
  # Show specific release
  ./versions.sh v1.2.3
  
  # List all releases
  ./versions.sh --releases
  
  # Show detailed history
  ./versions.sh --releases --verbose
  ```

- `check-workspace.sh` - Validates workspace is in known good state
  ```bash
  # Basic check
  ./check-workspace.sh
  
  # Detailed output
  ./check-workspace.sh --verbose
  ```

Ideas about improvements and additions (maybe):
- Release announcement automation
- CI/CD integration
- Component upgrade planning
- Dependency analysis tools
- Version compatibility matrices


## Workflow

- `stage-new-release.sh` - Create release branch with locked component versions
- `prepare-release.sh` - Validate and prepare release (includes version checks)
- `publish-release.sh` - Tag and publish release
- `switch-release.sh` - Switch workspace to specific release version

### Pre-release Handling
The same tools support pre-release versions:
- Alpha/test releases: Use `-test<n>` suffix (e.g. v2.1.0-test1)
- Beta/RC releases: Use `-rc<n>` suffix (e.g. v2.1.0-rc1)

Example:

```bash
# 1. Create release branch
./stage-new-release.sh v2.1.0-test1 component-a=v2.1.0 component-b=v1.4.2

# 2. Validate and prepare release
./check-workspace.sh
./prepare-release.sh v2.1.0-test1

# 3. Publish release
./publish-release.sh v2.1.0-test1

# Later: Create RC
./stage-new-release.sh v2.1.0-rc1 component-a=v2.1.0 component-b=v1.4.2
# (repeat steps 2-3)

# Finally: Production release
./stage-new-release.sh v2.1.0 component-a=v2.1.0 component-b=v1.4.2
# (repeat steps 2-3)
```

Or, at any time check the workspace/project state:

```bash
# Validate current state
./check-workspace.sh

# Review versions
./versions.sh

# Get machine-readable output
./versions.sh --format json
```

