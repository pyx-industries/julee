# switch-release.sh

Create a file in the current directory (bin/) called `switch-release.sh` which is a bash script that switches the workspace to a specific release version.

## Purpose
Safely transitions the workspace to a specified release tag by updating both the main repository and all submodules to their correct versions for that release.

## Implementation Details

The script should:

1. Accept a release tag as a command-line argument
2. Validate the specified release tag exists
3. Check for any local modifications that would be lost
4. Fetch the latest tags from the remote
5. Checkout the requested release tag
6. Update all submodules to their correct versions for that release
7. Verify the final workspace state matches the release specification

## Error Handling

The script should:
- Validate input parameters
- Check for uncommitted changes
- Verify tag existence before attempting checkout
- Handle submodule state verification
- Exit with appropriate error codes and messages if any step fails
- Provide clear error messages if workspace is in an invalid state

## Example Usage

```bash
./switch-release.sh v1.2.3
```

Expected output on success:
```
Switching to release v1.2.3
Checking workspace state... OK
Updating submodules... OK
Workspace is now at release v1.2.3
All components verified
```

Expected output on error:
```
ERROR: Cannot switch to v1.2.3
Reason: Local modifications present
Please commit or stash your changes first
```
