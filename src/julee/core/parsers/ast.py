"""Python code introspection using griffe.

Parses Python source files to extract class information for Clean Architecture
bounded contexts. Uses griffe for static analysis without importing source modules.

Pipeline analysis uses stdlib ast for method body inspection, as griffe does
not analyse statement-level patterns inside method bodies.

Note: Lazy imports within functions avoid circular imports, since use_cases
import from this module.
"""

import ast
import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import griffe

if TYPE_CHECKING:
    from julee.core.entities.code_info import (
        BoundedContextInfo,
        ClassInfo,
    )
    from julee.core.entities.pipeline import Pipeline

logger = logging.getLogger(__name__)


# =============================================================================
# GRIFFE-BASED CLASS EXTRACTION
# =============================================================================


def _griffe_load_file(py_file: Path) -> griffe.Module | None:
    """Load a single Python file with griffe (no imports)."""
    try:
        return griffe.load(
            py_file.stem,
            search_paths=[str(py_file.parent)],
            allow_inspection=False,
        )
    except Exception as e:
        logger.warning(f"Could not parse {py_file}: {e}")
        return None


def _griffe_class_to_classinfo(cls: griffe.Class, file_name: str) -> "ClassInfo":
    from julee.core.entities.code_info import (
        ClassInfo,
        FieldInfo,
        MethodInfo,
        ParameterInfo,
    )

    docstring = cls.docstring.value.split("\n")[0].strip() if cls.docstring else ""

    fields = [
        FieldInfo(
            name=member.name,
            type_annotation=str(member.annotation) if member.annotation else "",
            default=str(member.value) if member.value else None,
        )
        for member in cls.members.values()
        if isinstance(member, griffe.Attribute) and member.annotation is not None
    ]

    methods = []
    for member in cls.members.values():
        if not isinstance(member, griffe.Function) or member.name.startswith("_"):
            continue
        params = [
            ParameterInfo(
                name=p.name,
                type_annotation=str(p.annotation) if p.annotation else "",
            )
            for p in member.parameters
            if p.name != "self"
            and p.kind
            not in (
                griffe.ParameterKind.var_positional,
                griffe.ParameterKind.var_keyword,
            )
        ]
        method_doc = (
            member.docstring.value.split("\n")[0].strip() if member.docstring else ""
        )
        methods.append(
            MethodInfo(
                name=member.name,
                is_async="async" in member.labels,
                parameters=params,
                return_type=str(member.returns) if member.returns else "",
                docstring=method_doc,
            )
        )

    return ClassInfo(
        name=cls.name,
        docstring=docstring,
        file=file_name,
        bases=[str(b) for b in cls.bases],
        fields=fields,
        methods=methods,
    )


def _classes_from_file(py_file: Path, relative_to: Path) -> list["ClassInfo"]:
    """Parse all classes from a file, with path relative to relative_to."""
    try:
        rel = str(py_file.relative_to(relative_to))
    except ValueError:
        rel = py_file.name

    module = _griffe_load_file(py_file)
    if module is None:
        return []

    return [_griffe_class_to_classinfo(cls, rel) for cls in module.classes.values()]


