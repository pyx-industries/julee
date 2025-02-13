# stage-new-release.sh

Creates a release branch and updates component versions for a new release.

## Usage

```bash
stage-new-release.sh [release-version] [component-version-pairs...]

# Examples:
stage-new-release.sh v2.1.0                     # Interactive component selection
stage-new-release.sh v2.1.0-rc1                 # Create RC1
stage-new-release.sh v2.1.0 action-service=v2.1.0  # Specify component version
```

## Components

Required components:
- action-service
- knowledge-service
- orchestrator
- policy-service

## Version Format

- Stable: vX.Y.Z
- RC: vX.Y.Z-rcN
- Test: vX.Y.Z-testN

## Dependencies

- bash
- git
- bin/lib.sh

## Issues

### versions/ not populated

There was an idea to maintain files
using a very lightweight text DSL

  <component-name> <SemVer MAJOR.MINOR[.PATCH]>[ <date>]

in files for each state of the SDLC.

In other words, files such as:
- versions/planned.txt for versions that are not yet implemented
- versions/development.txt for versions that are in -test and -rc status
- versions/stable.txt for versions that have stable releases
- versions/depricated.txt for supported versions that will fall out of support (on date)
- versions/unsupported.txt for versions that are not being maintained

and these items would be consuted by the various scripts,
e.g. raising warnings for patches that are not listed in stable,
or warnings if the SDLC implied from the files
doesn't match the tag creation behaviors.

This is partially implemented, but I stopped
because it's complicated and the code is messy enough.

Work can start after creating a test suite,
possibly with bats-core or something like that,
so that it's easier to refactor the bash scripts
without them getting wrapped around the axle.

## Remaining Improvements

### Version Management
Version suggestion heuristic pseudocode:
```psuedocode
suggest_next_versions():
    # Read version state files 
    supported = read_versions("/versions/supported.txt")
    testing = read_versions("/versions/testing.txt")
    planned = read_versions("/versions/planned.txt")
    deprecated = read_versions("/versions/deprecated.txt")

    suggestions = []

    # For versions in testing, suggest:
    for ver in testing:
        if ver matches *-test*:
            suggest next test number
            suggest first RC
        if ver matches *-rc*:
            suggest next RC number
            suggest stable release

    # For versions in planned, suggest:
    for ver in planned:
        if not yet started:
            suggest -test1

    # For supported versions:
    # Only suggest patches if explicitly listed in planned.txt
    for ver in supported:
        if patch_version in planned:
            suggest patch increment

    return suggestions
```

Requirements:
- Version state files in /versions/ directory
- Simple text format: one version per line
- States: supported, testing, planned, deprecated
- Focus on active development lines only
- Natural progression: test -> rc -> stable
- Patches only when explicitly planned

### Error Handling
- [ ] Existing tag handling:
  - Check if tag exists before creating
  - Exit with clear error message if it does

