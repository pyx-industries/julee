"""Import analysis parser.

AST-based parsing for extracting import statements from Python source files.
Used for dependency rule validation in Clean Architecture.
"""

import ast
import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImportInfo(BaseModel):
    """Information about an import statement.

    Represents imports extracted via AST for dependency analysis.
    Used to validate Clean Architecture's dependency rule.
    """

    module: str  # e.g., "julee.hcd.domain.use_cases"
    names: list[str] = Field(default_factory=list)  # e.g., ["CreateStoryUseCase"]
    is_relative: bool = False
    file: str = ""  # source file containing this import


# Architecture layer keywords for dependency analysis
# Layer hierarchy (outer to inner):
#   deployment -> apps -> infrastructure -> use_cases -> models
#
# Protocols (repositories/, services/) are at the same level as use_cases,
# defining abstractions that use_cases depend on but don't know implementations of.
_LAYER_KEYWORDS = {
    # Innermost - domain entities/models
    "models": "models",
    "entities": "models",  # alias
    # Middle-inner - use cases and protocol definitions
    "use_cases": "use_cases",
    "usecases": "use_cases",  # alias
    "repositories": "repositories",  # protocol definitions
    "services": "services",  # protocol definitions
    # Middle-outer - infrastructure implementations
    "infrastructure": "infrastructure",
    # Outer - application layer (FastAPI, MCP, CLI)
    "apps": "apps",
    # Outermost - deployment configuration
    "deployment": "deployment",
}


def classify_import_layer(import_path: str) -> str | None:
    """Classify an import path into architectural layer.

    Identifies which Clean Architecture layer a module belongs to
    by examining the module path for layer keywords.

    Args:
        import_path: Module path like "julee.hcd.domain.use_cases"

    Returns:
        Layer name: "models", "use_cases", "repositories", "services",
        "infrastructure", or None if not a domain layer import
    """
    parts = import_path.lower().split(".")
    for part in parts:
        if part in _LAYER_KEYWORDS:
            return _LAYER_KEYWORDS[part]
    return None


def extract_imports(file_path: Path) -> list[ImportInfo]:
    """Extract all imports from a Python file.

    Parses the file's AST to extract both:
    - `import module` statements
    - `from module import name` statements

    Args:
        file_path: Path to the Python file

    Returns:
        List of ImportInfo with module path and imported names
    """
    if not file_path.exists():
        return []

    imports = []
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                # import module, import module as alias
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            names=[],
                            is_relative=False,
                            file=str(file_path),
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                # from module import name, from .module import name
                module = node.module or ""
                names = [alias.name for alias in node.names]
                is_relative = node.level > 0
                imports.append(
                    ImportInfo(
                        module=module,
                        names=names,
                        is_relative=is_relative,
                        file=str(file_path),
                    )
                )
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")

    return imports
