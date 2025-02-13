#!/bin/bash
# Common functions for release management scripts

# Version Management
get_next_version_number() {
    local base_version="$1"
    local type="$2"
    local highest=0
    
    # List all tags matching the base version with the given type
    for tag in $(git tag -l "${base_version}-${type}*" | sort -V); do
        local num=$(echo "$tag" | grep -oE "${type}[0-9]+" | grep -oE '[0-9]+')
        if [ -n "$num" ] && [ "$num" -gt "$highest" ]; then
            highest=$num
        fi
    done
    
    echo $((highest + 1))
}

suggest_next_versions() {
    local suggestions=()
    local latest_stable=""
    local latest_rc=""
    local latest_test=""

    # Get latest versions of each type
    while read -r tag; do
        if [[ $tag =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            latest_stable="$tag"
        elif [[ $tag =~ ^v[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+$ ]]; then
            latest_rc="$tag"
        elif [[ $tag =~ ^v[0-9]+\.[0-9]+\.[0-9]+-test[0-9]+$ ]]; then
            latest_test="$tag"
        fi
    done < <(git tag -l 'v*' | sort -V)

    # From latest stable, suggest:
    if [[ -n "$latest_stable" ]]; then
        if [[ $latest_stable =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
            local major="${BASH_REMATCH[1]}"
            local minor="${BASH_REMATCH[2]}"
            local patch="${BASH_REMATCH[3]}"
            # Patch increment
            suggestions+=("v${major}.${minor}.$((patch + 1)) (patch increment)")
            # New minor with test
            suggestions+=("v${major}.$((minor + 1)).0-test1 (new minor)")
            # New major with test
            suggestions+=("v$((major + 1)).0.0-test1 (new major)")
        fi
    fi

    # From latest RC without stable equivalent
    if [[ -n "$latest_rc" ]] && ! git rev-parse --verify --quiet "${latest_rc%-rc*}" >/dev/null; then
        if [[ $latest_rc =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)-rc([0-9]+)$ ]]; then
            local major="${BASH_REMATCH[1]}"
            local minor="${BASH_REMATCH[2]}"
            local patch="${BASH_REMATCH[3]}"
            local rc="${BASH_REMATCH[4]}"
            # Next RC
            suggestions+=("v${major}.${minor}.${patch}-rc$((rc + 1)) (next RC)")
            # Stable release
            suggestions+=("v${major}.${minor}.${patch} (stable from RC)")
        fi
    fi

    # From latest test without RC
    if [[ -n "$latest_test" ]]; then
        if [[ $latest_test =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)-test([0-9]+)$ ]]; then
            local major="${BASH_REMATCH[1]}"
            local minor="${BASH_REMATCH[2]}"
            local patch="${BASH_REMATCH[3]}"
            local test="${BASH_REMATCH[4]}"
            # Next test
            suggestions+=("v${major}.${minor}.${patch}-test$((test + 1)) (next test)")
            # First RC
            suggestions+=("v${major}.${minor}.${patch}-rc1 (first RC)")
        fi
    fi

    printf '%s\n' "${suggestions[@]}"
}

validate_version() {
    local version="$1"
    if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-rc[0-9]+|-test[0-9]+)?$ ]]; then
        return 1
    fi
    return 0
}

compare_versions() {
    local v1="$1"
    local v2="$2"
    
    # Strip v prefix
    v1="${v1#v}"
    v2="${v2#v}"
    
    # Split into components
    local IFS=.-
    local v1_parts=($v1)
    local v2_parts=($v2)
    
    # Compare major.minor.patch
    for i in {0..2}; do
        if (( ${v1_parts[$i]:-0} > ${v2_parts[$i]:-0} )); then
            return 1
        elif (( ${v1_parts[$i]:-0} < ${v2_parts[$i]:-0} )); then
            return 2
        fi
    done
    
    # If we get here, base versions are equal
    # Check pre-release tags if present
    if [ -z "${v1_parts[3]:-}" ] && [ -z "${v2_parts[3]:-}" ]; then
        return 0
    elif [ -z "${v1_parts[3]:-}" ]; then
        return 1  # No pre-release > pre-release
    elif [ -z "${v2_parts[3]:-}" ]; then
        return 2  # Pre-release < no pre-release
    else
        # Both have pre-release, compare them
        if [ "${v1_parts[3]}" = "${v2_parts[3]}" ]; then
            return 0
        else
            return 3  # Different pre-releases are incomparable
        fi
    fi
}

