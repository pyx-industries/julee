# run-integration-tests.sh

Create a file in the current directory (bin/) called `run-integration-tests.sh`, which is a bash script that executes integration tests across all components to verify they work together correctly.

## Purpose

This script runs integration tests to ensure all components can interact properly before finalizing a release. It sets up a test environment, executes the tests, and generates a report.

## Implementation

```bash
#!/bin/bash
set -euo pipefail

# Usage message
usage() {
    echo "Usage: $0 [--report-dir <dir>]"
    echo "Runs integration tests across all components"
    echo
    echo "Options:"
    echo "  --report-dir <dir>  Directory for test reports (default: tests/reports)"
    exit 1
}

# Parse arguments
REPORT_DIR="tests/reports"
while [[ $# -gt 0 ]]; do
    case $1 in
        --report-dir)
            REPORT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

# Record test environment
{
    echo "Test Environment:"
    echo "Date: $(date)"
    echo "Git commit: $(git rev-parse HEAD)"
    echo "Component versions:"
    for dir in components/*; do
        if [ -d "$dir" ]; then
            component=$(basename "$dir")
            version=$(cd "$dir" && git describe --tags --always)
            echo "  $component: $version"
        fi
    done
    echo
} > "$REPORT_DIR/environment.txt"

# Run tests for each component
EXIT_CODE=0
for dir in components/*; do
    if [ ! -d "$dir" ]; then
        continue
    fi

    component=$(basename "$dir")
    echo "Testing $component..."

    # Run component's integration tests if they exist
    if [ -f "$dir/tests/integration.sh" ]; then
        if ! (cd "$dir" && ./tests/integration.sh --report-dir "../../$REPORT_DIR/$component"); then
            echo "Error: Integration tests failed for $component"
            EXIT_CODE=1
        fi
    else
        echo "Warning: No integration tests found for $component"
    fi
done

# Generate summary report
{
    echo "Integration Test Summary"
    echo "======================="
    echo
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Status: PASSED"
    else
        echo "Status: FAILED"
    fi
    echo
    echo "See component-specific reports in $REPORT_DIR/"
} > "$REPORT_DIR/summary.txt"

exit $EXIT_CODE
```

## Usage

```bash
# Run tests with default report location
./run-integration-tests.sh

# Specify custom report directory
./run-integration-tests.sh --report-dir /tmp/test-reports
```

## Exit Codes

- 0: All tests passed
- 1: One or more tests failed

## Dependencies

- git
- Component-specific test dependencies

## Notes

- Creates timestamped test reports
- Records environment information
- Runs each component's integration tests
- Generates summary report
- Preserves component-specific test output
