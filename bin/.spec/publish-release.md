# publish-release.sh

Create a file in the current directory (bin/) called `publish-release.sh`, which is a bash script that publishes a release by pushing the release branch, tag, and generating release notes.

## Purpose

This script handles the publication of a release after it has been tagged, ensuring all changes are pushed to the remote repository and proper release notes are generated.

## Implementation

```bash
#!/bin/bash
set -euo pipefail

# Usage message
usage() {
    echo "Usage: $0 <release-version>"
    echo "Publishes a release by pushing branch and tag"
    echo
    echo "The release must already be tagged with tag-release.sh"
    exit 1
}

[ $# -ne 1 ] && usage

RELEASE_VERSION="$1"

# Validate release version format
if ! echo "$RELEASE_VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "Error: Release version must be in format vX.Y.Z"
    exit 1
fi

# Verify tag exists
if ! git rev-parse "$RELEASE_VERSION" >/dev/null 2>&1; then
    echo "Error: Release tag $RELEASE_VERSION not found"
    exit 1
fi

# Verify we're on the release branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
EXPECTED_BRANCH="release/${RELEASE_VERSION}"
if [[ "$CURRENT_BRANCH" != "$EXPECTED_BRANCH" ]]; then
    echo "Error: Must be on $EXPECTED_BRANCH branch"
    exit 1
fi

# Generate changelog from commits since last release
LAST_RELEASE=$(git describe --tags --abbrev=0 "$RELEASE_VERSION"^ 2>/dev/null || echo "")
if [ -n "$LAST_RELEASE" ]; then
    CHANGES=$(git log --pretty=format:"- %s" "$LAST_RELEASE..$RELEASE_VERSION")
else
    CHANGES=$(git log --pretty=format:"- %s" "$RELEASE_VERSION")
fi

# Create release notes file
NOTES_FILE="releases/notes-${RELEASE_VERSION}.md"
mkdir -p releases
{
    echo "# Release ${RELEASE_VERSION}"
    echo
    echo "## Component Versions"
    echo
    git tag -l --format='%(contents)' "$RELEASE_VERSION" | sed -n '/Components:/,$p'
    echo
    echo "## Changes"
    echo
    echo "$CHANGES"
} > "$NOTES_FILE"

# Push branch and tag
echo "Pushing release branch..."
git push origin "$CURRENT_BRANCH"

echo "Pushing release tag..."
git push origin "$RELEASE_VERSION"

echo "Release notes written to $NOTES_FILE"
echo
echo "Next steps:"
echo "1. Review release notes"
echo "2. Run announce-release.sh $RELEASE_VERSION"
```

## Usage

```bash
./publish-release.sh v2.1.0
```

## Exit Codes

- 0: Release published successfully
- 1: Error occurred (invalid input, failed checks, etc.)

## Dependencies

Requires:
- git
- releases/ directory for storing release notes

## Notes

- Pushes release branch and tag to origin
- Generates changelog from commits
- Creates structured release notes
- Provides clear next steps
