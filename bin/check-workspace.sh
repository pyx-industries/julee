#!/bin/bash
#
# check-workspace.sh - Validates the workspace is in a known good state

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "${SCRIPT_DIR}/lib.sh"
#
# This script performs comprehensive validation of the workspace by checking:
# - Git repository status (uncommitted/untracked changes)
# - Submodule states and configurations
# - Required directory structure
# - Required tool availability
#
# The script implements these checks in order:
#
# 1. Directory Structure Validation
#    - Verifies all expected directories are present (components/, deployment/, bin/)
#    - Ensures basic project structure matches conventions
#
# 2. Tool Availability Check
#    - Confirms required tools are available (git, bash, sed, awk)
#    - Prevents issues before they occur
#
# 3. Main Repository Status
#    - Checks for uncommitted changes
#    - Identifies untracked files
#    - Ensures clean working directory
#
# 4. Submodule Configuration
#    - Validates .gitmodules entries
#    - Confirms correct remote URLs
#    - Ensures all expected submodules are configured
#
# 5. Submodule States
#    - Verifies initialization status
#    - Checks for detached HEAD states
#    - Validates commit alignment
#    - Detects local modifications
#
# Error Handling:
# - Exits with status 0 if workspace is valid
# - Exits with non-zero status if any issues found
# - Provides clear, actionable error messages
# - Lists specific problems that need addressing
# - Suggests commands to fix common issues
#
# Version: 0.1.0
#
# Exit on error
set -e

# Usage message
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Validates the workspace is in a known good state.

Options:
  -h, --help     Show this help message
  -v, --verbose  Show detailed output
  --version      Show version information
EOF
}

# Parse arguments
VERBOSE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            exit 1
            ;;
    esac
done

# Component configuration
# These are the official upstream repositories that this workspace should track
readonly ORCHESTRATOR_URL="https://github.com/pyx-industries/julee-orchestrator.git"
readonly ORCHESTRATOR_PATH="components/orchestrator"

readonly KNOWLEDGE_URL="https://github.com/pyx-industries/julee-knowledge-service.git"
readonly KNOWLEDGE_PATH="components/knowledge-service"

readonly ACTION_URL="https://github.com/pyx-industries/julee-action-service.git"
readonly ACTION_PATH="components/action-service"

readonly POLICY_URL="https://github.com/pyx-industries/julee-policy-service.git"
readonly POLICY_PATH="components/policy-service"

# Component Configuration
# These define the official upstream repositories that this workspace should track.
# Each component can be:
# - Used as-is from our reference implementations
# - Replaced with custom implementations
# - Substituted with third-party services
# - Mixed and matched as needed
#
# The only requirement is that replacement implementations must conform to the
# documented interfaces.



# Function to check actual submodule states
check_submodule_states() {
    local has_issues=0

    echo "Checking submodule states..."

    # Check each submodule directory exists and is initialized
    for path in "$ORCHESTRATOR_PATH" "$KNOWLEDGE_PATH" "$ACTION_PATH" "$POLICY_PATH"; do
        if [ ! -d "$path" ]; then
            echo "Error: Submodule directory '$path' not found"
            echo "Run: git submodule update --init --recursive"
            has_issues=1
            continue
        fi

        # For submodules, .git is actually a file pointing to the real .git directory
        if [ ! -f "$path/.git" ] && [ ! -d "$path/.git" ]; then
            echo "Error: Submodule '$path' not properly initialized"
            echo "Run: git submodule update --init $path"
            has_issues=1
            continue
        fi

        # Check for local modifications
        if ! (cd "$path" && git diff --quiet HEAD); then
            echo "Error: Submodule '$path' has local modifications"
            if [ "$VERBOSE" -eq 1 ]; then
                (cd "$path" && git status --short)
            fi
            has_issues=1
        fi

        # Check for detached HEAD
        if is_detached_head "$path"; then
            echo "Warning: Submodule '$path' is in detached HEAD state"
            if [ "$VERBOSE" -eq 1 ]; then
                echo "Current commit: $(cd "$path" && git rev-parse --short HEAD)"
                echo "To fix: cd $path && git checkout master"
            fi
            has_issues=1
        fi

        # Verify submodule is at the expected commit
        expected_commit=$(git ls-tree HEAD "$path" | awk '{print $3}')
        actual_commit=$(cd "$path" && git rev-parse HEAD)
        if [ "$expected_commit" != "$actual_commit" ]; then
            echo "Error: Submodule '$path' is not at the expected commit"
            echo "Expected: $expected_commit"
            echo "Actual: $actual_commit"
            echo "To fix: git submodule update $path"
            has_issues=1
        fi
    done

    return $has_issues
}

