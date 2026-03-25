"""CRUD use case generator for julee applications.

Generates doctrine-compliant Get, List, Create, and Update use case classes
for a given entity and repository, writing plain Python into a .generated/
directory. Generated files are gitignored and regenerated via make generate-crud.

Usage::

    uv run python -m julee.core.use_cases.generate_crud \\
        --entity Assembly \\
        --entity-module julee.contrib.ceap.domain.models \\
        --repo AssemblyRepository \\
        --repo-module julee.contrib.ceap.domain.repositories.assembly \\
        --id-field assembly_id \\
        --create-fields "status:AssemblyStatus execution_id:str" \\
        --update-fields "status:AssemblyStatus assembled_document_id:str|None" \\
        --out src/julee/contrib/ceap/.generated/use_cases/
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

import inflect as inflect_lib

_inflect = inflect_lib.engine()

# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------


def _to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s).lower()


def _pluralize(word: str) -> str:
    """Pluralise a snake_case word using inflect."""
    return _inflect.plural(word)


def _parse_fields(fields_str: str | None) -> list[tuple[str, str]]:
    """Parse 'field:Type field2:Type2' into [(name, type), ...]."""
    if not fields_str:
        return []
    result = []
    for token in fields_str.split():
        name, _, type_ = token.partition(":")
        result.append((name.strip(), (type_ or "str").strip()))
    return result


def _needs_typing(all_fields: list[tuple[str, str]], include_create: bool) -> set[str]:
    """Return typing names (Any, Optional, etc.) referenced in field types."""
    needed = set()
    if include_create:
        needed.add("Any")  # _build_entity always uses **kwargs: Any
    for _, t in all_fields:
        if "Any" in t:
            needed.add("Any")
        if "Optional" in t:
            needed.add("Optional")
    return needed


def _extra_entity_imports(
    all_fields: list[tuple[str, str]],
    entity_module: str,
    entity: str,
) -> list[str]:
    """Return 'from entity_module import X' lines for non-builtin types in fields.

    Handles composite annotations like list[Foo], Foo|None, dict[str, Any].
    """
    safe = {
        "str",
        "int",
        "float",
        "bool",
        "None",
        "Any",
        "Optional",
        "list",
        "dict",
        "tuple",
        "set",
        "frozenset",
    }
    extra: set[str] = set()
    for _, type_str in all_fields:
        for token in re.split(r"[\[\],| ]+", type_str):
            token = token.strip()
            if token and token not in safe and token != entity and token[0:1].isupper():
                extra.add(token)
    if not extra:
        return []
    names = ", ".join(sorted(extra))
    return [f"from {entity_module} import {names}"]


def _field_lines(fields: list[tuple[str, str]], indent: str = "    ") -> str:
    if not fields:
        return ""
    return "\n".join(f"{indent}{name}: {type_}" for name, type_ in fields)


# ---------------------------------------------------------------------------
# Section generators
# ---------------------------------------------------------------------------


def _get_section(entity: str, snake: str, id_field: str) -> str:
    return f"""\
class Get{entity}Request(BaseModel):
    \"\"\"Request for getting a {entity} by {id_field}.\"\"\"

    {id_field}: str


class Get{entity}Response(BaseModel):
    \"\"\"Response for getting a {entity}.\"\"\"

    {snake}: {entity}


class Get{entity}UseCase(GetUseCase[{entity}, {entity}Repository]):
    \"\"\"Get a {entity} by {id_field}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(self, request: Get{entity}Request) -> Get{entity}Response:
        \"\"\"Execute the get {snake} use case.\"\"\"
        entity = await self._get_by_id(request.{id_field})
        return Get{entity}Response({snake}=entity)
"""


def _list_section(
    entity: str, snake: str, plural_snake: str, plural_entity: str
) -> str:
    return f"""\
class List{plural_entity}Request(BaseModel):
    \"\"\"Request for listing all {plural_entity}.\"\"\"


class List{plural_entity}Response(BaseModel):
    \"\"\"Response for listing all {plural_entity}.\"\"\"

    {plural_snake}: list[{entity}]
    total_count: int


class List{plural_entity}UseCase(ListUseCase[{entity}, {entity}Repository]):
    \"\"\"List all {plural_entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(self, request: List{plural_entity}Request) -> List{plural_entity}Response:
        \"\"\"Execute the list {plural_snake} use case.\"\"\"
        entities = await self._list_all()
        return List{plural_entity}Response({plural_snake}=entities, total_count=len(entities))
"""


def _create_section(
    entity: str,
    snake: str,
    id_field: str,
    create_fields: list[tuple[str, str]],
) -> str:
    field_lines = _field_lines(create_fields)
    field_kwargs = "\n".join(
        f"            {name}=request.{name}," for name, _ in create_fields
    )
    return f"""\
class Create{entity}Request(BaseModel):
    \"\"\"Request for creating a {entity}.\"\"\"

{field_lines}


class Create{entity}Response(BaseModel):
    \"\"\"Response for creating a {entity}.\"\"\"

    {snake}: {entity}


class Create{entity}UseCase(CreateUseCase[{entity}, {entity}Repository]):
    \"\"\"Create a new {entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    def _build_entity(self, entity_id: str, **kwargs: Any) -> {entity}:
        \"\"\"Construct a {entity} from a generated ID and request fields.\"\"\"
        return {entity}({id_field}=entity_id, **kwargs)

    async def execute(self, request: Create{entity}Request) -> Create{entity}Response:
        \"\"\"Execute the create {snake} use case.\"\"\"
        entity = await self._create(
{field_kwargs}
        )
        return Create{entity}Response({snake}=entity)
