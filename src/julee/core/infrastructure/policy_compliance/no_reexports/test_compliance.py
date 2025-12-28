"""No re-exports policy compliance tests.

This policy enforces that __init__.py files should not re-export symbols
from external modules. Re-exports obscure dependency graphs and can
lead to circular imports and layer violations.

Allowed in __init__.py:
- Relative imports from submodules (from .submodule import Thing)
- Side-effect imports for registration (import .submodule)
- Package-level constants and simple definitions

Not allowed:
- Re-exporting from external packages (from other.package import Thing)
- Re-exporting from infrastructure into core
"""

import ast
import os
from pathlib import Path


def get_target_path() -> Path:
    """Get the target solution path from environment."""
    target = os.environ.get("JULEE_TARGET")
    if target:
        return Path(target)
    # Default to julee itself
    return Path(__file__).parent.parent.parent.parent.parent.parent.parent


def find_init_files(root: Path) -> list[Path]:
    """Find all __init__.py files in src/."""
    src_dir = root / "src"
    if not src_dir.exists():
        return []
    return list(src_dir.glob("**/__init__.py"))


def extract_reexports(init_file: Path) -> list[tuple[str, str]]:
    """Extract re-exports from an __init__.py file.

    Returns list of (module, symbol) tuples for non-relative imports
    that import specific symbols (not just for side effects).
    """
    try:
        content = init_file.read_text()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError):
        return []

    reexports = []
    # Only check module-level statements, not imports inside functions
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            # Skip relative imports (from . or from .submodule)
            if node.level > 0:
                continue

            # Skip imports that don't import specific names
            if not node.names:
                continue

            # Skip "import X" style (no 'from')
            if node.module is None:
                continue

            # This is "from absolute.module import something"
            for alias in node.names:
                if alias.name != "*":
                    reexports.append((node.module, alias.name))

    return reexports


class TestNoReexports:
    """Policy: __init__.py files MUST NOT re-export external symbols."""

    def test_init_files_MUST_NOT_reexport_from_external_modules(self):
        """__init__.py files MUST NOT re-export from external modules.

        Re-exports obscure the true source of symbols and can lead to:
        - Circular import issues
        - Layer violations (re-exporting infrastructure into core)
        - Confusing dependency graphs

        Import directly from the defining module instead.
        """
        target = get_target_path()
        init_files = find_init_files(target)

        violations = []
        for init_file in init_files:
            reexports = extract_reexports(init_file)
            if reexports:
                rel_path = init_file.relative_to(target)
                for module, symbol in reexports:
                    violations.append(
                        f"{rel_path}: re-exports '{symbol}' from '{module}'"
                    )

        assert (
            not violations
        ), f"Found {len(violations)} re-export violations:\n" + "\n".join(violations)