# Workspace Management
check_workspace_state() {
    local has_issues=0
    local status_output
    local staged_changes
    local modified_files
    local untracked_files

    # Get status and filter different types of changes
    if ! status_output=$(git status --porcelain); then
        echo "Error: Failed to get git status"
        return 1
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
    total_count=$((staged_count + modified_count + untracked_count))

    return $(( total_count > 0 ))
}

is_detached_head() {
    local path="$1"
    if (cd "$path" && git symbolic-ref -q HEAD >/dev/null); then
        return 1  # Not detached
    else
        return 0  # Detached
    fi
}

check_component() {
    local path="$1"
    local url="$2"
    local has_issues=0

    if ! git config --file=.gitmodules --get "submodule.$path.path" >/dev/null; then
        echo "Error: Submodule '$path' not configured in .gitmodules"
        has_issues=1
    else
        configured_url=$(git config --file=.gitmodules --get "submodule.$path.url")
        if [ "$configured_url" != "$url" ]; then
            echo "Error: Submodule '$path' URL mismatch:"
            echo "  Expected: $url"
            echo "  Found: $configured_url"
            has_issues=1
        fi
    fi
    return $has_issues
}

validate_components() {
    local has_issues=0
    
    while read -r path; do
        if [ ! -d "$path" ]; then
            print_error "Component directory '$path' not found"
            has_issues=1
            continue
        fi
        
        if [ ! -f "$path/.git" ] && [ ! -d "$path/.git" ]; then
            print_error "Component '$path' not properly initialized"
            has_issues=1
            continue
        fi
        
        if [ -n "$(cd "$path" && git status --porcelain)" ]; then
            print_error "Component '$path' has local modifications"
            has_issues=1
        fi
    done < <(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' | cut -d' ' -f2)
    
    return $has_issues
}

get_component_version() {
    local component="$1"
    local version
    
    if [ ! -d "components/$component" ]; then
        echo "none"
        return
    fi
    
    if [ -n "$(cd "components/$component" && git status --porcelain)" ]; then
        version=$(cd "components/$component" && git describe --tags 2>/dev/null || git rev-parse --short HEAD)
        echo "${version}-modified"
    else
        version=$(cd "components/$component" && git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD)
        if [ -n "$version" ] && ! validate_version "$version"; then
            echo "invalid-version:$version"
        else
            echo "$version"
        fi
    fi
}

get_expected_version() {
    local component="$1"
    local target_version="$2"
    local version
    
    version=$(git tag -l --format='%(contents)' "$target_version" | \
        sed -n "/Components:/,\$p" | \
        grep "^$component:" | \
        cut -d' ' -f2) || echo "none"
    
    if [ "$version" != "none" ]; then
        if ! validate_version "$version"; then
            echo "invalid-version:$version"
        elif ! check_version_compatibility "$component" "$version"; then
            echo "incompatible:$version"
        else
            echo "$version"
        fi
    else
        echo "none"
    fi
}

# Git Operations
create_tag_message() {
    local version="$1"
    local message=""
    
    # Add component versions
    message+="Components:\n"
    while read -r path; do
        local component=$(basename "$path")
        local comp_version=$(get_component_version "$component")
        message+="$component: $comp_version\n"
    done < <(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' | cut -d' ' -f2)
    
    # Add release notes if available
    if [ -f "releases/notes-${version}.md" ]; then
        message+="\nRelease Notes:\n"
        message+=$(cat "releases/notes-${version}.md")
    fi
    
    echo -e "$message"
}

get_tag_metadata() {
    local tag="$1"
    git tag -l --format='%(contents)' "$tag"
}

generate_release_notes() {
    local version="$1"
    local last_version=$(git describe --tags --abbrev=0 "$version"^ 2>/dev/null || echo "")
    local notes=""
    
    notes+="# Release $version\n\n"
    notes+="## Component Versions\n\n"
    notes+=$(get_tag_metadata "$version" | sed -n '/Components:/,$p')
    notes+="\n## Changes\n\n"
    
    if [ -n "$last_version" ]; then
        notes+=$(git log --pretty=format:"- %s" "$last_version..$version")
    else
        notes+=$(git log --pretty=format:"- %s" "$version")
    fi
    
    echo -e "$notes"
}

# Output Formatting
format_output() {
    local format="$1"
    local data="$2"
    
    case "$format" in
        table)
            echo "$data"
            ;;
        csv)
            echo "$data" | sed 's/: /,/g'
            ;;
        json)
            echo "{"
            echo "$data" | while IFS=': ' read -r key value; do
                [ -n "$key" ] || continue
                echo "  \"$key\": \"$value\","
            done | sed '$ s/,$//'
            echo "}"
            ;;
        *)
            print_error "Invalid format: $format"
            return 1
            ;;
    esac
}