"""


def _update_section(
    entity: str,
    snake: str,
    id_field: str,
    update_fields: list[tuple[str, str]],
) -> str:
    field_lines = _field_lines(update_fields)
    return f"""\
class Update{entity}Request(BaseModel):
    \"\"\"Request for updating a {entity}.\"\"\"

    {id_field}: str
{field_lines}


class Update{entity}Response(BaseModel):
    \"\"\"Response for updating a {entity}.\"\"\"

    {snake}: {entity}


class Update{entity}UseCase(UpdateUseCase[{entity}, {entity}Repository]):
    \"\"\"Update a {entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(self, request: Update{entity}Request) -> Update{entity}Response:
        \"\"\"Execute the update {snake} use case.\"\"\"
        entity = await self._update_by_id(
            request.{id_field},
            request.model_dump(exclude={{"{id_field}"}}),
        )
        return Update{entity}Response({snake}=entity)
"""


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate(
    *,
    entity: str,
    entity_module: str,
    repo: str,
    repo_module: str,
    id_field: str,
    create_fields: list[tuple[str, str]],
    update_fields: list[tuple[str, str]],
    include_get: bool = True,
    include_list: bool = True,
    include_create: bool = True,
    include_update: bool = True,
    out_dir: Path,
) -> Path:
    """Generate a crud_{entity_snake}.py file into out_dir."""
    snake = _to_snake(entity)
    plural_snake = _pluralize(snake)
    # Capitalise each word of the plural snake to get plural entity name
    plural_entity = "".join(w.capitalize() for w in plural_snake.split("_"))

    # Collect all fields to determine typing imports
    all_fields = create_fields + update_fields
    typing_names = _needs_typing(all_fields, include_create)

    # Base class imports
    base_classes = []
    if include_get:
        base_classes.append("GetUseCase")
    if include_list:
        base_classes.append("ListUseCase")
    if include_create:
        base_classes.append("CreateUseCase")
    if include_update:
        base_classes.append("UpdateUseCase")
    base_imports = ", ".join(["EntityNotFoundError"] + base_classes)

    # Build import block
    imports = []
    if typing_names:
        imports.append(f"from typing import {', '.join(sorted(typing_names))}")
    imports.append("from pydantic import BaseModel")
    imports.append("")
    imports.append(f"from {entity_module} import {entity}")
    for extra in _extra_entity_imports(all_fields, entity_module, entity):
        imports.append(extra)
    imports.append(f"from {repo_module} import {repo}")
    imports.append(
        f"from julee.core.use_cases.generic_crud import (\n    {base_imports},\n)"
    )

    # If the caller supplied a repo name that differs from {Entity}Repository,
    # create an alias so templates can always reference {entity}Repository.
    if repo != f"{entity}Repository":
        imports.append(f"\n{entity}Repository = {repo}")

    # Build sections
    sections = [
        f'"""Generated CRUD use cases for {entity}.\n\nDo not edit — regenerate with make generate-crud.\n"""',
        "\n".join(imports),
    ]

    if include_get:
        sections.append(_get_section(entity, snake, id_field))
    if include_list:
        sections.append(_list_section(entity, snake, plural_snake, plural_entity))
    if include_create:
        sections.append(_create_section(entity, snake, id_field, create_fields))
    if include_update:
        sections.append(_update_section(entity, snake, id_field, update_fields))

    content = "\n\n".join(sections) + "\n"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"crud_{snake}.py"
    out_file.write_text(content)

    # Format with ruff
    result = subprocess.run(
        ["uv", "run", "ruff", "format", str(out_file)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Warning: ruff format failed:\n{result.stderr}", file=sys.stderr)

    return out_file


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate CRUD use cases for a julee entity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--entity", required=True, help="Entity class name, e.g. Assembly")
    p.add_argument(
        "--entity-module",
        required=True,
        help="Dotted module path for the entity, e.g. julee.contrib.ceap.domain.models",
    )
    p.add_argument(
        "--repo",
        required=True,
        help="Repository class name, e.g. AssemblyRepository",
    )
    p.add_argument(
        "--repo-module",
        required=True,
        help="Dotted module path for the repo",
    )
    p.add_argument(
        "--id-field",
        required=True,
        help="Name of the ID field on the entity, e.g. assembly_id",
    )
    p.add_argument(
        "--create-fields",
        default=None,
        help="Space-separated 'name:Type' pairs for CreateRequest fields",
    )
    p.add_argument(
        "--update-fields",
        default=None,
        help="Space-separated 'name:Type' pairs for UpdateRequest fields (excluding id-field)",
    )
    p.add_argument("--no-get", action="store_true", help="Skip GetUseCase")
    p.add_argument("--no-list", action="store_true", help="Skip ListUseCase")
    p.add_argument("--no-create", action="store_true", help="Skip CreateUseCase")
    p.add_argument("--no-update", action="store_true", help="Skip UpdateUseCase")
    p.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output directory for the generated file",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CRUD generator CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    out_file = generate(
        entity=args.entity,
        entity_module=args.entity_module,
        repo=args.repo,
        repo_module=args.repo_module,
        id_field=args.id_field,
        create_fields=_parse_fields(args.create_fields),
        update_fields=_parse_fields(args.update_fields),
        include_get=not args.no_get,
        include_list=not args.no_list,
        include_create=not args.no_create,
        include_update=not args.no_update,
        out_dir=args.out,
    )
    print(f"Generated: {out_file}")


if __name__ == "__main__":
    main()
