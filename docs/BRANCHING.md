# Branching Strategy

This document describes how to use branches in the Pyx Julee project.
It applies to the project repository itself,
and also to all the component/ submodule repositories

We uses a branching model centered around releases,
with each release developed in a release branch and marked with a tag.

## Branch Types

### Master Branch
The repository maintains a master development branch,
which is generally the focus of feature development efforts.
We call this master (not "main") because that's what it's called.

### Feature Branches
New feature branches are usually forked from the master branch,
then merged back into master branch when the work seems to be "done".
From there, -test releases of new features (MAJOR or MINOR releases)
or PATCH releases are created using SemVer of the feature set/patch level,
while the HEAD of the feature branch follows feature development.

The dicipline to create short-lived, frequently-released,
narrowly-scoped features is encouraged. 

### Maintenance Branches
Maintainance branches may be maintained for semantic MAJOR.MINOR versions
(i.e. feature sets). Hotfixes, backporting patches, etc occur here.

Maintenance releases are tagged from these branches, rather
than the main line of development (in the master branch).

### Release Branches

These are created and ultimately destroyed by the release management process.

- Named pattern: `release/vX.Y.Z`
- Created during release preparation
- Used to lock component versions for a specific release
- Created via `stage-new-release.sh`
- Contains specific tagged versions of all submodules,
- Also contains current-state documentation, scripts, etc.

## Tags

### Release Tags
- Named pattern: `vX.Y.Z`
- Created on release branches
- Contains metadata in tag message:
  - Date the tag was created
  - List of component versions
  - Release notes
- Created via `tag-release.sh`
- Published via `publish-release.sh`

Tag messages follow a proscribed format (per `tag-release.sh`)

There is work in progress to develop "component compatibility information"
in `versions/`, see notes in bin/*.md for information about WIP.

## Version Numbering

### Semantic Versioning
All version numbers follow SemVer 2.0 (https://semver.org/):
- Format: vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
- Example: v2.1.0, v2.1.1-rc1, v2.0.0-test3

### Pre-release Tags
For internal (ALPHA) Testing: Use `-test<n>` suffix
  - Example: v2.1.0-test1, v2.1.0-test2
  - May have breaking changes
  - Not for production use

For Release Candidate (BETA) Testing: Use `-rc<n>` suffix
  - Example: v2.1.0-rc1, v2.1.0-rc2
  - For external validation testing
  - Feature complete for the target release
  - May have bugs but no planned breaking changes

### Production Releases
- No suffix: v2.1.0
- Considered stable and production-ready
- Must have gone through at least one RC

## Component Integration

### Submodules
- Components are managed as git submodules
- Each component has its own repository
- Component versions are specified by their tags
- Component state is validated during release preparation

### Version Management
- Component versions are tracked in release tags
- Version compatibility is checked during release preparation
- Version state can be queried via `versions.sh`

## Release Process Flow

Note: For pre-releases (alpha/beta), follow the same process but use appropriate version suffixes:
- Alpha: `v2.1.0-test1`
- Beta/RC: `v2.1.0-rc1`

The same tooling and process applies, but these releases are marked as non-production in announcements.

1. Create Release Branch
   ```bash
   ./stage-new-release.sh v2.1.0 component-a=v2.1.0 component-b=v1.4.2
   ```

2. Validate Release
   ```bash
   ./check-workspace.sh
   # TODO ./run-integration-tests.sh
   ```

3. Tag Release (WIP)
   ```bash
   ./prepare-release.sh v2.1.0  # specify appropriate version
   ```

4. Publish Release (TODO)
   ```bash
   ./publish-release.sh v2.1.0
   ```
   Note: the branch is deleted after tagging succeeds. 

5. Announce Release (TODO)
   ```bash
   ./announce-release.sh v2.1.0
   ```

## Version Control Operations

### Branch Creation
- Release branches are created from master branch
- Component versions are locked when branch is created
- Version compatibility checked via lib.sh functions

### Tag Creation
- Tags are created on release branches
- Tags include full component version metadata
- Tags are annotated with release notes
- Tag messages generated via lib.sh create_tag_message()

### Publishing
- Both release branches and tags are pushed to origin
- Release notes generated via lib.sh generate_release_notes()
- Multiple output formats supported (table, CSV, JSON)

## Workspace Management

The workspace state can be queried and switched using:
```bash
# Show current versions
./versions.sh

# Show specific release
./versions.sh v2.1.0

# Switch to release
./switch-release.sh v2.1.0
```

This ensures all components are at their correct versions for the specified release.