print_error() {
    echo "Error: $1" >&2
}

print_warning() {
    echo "Warning: $1" >&2
}

format_version_table() {
    local julee_version="$1"
    local -n components_ref="$2"
    local -n issues_ref="$3"
    local status="$4"

    echo "Julee $julee_version"
    echo "Current component versions:"
    for component in "${!components_ref[@]}"; do
        IFS='|' read -r current expected <<< "${components_ref[$component]}"
        warning=""
        if [[ "$current" != "$expected" && "$expected" != "none" ]] || \
           [[ "$current" =~ -modified$ ]] || \
           [[ ! "$current" =~ ^v[0-9] ]]; then
            warning=" ⚠️"
        fi
        printf "%s: %s (expected: %s)%s\n" \
            "$component" "$current" "$expected" "$warning"
    done
    echo
    echo "Status: $status"
    if [ ${#issues_ref[@]} -gt 0 ]; then
        echo "Issues:"
        for issue in "${issues_ref[@]}"; do
            echo "- $issue"
        done
    fi
}

format_version_csv() {
    local -n components_ref="$1"
    
    echo "component,current,expected"
    for component in "${!components_ref[@]}"; do
        IFS='|' read -r current expected <<< "${components_ref[$component]}"
        echo "$component,$current,$expected"
    done
}

format_version_json() {
    local julee_version="$1"
    local -n components_ref="$2"
    local -n issues_ref="$3"
    local status="$4"

    echo "{"
    echo "  \"julee_version\": \"$julee_version\","
    echo "  \"status\": \"$status\","
    echo "  \"components\": {"
    first=1
    for component in "${!components_ref[@]}"; do
        IFS='|' read -r current expected <<< "${components_ref[$component]}"
        [ $first -eq 1 ] || echo ","
        echo "    \"$component\": {"
        echo "      \"current\": \"$current\","
        echo "      \"expected\": \"$expected\""
        echo -n "    }"
        first=0
    done
    echo
    echo "  },"
    echo "  \"issues\": ["
    for i in "${!issues_ref[@]}"; do
        [ $i -eq 0 ] || echo ","
        echo "    \"${issues_ref[$i]}\""
    done
    echo "  ]"
    echo "}"
}

# Configuration Management
load_config() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        return 1
    fi
    
    # Source the config file
    . "$config_file"
    return 0
}

get_version_constraints() {
    local component="$1"
    local constraints_file="deployment/version-constraints.txt"
    
    if [ ! -f "$constraints_file" ]; then
        return 0
    fi
    
    grep "^$component:" "$constraints_file" | cut -d: -f2- || echo ""
}

# Compatibility checking
check_version_compatibility() {
    local component="$1"
    local version="$2"
    local constraints=$(get_version_constraints "$component")
    
    [ -z "$constraints" ] && return 0
    
    # TODO: Implement actual constraint checking
    # For now, just return true
    return 0
}
