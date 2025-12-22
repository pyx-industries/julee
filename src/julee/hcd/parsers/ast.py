"""Python code introspection parser.

Parses Python source files using AST to extract class information
for ADR 001-compliant bounded contexts.
"""

import ast
import logging
from pathlib import Path

from ..domain.models.code_info import BoundedContextInfo, ClassInfo

logger = logging.getLogger(__name__)


def parse_python_classes(directory: Path) -> list[ClassInfo]:
    """Extract class information from Python files in a directory using AST.

    Args:
        directory: Directory to scan for .py files

    Returns:
        List of ClassInfo objects sorted by class name
    """
    if not directory.exists():
        return []

    classes = []
    for py_file in directory.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or ""
                    first_line = docstring.split("\n")[0].strip() if docstring else ""
                    classes.append(
                        ClassInfo(
                            name=node.name,
                            docstring=first_line,
                            file=py_file.name,
                        )
                    )
        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Could not parse {py_file}: {e}")

    return sorted(classes, key=lambda c: c.name)


def parse_module_docstring(module_path: Path) -> tuple[str | None, str | None]:
    """Extract module docstring from a Python file using AST.

    Args:
        module_path: Path to Python file

    Returns:
        Tuple of (first_line, full_docstring) or (None, None) if not found
    """
    if not module_path.exists():
        return None, None

    try:
        source = module_path.read_text()
        tree = ast.parse(source, filename=str(module_path))
        docstring = ast.get_docstring(tree)
        if docstring:
            first_line = docstring.split("\n")[0].strip()
            return first_line, docstring
    except SyntaxError as e:
        logger.warning(f"Syntax error in {module_path}: {e}")
    except Exception as e:
        logger.warning(f"Could not parse {module_path}: {e}")

    return None, None


def parse_bounded_context(context_dir: Path) -> BoundedContextInfo | None:
    """Introspect a bounded context directory for ADR 001-compliant code structure.

    Expected directory structure:
    - context_dir/
      - __init__.py (module docstring becomes objective)
      - domain/
        - models/ (entities)
        - repositories/ (repository protocols)
        - services/ (service protocols)
      - use_cases/ (use case classes)
      - infrastructure/ (optional)

    Args:
        context_dir: Path to the bounded context directory

    Returns:
        BoundedContextInfo if directory exists, None otherwise
    """
    if not context_dir.exists() or not context_dir.is_dir():
        return None

    init_file = context_dir / "__init__.py"
    objective, full_docstring = parse_module_docstring(init_file)

    return BoundedContextInfo(
        slug=context_dir.name,
        entities=parse_python_classes(context_dir / "domain" / "models"),
        use_cases=parse_python_classes(context_dir / "use_cases"),
        repository_protocols=parse_python_classes(
            context_dir / "domain" / "repositories"
        ),
        service_protocols=parse_python_classes(context_dir / "domain" / "services"),
        has_infrastructure=(context_dir / "infrastructure").exists(),
        code_dir=context_dir.name,
        objective=objective,
        docstring=full_docstring,
    )


def scan_bounded_contexts(
    src_dir: Path,
    exclude: list[str] | None = None,
) -> list[BoundedContextInfo]:
    """Scan a source directory for all bounded contexts.

    Only includes directories that have the structure of a bounded context
    (i.e., contain a domain/ subdirectory with models or repositories).

    Args:
        src_dir: Root source directory (e.g., project/src/)
        exclude: List of directory names to exclude (e.g., ["shared"])

    Returns:
        List of BoundedContextInfo objects for all discovered contexts
    """
    if not src_dir.exists():
        logger.info(f"Source directory not found: {src_dir}")
        return []

    exclude = exclude or []
    contexts = []
    for context_dir in src_dir.iterdir():
        if not context_dir.is_dir():
            continue
        if context_dir.name.startswith((".", "_")):
            continue
        if context_dir.name in exclude:
            continue

        # Only consider directories with domain/ structure as bounded contexts
        domain_dir = context_dir / "domain"
        if not domain_dir.exists():
            continue

        context_info = parse_bounded_context(context_dir)
        if context_info:
            contexts.append(context_info)
            logger.info(
                f"Introspected bounded context '{context_info.slug}': {context_info.summary()}"
            )

    return contexts
