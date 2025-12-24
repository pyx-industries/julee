"""Python code introspection parser.

Parses Python source files using AST to extract class information
for Clean Architecture bounded contexts.

Note: Imports from julee.shared.domain are done lazily within functions
to avoid circular imports, since use_cases import from this module.
"""

import ast
import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from julee.shared.domain.models.code_info import (
        BoundedContextInfo,
        ClassInfo,
        FieldInfo,
        MethodInfo,
        PipelineInfo,
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


def _extract_class_fields(class_node: ast.ClassDef) -> list["FieldInfo"]:
    """Extract field information from a class definition.

    Handles:
    - Simple class attributes with type annotations
    - Pydantic Field() defaults
    - Regular default values
    """
    from julee.shared.domain.models.code_info import FieldInfo

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


def _extract_class_methods(class_node: ast.ClassDef) -> list["MethodInfo"]:
    """Extract method information from a class definition.

    Extracts public methods (not starting with _) including:
    - Regular methods
    - Async methods
    - Method signatures and docstrings
    """
    from julee.shared.domain.models.code_info import MethodInfo

    methods = []
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
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


def _parse_class_node(class_node: ast.ClassDef, file_name: str) -> "ClassInfo":
    """Parse a class AST node into ClassInfo with full details."""
    from julee.shared.domain.models.code_info import ClassInfo

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
) -> list["ClassInfo"]:
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


def parse_python_classes_from_file(file_path: Path) -> list["ClassInfo"]:
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


def parse_bounded_context(context_dir: Path) -> "BoundedContextInfo | None":
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
    return _parse_bounded_context_cached(str(context_dir))


@functools.lru_cache(maxsize=64)
def _parse_bounded_context_cached(context_dir_str: str) -> "BoundedContextInfo | None":
    """Cached implementation of parse_bounded_context.

    Uses string path for hashability with lru_cache.
    """
    from julee.shared.domain.models.code_info import BoundedContextInfo

    context_dir = Path(context_dir_str)

    if not context_dir.exists() or not context_dir.is_dir():
        return None

    init_file = context_dir / "__init__.py"
    objective, full_docstring = parse_module_docstring(init_file)

    # Check both use_cases/ and domain/use_cases/ locations
    use_cases_dir = context_dir / "use_cases"
    if not use_cases_dir.exists():
        use_cases_dir = context_dir / "domain" / "use_cases"

    # Parse all classes from use_cases directory
    all_classes = parse_python_classes(use_cases_dir)

    # Filter classes into categories based on naming conventions:
    # - *Request classes are requests
    # - *Response classes are responses
    # - *UseCase classes are use cases
    # - Other classes (like *Item) are auxiliary
    requests = [c for c in all_classes if c.name.endswith("Request")]
    responses = [c for c in all_classes if c.name.endswith("Response")]
    use_cases = [c for c in all_classes if c.name.endswith("UseCase")]

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
) -> list["BoundedContextInfo"]:
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


# =============================================================================
# PIPELINE PARSING
# =============================================================================


def _get_decorator_names(decorators: list[ast.expr]) -> list[str]:
    """Extract decorator names from a list of decorator nodes.

    Handles:
    - Simple decorators: @foo -> "foo"
    - Attribute decorators: @workflow.defn -> "workflow.defn"
    - Call decorators: @foo() -> "foo"
    """
    names = []
    for dec in decorators:
        try:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(ast.unparse(dec))
            elif isinstance(dec, ast.Call):
                # Handle @decorator() syntax
                if isinstance(dec.func, ast.Name):
                    names.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    names.append(ast.unparse(dec.func))
        except Exception:
            pass
    return names


def _has_decorator(
    node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, decorator_name: str
) -> bool:
    """Check if a class or function has a specific decorator."""
    decorator_names = _get_decorator_names(node.decorator_list)
    return decorator_name in decorator_names


