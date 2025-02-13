# Pyx Julee Project Conventions

This document outlines the key conventions used across the Pyx Julee project.

## Project Structure

- `components/` - Reference implementations (as git submodules)
- `deployment/` - Deployment pattern examples
- `bin/` - Release management scripts
- `docs/` - Release management documentation

## Component Conventions

### Submodules
- Each component is maintained as a separate git submodule
- Components must be versioned using semantic versioning
- Component interfaces must be well-documented
- Breaking changes must be clearly noted in release notes

### Implementation Freedom
Components can be:
- Used as-is from our reference implementations
- Replaced with custom implementations
- Substituted with third-party services
- Mixed and matched as needed

The only requirement is that replacement implementations must conform to the documented interfaces.

## Deployment Conventions

- Deployment patterns are illustrative, not prescriptive
- Each deployment pattern should document its:
  - Component choices
  - Infrastructure requirements
  - Configuration approach
  - Security considerations

## Release Management

- Release processes are documented through executable scripts in `bin/`
- Release versions are tracked in git tags
- Component version combinations are documented with each release
- Breaking changes across components must be coordinated

## Documentation

- Interface documentation lives with each component
- Architecture documentation lives in this repository
- Deployment patterns serve as working examples
- Scripts serve as executable documentation

## Contributing

- Follow the existing code style of each component
- Document interface changes thoroughly
- Include tests for new functionality
- Update relevant deployment patterns when changing interfaces
- Submit changes through pull requests

## Version Compatibility

- Component version compatibility is documented with each release
- Breaking changes require major version bumps
- Deployment patterns specify their minimum component versions
