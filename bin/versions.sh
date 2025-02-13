#!/bin/bash
set -euo pipefail

# versions.sh - Unified interface for querying version information
# 
# This script provides a single source of truth for version information across
# the project, combining functionality for:
# - Showing current workspace versions
# - Listing available releases
# - Displaying version history
#
# Output Formats:
# - table (default): Human-readable formatted output
# - csv: Machine-readable comma-separated values
# - json: Machine-readable JSON format
#
# Exit Codes:
# - 0: Success
# - 1: Usage error 
# - 2: Git repository error
# - 3: Invalid release specified
#
# Dependencies:
# - git
# - bash
# - Standard Unix tools (sed, awk, etc.)
#
# See docs/COMPATABLE_VERSIONS.md for version compatibility details

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${SCRIPT_DIR}/lib.sh"

# Usage message
usage() {
    echo "Usage: $0 [<version>] [options]"
    echo "Shows version information for Julee components"
    echo
    echo "Options:"
    echo "  -r, --releases     List available releases"
    echo "  -v, --verbose      Show detailed information"
    echo "  -f, --format FORMAT Output format (table|csv|json)"
    echo "  --sort-by FIELD    Sort releases by 'date' or 'version'"
    echo
    echo "Examples:"
    echo "  $0                 # Show current versions"
    echo "  $0 v1.2.3         # Show specific release"
    echo "  $0 --releases     # List all releases"
    echo "  $0 --format json  # JSON output"
    exit 1
}

# Configuration
FORMAT="table"        # Output format (table|csv|json)
SHOW_RELEASES=0      # List releases instead of current versions
VERBOSE=0           # Show detailed information
SORT_BY="date"      # Sort releases by date or version
TARGET_VERSION=""   # Specific version to show

# Parse arguments

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--releases)
            SHOW_RELEASES=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        --sort-by)
            SORT_BY="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Error: Unknown option $1"
            usage
            ;;
        *)
            if [ -z "$TARGET_VERSION" ]; then
                TARGET_VERSION="$1"
            else
                echo "Error: Multiple versions specified"
                usage
            fi
            shift
            ;;
    esac
done

# Validate format
case "$FORMAT" in
    table|csv|json) ;;
    *)
        echo "Error: Invalid format $FORMAT"
        exit 1
        ;;
esac

# Validate sort field
case "$SORT_BY" in
    date|version) ;;
    *)
        echo "Error: Invalid sort field $SORT_BY"
        exit 1
        ;;
esac

# Enhanced version validation to handle pre-release and build metadata
validate_semver() {
    local version=$1
    if ! [[ $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$ ]]; then
        return 1
    fi
    return 0
}

# Standardized error handling
handle_error() {
    local code=$1
    local message=$2
    echo "Error: $message" >&2
    exit "$code"
}

# Version compatibility checking using tag metadata
check_version_compatibility() {
    local component=$1
    local version=$2
    local tag=$3

    # Get component versions from tag metadata
    local expected_version=$(git tag -l --format='%(contents)' "$tag" | 
        sed -n '/Components:/,$p' | grep "^${component}:" | cut -d: -f2 | tr -d ' ')

    if [ -z "$expected_version" ]; then
        return 0  # Component not specified in tag
    fi

    if [ "$version" != "$expected_version" ]; then
        return 1
    fi
    return 0
}