def _find_method(
    class_node: ast.ClassDef, method_name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find a method by name in a class definition."""
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name == method_name:
                return node
    return None


def _method_delegates_to_use_case(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[bool, str | None]:
    """Analyze if a method delegates to a UseCase.

    Looks for patterns like:
    - use_case = SomeUseCase(...)
    - return await use_case.execute(...)
    - result = await use_case.execute(...)

    Returns:
        Tuple of (delegates, use_case_name)
    """
    from julee.shared.domain.doctrine_constants import USE_CASE_SUFFIX

    use_case_instantiated: str | None = None
    use_case_called = False

    for node in ast.walk(method_node):
        # Look for UseCase instantiation: use_case = FooUseCase(...)
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    class_name = node.value.func.id
                    if class_name.endswith(USE_CASE_SUFFIX):
                        use_case_instantiated = class_name

        # Look for UseCase.execute() call
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute):
                    if call.func.attr == "execute":
                        use_case_called = True

    delegates = use_case_instantiated is not None and use_case_called
    return delegates, use_case_instantiated


def _method_calls_method(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
    target_method: str,
) -> bool:
    """Check if a method calls self.{target_method}().

    Looks for patterns like:
    - await self.run_next(...)
    - self.run_next(...)
    - result = await self.run_next(...)

    Args:
        method_node: The method to analyze
        target_method: Name of the method being called (e.g., "run_next")

    Returns:
        True if the method calls self.{target_method}()
    """
    for node in ast.walk(method_node):
        call_node = None

        # Handle await self.method(...)
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                call_node = node.value
        # Handle self.method(...)
        elif isinstance(node, ast.Call):
            call_node = node

        if call_node and isinstance(call_node.func, ast.Attribute):
            if call_node.func.attr == target_method:
                # Check if it's self.method
                if isinstance(call_node.func.value, ast.Name):
                    if call_node.func.value.id == "self":
                        return True

    return False


def _method_sets_dispatches(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Check if a method sets dispatches on a response.

    Looks for patterns like:
    - response.dispatches = ...
    - result.dispatches = ...

    Args:
        method_node: The method to analyze

    Returns:
        True if the method sets .dispatches on any object
    """
    for node in ast.walk(method_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if target.attr == "dispatches":
                        return True

    return False


def _parse_pipeline_class(
    class_node: ast.ClassDef,
    file_path: str,
    bounded_context: str = "",
):
    """Parse a class AST node into PipelineInfo if it's a pipeline.

    A class is considered a pipeline if it:
    1. Has name ending with 'Pipeline', OR
    2. Has @workflow.defn decorator

    Args:
        class_node: The AST class definition
        file_path: Path to the source file
        bounded_context: Name of the bounded context

    Returns:
        PipelineInfo if class is a pipeline, None otherwise
    """
    from julee.shared.domain.doctrine_constants import PIPELINE_SUFFIX
    from julee.shared.domain.models.code_info import MethodInfo, PipelineInfo

    # Check if this is a pipeline class
    is_pipeline_by_name = class_node.name.endswith(PIPELINE_SUFFIX)
    has_workflow_decorator = _has_decorator(class_node, "workflow.defn")

    if not is_pipeline_by_name and not has_workflow_decorator:
        return None

    # Extract docstring
    docstring = ast.get_docstring(class_node) or ""
    first_line = docstring.split("\n")[0].strip() if docstring else ""

    # Check for run method
    run_method = _find_method(class_node, "run")
    has_run_method = run_method is not None
    has_run_decorator = False
    delegates_to_use_case = False
    wrapped_use_case: str | None = None

    if run_method:
        has_run_decorator = _has_decorator(run_method, "workflow.run")
        delegates_to_use_case, wrapped_use_case = _method_delegates_to_use_case(
            run_method
        )

    # Check for run_next() pattern
    run_next_method = _find_method(class_node, "run_next")
    has_run_next_method = run_next_method is not None
    run_next_has_workflow_decorator = False
    run_calls_run_next = False
    sets_dispatches_on_response = False

    if run_next_method:
        run_next_has_workflow_decorator = _has_decorator(
            run_next_method, "workflow.run"
        )

    if run_method:
        run_calls_run_next = _method_calls_method(run_method, "run_next")
        sets_dispatches_on_response = _method_sets_dispatches(run_method)

    # Extract methods (same logic as _extract_class_methods but we want run too)
    methods = []
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            params = [arg.arg for arg in node.args.args if arg.arg != "self"]
            method_doc = ast.get_docstring(node) or ""
            methods.append(
                MethodInfo(
                    name=node.name,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    parameters=params,
                    return_type=_get_annotation_str(node.returns),
                    docstring=method_doc.split("\n")[0].strip() if method_doc else "",
                )
            )

    return PipelineInfo(
        name=class_node.name,
        docstring=first_line,
        file=file_path,
        bounded_context=bounded_context,
        has_workflow_decorator=has_workflow_decorator,
        has_run_decorator=has_run_decorator,
        has_run_method=has_run_method,
        wrapped_use_case=wrapped_use_case,
        delegates_to_use_case=delegates_to_use_case,
        methods=methods,
        # run_next() pattern
        has_run_next_method=has_run_next_method,
        run_next_has_workflow_decorator=run_next_has_workflow_decorator,
        run_calls_run_next=run_calls_run_next,
        sets_dispatches_on_response=sets_dispatches_on_response,
    )


def parse_pipelines_from_file(
    file_path: Path,
    bounded_context: str = "",
) -> list[PipelineInfo]:
    """Extract pipeline information from a Python file.

    Args:
        file_path: Path to the Python file
        bounded_context: Name of the bounded context

    Returns:
        List of PipelineInfo objects
    """
    if not file_path.exists():
        return []

    pipelines = []
    try:
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                pipeline = _parse_pipeline_class(node, file_path.name, bounded_context)
                if pipeline:
                    pipelines.append(pipeline)
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Could not parse {file_path}: {e}")

    return sorted(pipelines, key=lambda p: p.name)


def parse_pipelines_from_bounded_context(context_dir: Path) -> list[PipelineInfo]:
    """Extract pipelines from a bounded context.

    Looks for pipelines at:
    - {context}/apps/worker/pipelines.py (canonical location)
    - {context}/apps/worker/*.py (fallback)

    Args:
        context_dir: Path to the bounded context directory

    Returns:
        List of PipelineInfo objects
    """
    from julee.shared.domain.doctrine_constants import PIPELINE_LOCATION

    pipelines = []
    bounded_context = context_dir.name

    # Check canonical location first
    canonical_path = context_dir / PIPELINE_LOCATION
    if canonical_path.exists():
        pipelines.extend(parse_pipelines_from_file(canonical_path, bounded_context))
    else:
        # Fallback: scan apps/worker/ directory
        worker_dir = context_dir / "apps" / "worker"
        if worker_dir.exists():
            for py_file in worker_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                pipelines.extend(parse_pipelines_from_file(py_file, bounded_context))

    return sorted(pipelines, key=lambda p: p.name)