def parse_python_classes(
    directory: Path,
    recursive: bool = True,
    exclude_tests: bool = True,
    exclude_files: list[str] | None = None,
) -> list["ClassInfo"]:
    """Extract class information from Python files in a directory.

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
        if py_file.name.startswith("_"):
            continue
        if exclude_tests and (
            py_file.name.startswith("test_") or "/tests/" in str(py_file)
        ):
            continue
        if py_file.name in exclude_files:
            continue
        for cls in _classes_from_file(py_file, directory):
            if exclude_tests and cls.name.startswith("Test"):
                continue
            classes.append(cls)

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
    return sorted(_classes_from_file(file_path, file_path.parent), key=lambda c: c.name)


def parse_module_docstring(module_path: Path) -> tuple[str | None, str | None]:
    """Extract module docstring from a Python file.

    Args:
        module_path: Path to Python file

    Returns:
        Tuple of (first_line, full_docstring) or (None, None) if not found
    """
    if not module_path.exists():
        return None, None

    module = _griffe_load_file(module_path)
    if module is None:
        return None, None

    if module.docstring:
        full = module.docstring.value
        return full.split("\n")[0].strip(), full

    return None, None


def _imported_class_names(directory: Path) -> set[str]:
    """Return names imported into any non-private file in directory.

    Scans import statements (not class definitions) so that re-exported
    Request/Response classes satisfy doctrine checks even when they are
    defined outside the use_cases directory (e.g. in _generated/).
    """
    if not directory.exists():
        return set()
    names: set[str] = set()
    for py_file in directory.glob("**/*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            for alias in node.names:
                local_name = alias.asname if alias.asname else alias.name
                names.add(local_name.split(".")[-1])
    return names


def _resolve_layer_path(context_dir: Path, path_tuple: tuple[str, ...]) -> Path:
    result = context_dir
    for part in path_tuple:
        result = result / part
    return result


@functools.lru_cache(maxsize=64)
def _parse_bounded_context_cached(context_dir_str: str) -> "BoundedContextInfo | None":
    from julee.core.doctrine_constants import USE_CASES_PATH
    from julee.core.entities.code_info import BoundedContextInfo

    context_dir = Path(context_dir_str)
    if not context_dir.exists() or not context_dir.is_dir():
        return None

    objective, full_docstring = parse_module_docstring(context_dir / "__init__.py")

    use_cases_dir = _resolve_layer_path(context_dir, USE_CASES_PATH)
    # ADR 001 nested solution structure uses domain/models/, domain/repositories/,
    # and domain/services/
    domain_models_dir = context_dir / "domain" / "models"
    domain_repositories_dir = context_dir / "domain" / "repositories"
    domain_services_dir = context_dir / "domain" / "services"

    all_classes = parse_python_classes(use_cases_dir)
    defined_names = {c.name for c in all_classes}

    # Also collect names imported into use_cases files so that Request/Response
    # classes defined elsewhere (e.g. _generated/) satisfy doctrine checks.
    # Only augments Request/Response — UseCase imports are typically dependencies,
    # not definitions, so they must remain class-definition-only.
    imported = _imported_class_names(use_cases_dir)
    for name in sorted(imported - defined_names):
        if not name.startswith("_") and name.endswith(("Request", "Response")):
            from julee.core.entities.code_info import ClassInfo

            all_classes.append(ClassInfo(name=name))

    requests = [c for c in all_classes if c.name.endswith("Request")]
    responses = [c for c in all_classes if c.name.endswith("Response")]
    use_cases = [c for c in all_classes if c.name.endswith("UseCase")]

    all_service_classes = parse_python_classes(domain_services_dir)
    service_protocols = [c for c in all_service_classes if c.name.endswith("Service")]
    handler_protocols = [c for c in all_service_classes if c.name.endswith("Handler")]

    return BoundedContextInfo(
        slug=context_dir.name,
        entities=parse_python_classes(domain_models_dir),
        use_cases=use_cases,
        requests=requests,
        responses=responses,
        repository_protocols=parse_python_classes(domain_repositories_dir),
        service_protocols=service_protocols,
        handler_protocols=handler_protocols,
        has_infrastructure=(context_dir / "infrastructure").exists(),
        code_dir=context_dir.name,
        objective=objective,
        docstring=full_docstring,
    )


def parse_bounded_context(context_dir: Path) -> "BoundedContextInfo | None":
    """Introspect a bounded context directory for Clean Architecture structure."""
    return _parse_bounded_context_cached(str(context_dir))


def _has_bounded_context_structure(context_dir: Path) -> bool:
    from julee.core.doctrine_constants import ENTITIES_PATH, USE_CASES_PATH

    for path_tuple in [ENTITIES_PATH, USE_CASES_PATH]:
        path = context_dir
        for part in path_tuple:
            path = path / part
        if path.exists():
            return True
    return False


def scan_bounded_contexts(
    src_dir: Path,
    exclude: list[str] | None = None,
) -> list["BoundedContextInfo"]:
    """Scan a source directory for all bounded contexts."""
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
        if not _has_bounded_context_structure(context_dir):
            continue
        context_info = parse_bounded_context(context_dir)
        if context_info:
            contexts.append(context_info)
            logger.info(
                f"Introspected bounded context '{context_info.slug}': {context_info.summary()}"
            )

    return contexts


# =============================================================================
# PIPELINE PARSING (stdlib ast — griffe does not analyse method bodies)
# =============================================================================


def _get_decorator_names(decorators: list[ast.expr]) -> list[str]:
    names = []
    for dec in decorators:
        try:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(ast.unparse(dec))
            elif isinstance(dec, ast.Call):
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
    return decorator_name in _get_decorator_names(node.decorator_list)


def _find_method(
    class_node: ast.ClassDef, method_name: str
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name == method_name:
                return node
    return None


def _method_delegates_to_use_case(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[bool, str | None]:
    from julee.core.doctrine_constants import USE_CASE_SUFFIX

    use_case_instantiated: str | None = None
    use_case_called = False

    for node in ast.walk(method_node):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and isinstance(
                node.value.func, ast.Name
            ):
                if node.value.func.id.endswith(USE_CASE_SUFFIX):
                    use_case_instantiated = node.value.func.id
        if isinstance(node, ast.Await):
            if isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "execute":
                    use_case_called = True

    return use_case_instantiated is not None and use_case_called, use_case_instantiated


def _method_calls_method(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
    target_method: str,
) -> bool:
    for node in ast.walk(method_node):
        call_node = None
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            call_node = node.value
        elif isinstance(node, ast.Call):
            call_node = node
        if call_node and isinstance(call_node.func, ast.Attribute):
            if call_node.func.attr == target_method:
                if (
                    isinstance(call_node.func.value, ast.Name)
                    and call_node.func.value.id == "self"
                ):
                    return True
    return False


def _method_sets_dispatches(
    method_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    for node in ast.walk(method_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == "dispatches":
                    return True
    return False


def _parse_pipeline_class(
    class_node: ast.ClassDef,
    file_path: str,
    bounded_context: str = "",
):
    from julee.core.doctrine_constants import PIPELINE_SUFFIX
    from julee.core.entities.code_info import MethodInfo, ParameterInfo
    from julee.core.entities.pipeline import Pipeline

    is_pipeline_by_name = class_node.name.endswith(PIPELINE_SUFFIX)
    has_workflow_decorator = _has_decorator(class_node, "workflow.defn")
    if not is_pipeline_by_name and not has_workflow_decorator:
        return None

    docstring = ast.get_docstring(class_node) or ""
    first_line = docstring.split("\n")[0].strip() if docstring else ""

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

    methods = []
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            params = [
                ParameterInfo(
                    name=arg.arg,
                    type_annotation=(
                        ast.unparse(arg.annotation) if arg.annotation else ""
                    ),
                )
                for arg in node.args.args
                if arg.arg != "self"
            ]
            method_doc = ast.get_docstring(node) or ""
            methods.append(
                MethodInfo(
                    name=node.name,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    parameters=params,
                    return_type=ast.unparse(node.returns) if node.returns else "",
                    docstring=method_doc.split("\n")[0].strip() if method_doc else "",
                )
            )

    return Pipeline(
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
        has_run_next_method=has_run_next_method,
        run_next_has_workflow_decorator=run_next_has_workflow_decorator,
        run_calls_run_next=run_calls_run_next,
        sets_dispatches_on_response=sets_dispatches_on_response,
    )


def parse_pipelines_from_file(
    file_path: Path,
    bounded_context: str = "",
) -> "list[Pipeline]":
    """Extract pipeline information from a Python file."""
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


def parse_pipelines_from_bounded_context(context_dir: Path) -> "list[Pipeline]":
    """Extract pipelines from a bounded context."""
    from julee.core.doctrine_constants import PIPELINE_LOCATION

    pipelines = []
    bounded_context = context_dir.name

    canonical_path = context_dir / PIPELINE_LOCATION
    if canonical_path.exists():
        pipelines.extend(parse_pipelines_from_file(canonical_path, bounded_context))
    else:
        worker_dir = context_dir / "apps" / "worker"
        if worker_dir.exists():
            for py_file in worker_dir.glob("*.py"):
                if not py_file.name.startswith("_"):
                    pipelines.extend(
                        parse_pipelines_from_file(py_file, bounded_context)
                    )

    return sorted(pipelines, key=lambda p: p.name)