# Function to validate submodule configuration
check_submodule_config() {
    local has_issues=0

    echo "Checking submodule configuration..."

    # Check .gitmodules exists
    if [ ! -f ".gitmodules" ]; then
        if [ "$VERBOSE" -eq 1 ]; then
            echo "No .gitmodules file found - workspace not yet initialized"
            echo "To initialize the workspace with required submodules:"
            echo "  1. git submodule add $ORCHESTRATOR_URL $ORCHESTRATOR_PATH"
            echo "  2. git submodule add $KNOWLEDGE_URL $KNOWLEDGE_PATH"
            echo "  3. git submodule add $ACTION_URL $ACTION_PATH"
            echo "  4. git submodule add $POLICY_URL $POLICY_PATH"
            echo "  5. git submodule update --init --recursive"
        else
            echo "Error: Workspace not initialized (run with -v for setup instructions)"
        fi
        return 1
    fi

    # Check each component
    check_component "$ORCHESTRATOR_PATH" "$ORCHESTRATOR_URL" || has_issues=1
    check_component "$KNOWLEDGE_PATH" "$KNOWLEDGE_URL" || has_issues=1
    check_component "$ACTION_PATH" "$ACTION_URL" || has_issues=1
    check_component "$POLICY_PATH" "$POLICY_URL" || has_issues=1

    return $has_issues
}

# Function to check required directories exist
check_required_directories() {
    local has_issues=0

    echo "Checking required directories..."

    # Check core directories from CONVENTIONS.md
    local required_dirs=(
        "components"
        "deployment"
        "bin"
    )

    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            echo "Error: Required directory '$dir' not found"
            has_issues=1
        elif [ "$VERBOSE" -eq 1 ]; then
            echo "Found required directory: $dir"
        fi
    done

    return $has_issues
}

# Function to check required tools are available
check_required_tools() {
    local has_issues=0

    echo "Checking required tools..."

    # Core tools needed for the workspace
    local required_tools=(
        "git"
        "bash"
        "sed"
        "awk"
    )

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "Error: Required tool '$tool' not found in PATH"
            has_issues=1
        elif [ "$VERBOSE" -eq 1 ]; then
            echo "Found required tool: $tool"
        fi
    done

    return $has_issues
}

# Function to check git status
check_git_status() {
    local has_issues=0
    local status_output
    local staged_changes
    local modified_files
    local untracked_files

    echo "Checking main repository status..."

    # Get status and filter different types of changes
    if ! status_output=$(git status --porcelain); then
        echo "Error: Failed to get git status"
        exit 1
    fi

    # Initialize counters
    staged_count=0
    modified_count=0
    added_modified_count=0
    untracked_count=0
    total_count=0

    # Filter different types of changes
    staged_changes=$(echo "$status_output" | grep '^[AMDRC]' | grep -v '^AM' || true)
    modified_files=$(echo "$status_output" | grep '^.[MD]' | grep -v '^AM' || true)
    added_modified=$(echo "$status_output" | grep '^AM' || true)
    untracked_files=$(echo "$status_output" | grep '^??' || true)

    # Count each type
    [ -n "$staged_changes" ] && staged_count=$(echo "$staged_changes" | grep -c '^' || true)
    [ -n "$modified_files" ] && modified_count=$(echo "$modified_files" | grep -c '^' || true)
    [ -n "$added_modified" ] && added_modified_count=$(echo "$added_modified" | grep -c '^' || true)
    [ -n "$untracked_files" ] && untracked_count=$(echo "$untracked_files" | grep -c '^' || true)
    total_count=$((staged_count + modified_count + untracked_count))  # Don't double count AM files

    if [ $total_count -gt 0 ]; then
        has_issues=1
        echo "Repository has pending changes ($total_count total):"

        if [ -n "$staged_changes" ] || [ -n "$added_modified" ]; then
            echo -e "\nStaged changes ($(($staged_count + $added_modified_count)) files):"
            [ -n "$staged_changes" ] && echo "$staged_changes"
            [ -n "$added_modified" ] && echo "$added_modified"
        fi

        if [ -n "$modified_files" ]; then
            echo -e "\nModified (unstaged) files ($modified_count files):"
            echo "$modified_files"
        fi

        if [ -n "$untracked_files" ]; then
            echo -e "\nUntracked files ($untracked_count files):"
            echo "$untracked_files"
        fi
        echo -e "\nTo fix:"
        [ -n "$staged_changes" ] && echo "  - git commit # to commit staged changes"
        [ -n "$modified_files" ] && echo "  - git add -u # to stage modified files"
        [ -n "$untracked_files" ] && echo "  - git clean -fd # to remove untracked files"
        echo "  - git reset --hard # to discard all changes (use with caution!)"
    else
        if [ "$VERBOSE" -eq 1 ]; then
            echo "Git working directory is clean"
        fi
    fi

    return $has_issues
}

# Main logic
echo "Checking workspace state..."
exit_code=0

if ! check_required_directories; then
    exit_code=1
fi

if ! check_required_tools; then
    exit_code=1
fi

if ! check_git_status; then
    exit_code=1
fi

if ! check_submodule_config; then
    exit_code=1
fi

if ! check_submodule_states; then
    exit_code=1
fi

# Print final status
if [ $exit_code -eq 0 ]; then
    echo -e "\nWorkspace Status: VALID"
    echo "All checks passed successfully"
else
    echo -e "\nWorkspace Status: INVALID"
    echo "One or more checks failed - see errors above"
fi

exit $exit_code