# show_current_versions(): Display version information for current workspace
# 
# Shows:
# - Master Julee version
# - Component versions and their expected versions
# - Workspace status (CLEAN/DIRTY)
# - Any version mismatches or local modifications
show_current_versions() {
    # Get Julee version
    JULEE_VERSION=$(git describe --tags 2>/dev/null || echo "unknown")
    if [ -n "$(git status --porcelain)" ]; then
        JULEE_VERSION="${JULEE_VERSION}-dirty"
    fi

    # Get latest release tag
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    # Collect component information
    declare -A COMPONENTS
    ISSUES=()
    
    for dir in components/*; do
        if [ ! -d "$dir" ]; then
            continue
        fi

        component=$(basename "$dir")
        current=$(get_component_version "$dir")
        expected=$(get_expected_version "$LATEST_TAG" "$component")
        
        if [ "$current" != "$expected" ] && [ "$expected" != "none" ]; then
            if [[ $current =~ ^v[0-9] ]]; then
                ISSUES+=("Version mismatch in ${component}")
            fi
        fi
        
        if [[ "$current" =~ -modified$ ]]; then
            ISSUES+=("Local modifications in ${component}")
        fi
        
        if is_detached_head "components/$component"; then
            ISSUES+=("Detached HEAD in ${component}")
        fi

        COMPONENTS[$component]="$current|$expected"
    done

    # Determine status
    if [ ${#ISSUES[@]} -gt 0 ]; then
        STATUS="DIRTY"
    else
        STATUS="CLEAN"
    fi

    # Output based on format
    case "$FORMAT" in
        table)
            format_version_table "$JULEE_VERSION" COMPONENTS ISSUES "$STATUS"
            ;;
        csv)
            format_version_csv COMPONENTS
            ;;
        json)
            format_version_json "$JULEE_VERSION" COMPONENTS ISSUES "$STATUS"
            ;;
    esac
}

# show_releases(): Display information about available releases
#
# Shows:
# - List of all release versions
# - Release dates
# - Component versions (in verbose mode)
# - Release notes (in verbose mode)
show_releases() {
    # Get all tags
    local tags
    if [ "$SORT_BY" = "date" ]; then
        tags=$(git tag -l 'v*' --sort=-creatordate)
    else
        tags=$(git tag -l 'v*' --sort=-v:refname)
    fi
    
    # Get latest release tag
    local latest_tag=$(echo "$tags" | head -n1)

    if [ -z "$tags" ]; then
        echo "No releases found"
        exit 0
    fi

    case "$FORMAT" in
        table)
            if [ $VERBOSE -eq 1 ]; then
                for tag in $tags; do
                    date=$(git log -1 --format=%ai "$tag" | cut -d' ' -f1)
                    latest_marker=""
                    [ "$tag" = "$latest_tag" ] && latest_marker=" - Latest"
                    echo "Julee $tag ($date)$latest_marker"
                    echo "Components:"
                    git tag -l --format='%(contents)' "$tag" | \
                        sed -n '/Components:/,$p' | tail -n +2 | sed 's/^/  /'
                    echo "Changes:"
                    git tag -l --format='%(contents)' "$tag" | \
                        sed -n '/Changes:/,/Components:/p' | sed '/Components:/d' | \
                        grep -v '^Changes:' | sed 's/^/  - /'
                    echo
                done
            else
                echo "Julee releases:"
                for tag in $tags; do
                    date=$(git log -1 --format=%ai "$tag" | cut -d' ' -f1)
                    echo "$tag ($date)"
                done
            fi
            ;;
        csv)
            echo "version,date,message"
            for tag in $tags; do
                date=$(git log -1 --format=%ai "$tag" | cut -d' ' -f1)
                message=$(git tag -l --format='%(contents)' "$tag" | tr '\n' ' ' | sed 's/,/ /g')
                echo "$tag,$date,\"$message\""
            done
            ;;
        json)
            echo "{"
            echo "  \"releases\": ["
            first=1
            for tag in $tags; do
                [ $first -eq 1 ] || echo ","
                date=$(git log -1 --format=%ai "$tag" | cut -d' ' -f1)
                echo "    {"
                echo "      \"version\": \"$tag\","
                echo "      \"date\": \"$date\","
                if [ $VERBOSE -eq 1 ]; then
                    echo "      \"message\": \"$(git tag -l --format='%(contents)' "$tag" | tr '\n' ' ')\","
                fi
                echo "      \"components\": {"
                first_comp=1
                while IFS=': ' read -r component version; do
                    [ -z "$component" ] && continue
                    [ $first_comp -eq 1 ] || echo ","
                    echo "        \"$component\": \"$version\""
                    first_comp=0
                done < <(git tag -l --format='%(contents)' "$tag" | sed -n '/Components:/,$p' | tail -n +2)
                echo "      }"
                echo -n "    }"
                first=0
            done
            echo
            echo "  ]"
            echo "}"
            ;;
    esac
}

# Main logic
if [ -n "$TARGET_VERSION" ]; then
    if ! git rev-parse "$TARGET_VERSION" >/dev/null 2>&1; then
        echo "Error: Invalid version $TARGET_VERSION"
        exit 1
    fi
    git checkout -q "$TARGET_VERSION"
    show_current_versions
    git checkout -q - >/dev/null
elif [ $SHOW_RELEASES -eq 1 ]; then
    show_releases
else
    show_current_versions
fi
