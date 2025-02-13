#!/bin/bash

# Debug function for consistent output
debug() {
    echo "DEBUG: $*" >&2
}
# debug "Script starting with arguments: $*"

# Enable error handling but preserve debug output
set -uo pipefail
#
#set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "${SCRIPT_DIR}/lib.sh"

select_version() {
    local component="$1"
    local partial_ver="$2"  # Optional partial version like "v2" or "v2.1"
    local versions=($(cd "components/$component" && git tag -l 'v*' | sort -V))
    
    if [ ${#versions[@]} -eq 0 ]; then
        print_error "No valid versions found for $component"
        return 1
    fi

    # If partial version specified, filter versions
    if [ -n "$partial_ver" ]; then
        local filtered=()
        for v in "${versions[@]}"; do
            if [[ "$v" == "$partial_ver"* ]]; then
                filtered+=("$v")
            fi
        done
        versions=("${filtered[@]}")
        
        if [ ${#versions[@]} -eq 0 ]; then
            print_error "No versions match $partial_ver"
            return 1
        fi
    fi

    # Extract unique MAJOR versions
    local -A majors=()
    for v in "${versions[@]}"; do
        local major=$(echo "$v" | cut -d. -f1)
        majors["$major"]=1
    done
    
    # Select MAJOR if not specified in partial_ver
    if [[ ! "$partial_ver" =~ ^v[0-9]+(\.|$) ]]; then
        if [ ${#majors[@]} -gt 1 ]; then
            echo "Available major versions:"
            local i=1
            local major_list=()
            for v in "${!majors[@]}"; do
                echo "  $i. $v"
                major_list+=("$v")
                ((i++))
            done
            read -p "Select major version [${#major_list[@]}]: " choice
            choice=${choice:-${#major_list[@]}}
            
            if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#major_list[@]} ]; then
                print_error "Invalid selection"
                return 1
            fi
            selected_major="${major_list[$((choice-1))]}"
        else
            selected_major="${!majors[@]}"
        fi
    else
        selected_major=$(echo "$partial_ver" | cut -d. -f1)
    fi

    # Filter to selected MAJOR and get unique MINOR versions
    local filtered=()
    local -A minors=()
    for v in "${versions[@]}"; do
        if [[ "$v" == "$selected_major"* ]]; then
            filtered+=("$v")
            local minor=$(echo "$v" | cut -d. -f2)
            minors["$minor"]=1
        fi
    done
    versions=("${filtered[@]}")

    # Select MINOR if not specified in partial_ver
    if [[ ! "$partial_ver" =~ ^v[0-9]+\.[0-9]+(\.|$) ]]; then
        if [ ${#minors[@]} -gt 1 ]; then
            echo "Available minor versions for $selected_major:"
            local i=1
            local minor_list=()
            for v in "${!minors[@]}"; do
                echo "  $i. $v"
                minor_list+=("$v")
                ((i++))
            done
            read -p "Select minor version [${#minor_list[@]}]: " choice
            choice=${choice:-${#minor_list[@]}}
            
            if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#minor_list[@]} ]; then
                print_error "Invalid selection"
                return 1
            fi
            selected_minor="${minor_list[$((choice-1))]}"
        else
            selected_minor="${!minors[@]}"
        fi
    else
        selected_minor=$(echo "$partial_ver" | cut -d. -f2)
    fi

    # Filter to selected MINOR and show remaining versions
    filtered=()
    for v in "${versions[@]}"; do
        if [[ "$v" == "$selected_major.$selected_minor"* ]]; then
            filtered+=("$v")
        fi
    done
    versions=("${filtered[@]}")

    # Final version selection
    echo "Available versions for $selected_major.$selected_minor:"
    for i in "${!versions[@]}"; do
        echo "  $((i+1)). ${versions[$i]}"
    done
    
    latest=$((${#versions[@]}))
    read -p "Select version [${latest}]: " choice
    choice=${choice:-$latest}
    
    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#versions[@]} ]; then
        print_error "Invalid selection"
        return 1
    fi

    selected_version="${versions[$((choice-1))]}"
    echo "$selected_version"
    return 0
}

# Usage message
usage() {
    echo "Stage a new release by creating a release branch and setting component versions"
    echo
    echo "Usage: $0 [release-version] [component-version-pairs...]"
    echo
    echo "Release Version Format:"
    echo "  vX.Y.Z         Stable release (e.g. v2.1.0)"
    echo "  vX.Y.Z-rcN     BETA/Release Candidate (e.g. v2.1.0-rc1)"
    echo "  vX.Y.Z-testN   ALPHA/Test release (e.g. v2.1.0-test1)"
    echo
    echo "Components:"
    echo "  action-service"
    echo "  knowledge-service"
    echo "  orchestrator"
    echo "  policy-service"
    echo
    echo "Examples:"
    echo "  $0 v2.1.0                                    # Create stable release v2.1.0"
    echo "  $0 v2.1.0-rc1                               # Create release candidate 1"
    echo "  $0 v2.1.0-test1                             # Create test release 1"
    echo "  $0 v2.1.0 action-service=v2.1.0             # With specific component version"
    echo
    echo "If no version is provided, the script will guide you through version selection."
    exit 1
}

# Show usage for help flags or if no arguments and not in a terminal
if [ "$1" = "--help" ] || [ "$1" = "-h" ] || ([ $# -eq 0 ] && [ ! -t 0 ]); then
    usage
fi

get_release_version() {
    local base_version="${1:-}"
    
    # Handle no arguments case
    if [ -z "$base_version" ]; then
        echo "Please enter the base version number:"
        echo "Format: vX.Y.Z (where X, Y, and Z are numbers)"
        echo
        echo "Examples:"
        echo "  v2.1.0  - for a new major/minor release"
        echo "  v2.1.1  - for a patch release"
        echo
        echo "Type 'q' to quit"
        echo
        read -p "> " base_version
        
        if [ "$base_version" = "q" ]; then
            exit 0
        elif [ -z "$base_version" ]; then
            print_error "No version provided"
            return 1
        fi
    fi
    
    # Validate base version format
    if [[ ! $base_version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Base version must be in format vX.Y.Z"
        return 1
    fi
    
    # If full version specified on command line, validate and return it
    if [ $# -gt 1 ]; then
        if ! validate_version "$1"; then
            print_error "Invalid version format: $1"
            return 1
        fi
        echo "$1"
        return 0
    fi
    
    # Interactive menu for release type if no full version specified
    local final_version
    if [ $# -eq 1 ]; then  # Only base version provided
        printf "Select release type:\n"
        printf "1. Stable Release (no suffix)\n"
        printf "2. Release Candidate (-rcN)\n"
        printf "3. Test Release (-testN)\n"
        read -p "Choice [1]: " choice
        choice=${choice:-1}
        
        case $choice in
            1)
                final_version="$base_version"
                ;;
            2)
                local next_rc=$(get_next_version_number "$base_version" "rc")
                final_version="${base_version}-rc${next_rc}"
                ;;
            3)
                local next_test=$(get_next_version_number "$base_version" "test")
                final_version="${base_version}-test${next_test}"
                ;;
            *)
                print_error "Invalid choice"
                return 1
                ;;
        esac
    else
        # Full version already provided
        final_version="$base_version"
    fi
    printf "%s\n" "$final_version"
}

# Get release version
if [ $# -ge 1 ]; then
    VERSION_ARG="$1"
    shift
    # debug "Processing provided version: $VERSION_ARG"
    
    # Check if it's a partial version (vX.Y)
    if [[ "$VERSION_ARG" =~ ^v[0-9]+\.[0-9]+$ ]]; then
        echo "Completing partial version $VERSION_ARG"
        echo "Available patch versions:"
        git tag -l "${VERSION_ARG}.*" | sort -V | sed 's/^/  /'
        echo
        read -p "Enter patch number: " patch_num
        if [[ ! "$patch_num" =~ ^[0-9]+$ ]]; then
            print_error "Invalid patch number"
            exit 1
        fi
        RELEASE_VERSION="${VERSION_ARG}.${patch_num}"
        # debug "Completed version: $RELEASE_VERSION"
    else
        RELEASE_VERSION="$VERSION_ARG"
    fi
    
    if ! validate_version "$RELEASE_VERSION"; then
        # debug "Release version validation failed"
        print_error "Release version must be in format vX.Y.Z[-rcN|-testN]"
        exit 1
    fi
else
    # debug "No version provided, entering interactive mode"
    RELEASE_VERSION=$(get_release_version) || exit 1
fi
# debug "Release version selected: $RELEASE_VERSION"

# Define required components
REQUIRED_COMPONENTS=("action-service" "knowledge-service" "orchestrator" "policy-service")

# Check which required components are missing versions
declare -A specified_components
for pair in "$@"; do
    component="${pair%%=*}"
    specified_components["$component"]=1
done

missing_components=()
invalid_components=()
for pair in "$@"; do
    component="${pair%%=*}"
    if [[ ! " ${REQUIRED_COMPONENTS[@]} " =~ " ${component} " ]]; then
        invalid_components+=("$component")
    fi
done

for comp in "${REQUIRED_COMPONENTS[@]}"; do
    if [[ -z "${specified_components[$comp]:-}" ]]; then
        missing_components+=("$comp")
    fi
done

# Error if any invalid components specified
if [ ${#invalid_components[@]} -gt 0 ]; then
    print_error "Invalid components specified: ${invalid_components[*]}"
    print_error "Valid components are: ${REQUIRED_COMPONENTS[*]}"
    exit 1
fi

# If any required components are missing versions, offer interactive selection
if [ ${#missing_components[@]} -gt 0 ]; then
    echo "Missing versions for components: ${missing_components[*]}"
    echo "Enter interactive selection mode?"
    read -p "Continue? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        # Build up component version pairs
        declare -a selections=()
        
        # For each missing component
        for component in "${missing_components[@]}"; do
            echo
            echo "Selecting version for $component:"
            
            # Get available versions
            versions=($(cd "components/$component" && git tag -l 'v*' | sort -V))
            
            if [ ${#versions[@]} -eq 0 ]; then
                print_error "No valid versions found for $component"
                exit 1
            fi

            # Allow partial version specification first
            read -p "Enter partial version (e.g. v2 or v2.1) or press enter for available versions: " partial
            
            if [ -n "$partial" ]; then
                # Filter versions based on partial
                filtered=()
                for v in "${versions[@]}"; do
                    if [[ "$v" == "$partial"* ]]; then
                        filtered+=("$v")
                    fi
                done
                versions=("${filtered[@]}")
            fi
            
            # Show available versions (either all or filtered)
            echo "Available versions:"
            for i in "${!versions[@]}"; do
                echo "   [$((i+1))] $component ${versions[$i]}"
            done
            echo
            
            selected_version=$(select_version "$component" "$partial" | tail -n1)
            if [ $? -ne 0 ]; then
                exit 1
            fi
            if [ -z "$selected_version" ]; then
                print_error "No version selected for $component"
                exit 1
            fi
            # debug "Selected version for $component: $selected_version"
            selections+=("$component=$selected_version")
        done
        
        # Add selections to command line arguments
        set -- "$RELEASE_VERSION" "${selections[@]}"
    fi
fi

# Validate current state
if ! check_workspace_state; then
    print_error "Working directory not clean"
    exit 1
fi

# Create and switch to release branch
BRANCH="release/${RELEASE_VERSION}"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    print_error "Branch $BRANCH already exists"
    print_error "Delete the existing branch or choose a different version"
    exit 1
fi
git checkout -b "$BRANCH"

# Skip the release version argument
shift

# Debug component version pairs
# debug "Validating component versions: $*"

# Validate component versions exist
for pair in "$@"; do
    component="${pair%%=*}"
    version="${pair#*=}"
    
    # debug "Validating $component version: $version"
    if ! (cd "components/$component" && git rev-parse --verify "$version" >/dev/null 2>&1); then
        # debug "Failed to verify $version in components/$component"
        print_error "Version $version does not exist for component $component"
        git checkout -
        git branch -D "$BRANCH"
        exit 1
    fi
done

# Update each submodule
for pair in "$@"; do
    component="${pair%%=*}"
    version="${pair#*=}"

    echo "Updating $component to $version..."
    (cd "components/$component" && \
     git fetch && \
     git checkout "$version")

    git add "components/$component"
done

# Validate final state
if ! validate_components; then
    print_error "Component validation failed"
    git checkout -
    git branch -D "$BRANCH"
    exit 1
fi

# Check versions against lifecycle files
for pair in "$@"; do
    component="${pair%%=*}"
    version="${pair#*=}"
    found=0
    
    # Check each version file
    for state in supported testing deprecated planned; do
        if [ -f "/versions/${state}.txt" ] && grep -q "^${component} ${version}" "/versions/${state}.txt"; then
            found=1
            if [ "$state" = "deprecated" ]; then
                # Check EOL date if present
                eol_date=$(grep "^${component} ${version}" "/versions/${state}.txt" | awk '{print $3}')
                if [ -n "$eol_date" ] && [ "$(date +%Y-%m-%d)" \> "$eol_date" ]; then
                    echo "WARNING: $component $version is past EOL date $eol_date"
                fi
            fi
            break
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo
        echo "Version $version of $component is not listed in any version state file"
        echo "Select state to add it to:"
        echo "[1] supported"
        echo "[2] testing"
        echo "[3] deprecated"
        echo "[4] planned"
        echo "[5] do nothing (leave it undocumented)"
        read -p "Choice [5]: " choice
        choice=${choice:-5}
        
        case $choice in
            1|2|3|4)
                states=(supported testing deprecated planned)
                state=${states[$((choice-1))]}
                mkdir -p /versions
                echo "$component $version" >> "/versions/${state}.txt"
                echo "Added to ${state}.txt"
                ;;
            5)
                echo "Leaving version undocumented"
                ;;
            *)
                echo "Invalid choice, leaving version undocumented"
                ;;
        esac
    fi
done

# Generate tag message
echo "Generating tag message..."

# Get previous version for changes
PREV_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$PREV_VERSION" ]; then
    CHANGES=$(git log --pretty=format:"- %s" "${PREV_VERSION}..HEAD")
else
    CHANGES=$(git log --pretty=format:"- %s")
fi

# Create tag message with required sections
TAG_MSG=$(cat << EOF
Release Date: $(date +%Y-%m-%d)

Component Versions:
$(printf '%s\n' "$@" | sed 's/=/ /g' | sed 's/^/- /')

Changes:
${CHANGES}
EOF
)

# Prompt for additional notes
echo
echo "Current tag message:"
echo "-------------------"
echo "$TAG_MSG"
echo "-------------------"
echo
read -p "Would you like to add additional notes? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Enter additional notes (end with Ctrl+D):"
    ADDITIONAL_NOTES=$(cat)
    if [ -n "$ADDITIONAL_NOTES" ]; then
        TAG_MSG+=$'\n\nAdditional Notes:\n'"$ADDITIONAL_NOTES"
    fi
fi

# Commit the changes
git commit -m "build: Stage $RELEASE_VERSION

Component versions:
$(printf '%s\n' "$@" | sed 's/=/: /g')"

# Store tag message temporarily
echo "$TAG_MSG" > ".git/TAG_MSG.tmp"

# Show release summary and get confirmation
echo
echo "Release Summary for $RELEASE_VERSION"
echo "=================================="
echo
echo "Component Versions:"
for pair in "$@"; do
    component="${pair%%=*}"
    version="${pair#*=}"
    echo "  $component: $version"
done
echo
echo "Changes since last release:"
echo "$CHANGES"
echo
echo "Release Notes Preview:"
echo "-------------------"
echo "$TAG_MSG"
echo "-------------------"
echo
while true; do
    echo "Options:"
    echo "1. View release summary"
    echo "2. Proceed with release"
    echo "3. Edit release notes"
    echo "4. Modify component versions"
    echo "5. Abort (delete branch)"
    echo
    read -p "Select action [1]: " action
    action=${action:-1}

    case $action in
        1)
            echo
            echo "Release Summary:"
            echo "==============="
            cat ".git/TAG_MSG.tmp"
            echo
            echo "===================="
            echo
            ;;
        2)
            echo "Proceeding with release..."
            echo
            echo "NOTE: Integration tests not yet implemented - proceed with caution"
            echo
            echo "Review the changes and press Enter to create the release tag, or Ctrl+C to abort"
            read
            
            # Create the tag
            git tag -F .git/TAG_MSG.tmp "$RELEASE_VERSION"
            rm -f .git/TAG_MSG.tmp
            
            echo "Release $RELEASE_VERSION tagged successfully"
            echo
            
            # Get list of non-release branches
            mapfile -t branches < <(git for-each-ref --format='%(refname:short)' refs/heads/ | grep -v "^release/")
            
            if [ ${#branches[@]} -gt 1 ]; then
                echo "Select branch to return to:"
                select branch in "${branches[@]}"; do
                    if [ -n "$branch" ]; then
                        break
                    fi
                    echo "Invalid selection"
                done
            else
                branch="master"
            fi
            
            echo "Switching to $branch branch..."
            git checkout "$branch"
            
            echo "Delete release branch? [Y/n]"
            read -r response
            response=${response:-y}
            if [[ $response =~ ^[Yy] ]]; then
                git branch -D "$BRANCH"
                echo "Release branch deleted"
            else
                echo "Release branch preserved"
            fi
            
            break
            ;;
        3)
            EDITOR=emacs
            $EDITOR ".git/TAG_MSG.tmp"
            # Regenerate tag message with edited content
            TAG_MSG=$(cat ".git/TAG_MSG.tmp")
            # Continue showing the menu
            ;;
        4)
            echo "Branch $BRANCH created."
            echo "Edit component versions and run:"
            echo "  $0 $RELEASE_VERSION $*"
            break
            ;;
        5)
            echo "Aborting release..."
            git checkout -
            git branch -D "$BRANCH"
            rm -f ".git/TAG_MSG.tmp"
            exit 1
            ;;
        *)
            echo "Invalid selection"
            ;;
    esac
done
