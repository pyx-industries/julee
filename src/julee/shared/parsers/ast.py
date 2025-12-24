"""Python code introspection parser.

Parses Python source files using AST to extract class information
for Clean Architecture bounded contexts.
"""

import ast
import logging
from pathlib import Path

from julee.shared.domain.models.code_info import (
    BoundedContextInfo,
    ClassInfo,
    FieldInfo,
    MethodInfo,
)

logger = logging.getLogger(__name__)


def _get_annotation_str(node: ast.expr | None) -> str:
    """Convert an AST annotation node to a string representation."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _extract_base_classes(class_node: ast.ClassDef) -> list[str]:
    """Extract base class names from a class definition."""
    bases = []
    for base in class_node.bases:
        try:
            bases.append(ast.unparse(base))
        except Exception:
            pass
    return bases


def _extract_class_fields(class_node: ast.ClassDef) -> list[FieldInfo]:
    """Extract field information from a class definition.

    Handles:
    - Simple class attributes with type annotations
    - Pydantic Field() defaults
    - Regular default values
    """
    fields = []
    for node in class_node.body:
        # Handle annotated assignments: field: Type = value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            type_annotation = _get_annotation_str(node.annotation)
            default = None
            if node.value is not None:
                try:
                    default = ast.unparse(node.value)
                except Exception:
                    default = "..."
            fields.append(
                FieldInfo(name=name, type_annotation=type_annotation, default=default)
            )
    return fields


def _extract_class_methods(class_node: ast.ClassDef) -> list[MethodInfo]:
    """Extract method information from a class definition.

    Extracts public methods (not starting with _) including:
    - Regular methods
    - Async methods
    - Method signatures and docstrings
    """
    methods = []
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private/dunder methods
            if node.name.startswith("_"):
                continue

            # Extract parameter names (excluding self)
            params = []
            for arg in node.args.args:
                if arg.arg != "self":
                    params.append(arg.arg)

            # Get return type annotation
            return_type = _get_annotation_str(node.returns)

            # Get docstring
            docstring = ast.get_docstring(node) or ""
            first_line = docstring.split("\n")[0].strip() if docstring else ""

            methods.append(
                MethodInfo(
                    name=node.name,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    parameters=params,
                    return_type=return_type,
                    docstring=first_line,
                )
            )
    return methods


def _parse_class_node(class_node: ast.ClassDef, file_name: str) -> ClassInfo:
    """Parse a class AST node into ClassInfo with full details."""
    docstring = ast.get_docstring(class_node) or ""
    first_line = docstring.split("\n")[0].strip() if docstring else ""
    return ClassInfo(
        name=class_node.name,
        docstring=first_line,
        file=file_name,
        bases=_extract_base_classes(class_node),
        fields=_extract_class_fields(class_node),
        methods=_extract_class_methods(class_node),
    )


def parse_python_classes(
    directory: Path,
    recursive: bool = True,
    exclude_tests: bool = True,
    exclude_files: list[str] | None = None,
) -> list[ClassInfo]:
    """Extract class information from Python files in a directory using AST.

    Args:
        directory: Directory to scan for .py files
        recursive: If True, scan subdirectories recursively
        exclude_tests: If True, exclude test files and test classes
        exclude_files: List of file names to exclude (e.g., ["requests.py"])

    Returns:
        List of ClassInfo objects sorted by class name
    """
    if not directory.exists():
        return []

    exclude_files = exclude_files or []
    classes = []
    pattern = "**/*.py" if recursive else "*.py"
    for py_file in directory.glob(pattern):
        # Skip private/internal files
        if py_file.name.startswith("_"):
            continue

        # Skip test files
        if exclude_tests:
            if py_file.name.startswith("test_") or "/tests/" in str(py_file):
                continue

        # Skip explicitly excluded files
        if py_file.name in exclude_files:
            continue

        try:
            source = py_file.read_text()
            tree = ast.parse(source, filename=str(py_file))

            # Get relative path from directory for proper autoapi linking
            relative_path = py_file.relative_to(directory)
            # Convert to module-style path (diagrams/container_diagram.py -> diagrams/container_diagram)
            file_path = str(relative_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Skip test classes
                    if exclude_tests and node.name.startswith("Test"):
                        continue

                    classes.append(_parse_class_node(node, file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {py_file}: {e}")
        except Exception as e:
            logger.warning(f"Could not parse {py_file}: {e}")

    return sorted(classes, key=lambda c: c.name)


def parse_python_classes_from_file(file_path: Path) -> list[ClassInfo]:
    """Extract class information from a single Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of ClassInfo objects sorted by class name
    """
    if not file_path.exists():
        return []

    classes = []
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(_parse_class_node(node, file_path.name))
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")

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
    """Introspect a bounded context directory for Clean Architecture structure.

    Expected directory structure:
    - context_dir/
      - __init__.py (module docstring becomes objective)
      - domain/
        - models/ (entities)
        - repositories/ (repository protocols)
        - services/ (service protocols)
        - use_cases/ (use case classes, requests.py, responses.py)
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

    # Check both use_cases/ and domain/use_cases/ locations
    use_cases_dir = context_dir / "use_cases"
    if not use_cases_dir.exists():
        use_cases_dir = context_dir / "domain" / "use_cases"

    # Parse requests and responses from dedicated files
    requests = parse_python_classes_from_file(use_cases_dir / "requests.py")
    responses = parse_python_classes_from_file(use_cases_dir / "responses.py")

    # Parse use cases, excluding requests.py and responses.py
    use_cases = parse_python_classes(
        use_cases_dir,
        exclude_files=["requests.py", "responses.py"],
    )

    return BoundedContextInfo(
        slug=context_dir.name,
        entities=parse_python_classes(context_dir / "domain" / "models"),
        use_cases=use_cases,
        requests=requests,
        responses=responses,
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
