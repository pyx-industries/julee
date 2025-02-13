# Component Version Compatibility

## Overview
Compatible component versions are tracked via git tags. Each release tag includes metadata listing specific component versions that work together.

## Checking Versions

Use bin/versions.sh to:

```bash
# List known-good version combinations
bin/versions.sh --releases

# Show detailed version info
bin/versions.sh --releases --verbose

# Get machine-readable output
bin/versions.sh --releases --format json|csv
```

## Release Tag Format

- `v1.2.3-test1` - Internal testing 
- `v1.2.3-rc1` - Release candidate
- `v1.2.3` - Stable release

Each tag contains component version metadata:
```
Components:
orchestrator: v2.1.0
policy-service: v1.4.2
knowledge-service: v3.0.0
action-service: v1.2.3
```

## Custom Implementations

The component versions in release tags specify interface compatibility requirements. When implementing your own version of a component:

1. Reference the interface specification from the corresponding component version
2. Ensure your implementation conforms to that interface version
3. Your implementation should then be compatible with other components from that release combination

## Validation

Check version compatibility:

```bash
# Validate current versions
bin/versions.sh

# Compare against specific release
bin/versions.sh v1.2.3
```

See docs/RELEASE_PROCESS.md for details on release creation and validation.
