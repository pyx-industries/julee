"""CRUD use case generator for julee applications.

Generates doctrine-compliant Get, List, Create, and Update use case classes
for a given entity and repository, writing plain Python into a .generated/
directory. Generated files are gitignored and regenerated via make generate-crud.

Usage::

    uv run python -m julee.core.usecases.generate_crud \\
        --entity Assembly \\
        --entity-module julee.contrib.ceap.domain.models \\
        --repo AssemblyRepository \\
        --repo-module julee.contrib.ceap.domain.repositories.assembly \\
        --id-field assembly_id \\
        --create-fields "status:AssemblyStatus execution_id:str" \\
        --update-fields "status:AssemblyStatus assembled_document_id:str|None" \\
        --out src/julee/contrib/ceap/.generated/usecases/
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
        # A field may carry a default ('SystemType = SystemType.INTERNAL').
        # Only the annotation names a type; the default names a value, and
        # its leading dotted part is already imported by the annotation.
        annotation = type_str.partition("=")[0]
        for token in re.split(r"[\[\],| ]+", annotation):
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


def _optional_field_lines(fields: list[tuple[str, str]], indent: str = "    ") -> str:
    """Render fields as optional, so an update can name only what it changes.

    A type that already admits None gains a default; anything else is widened
    to ``T | None`` first. Unset is what the use case acts on, not None, so a
    field left out is left alone while one passed as None is cleared.
    """
    if not fields:
        return ""
    lines = []
    for name, type_ in fields:
        # Any default the caller wrote is dropped: the default that matters on
        # an update is None, standing for "not mentioned".
        annotation = type_.partition("=")[0].strip()
        if "None" not in annotation:
            annotation = f"{annotation} | None"
        lines.append(f"{indent}{name}: {annotation} = None")
    return "\n".join(lines)


def _message_names(
    entity: str,
    plural_entity: str,
    include_get: bool,
    include_list: bool,
    include_create: bool,
    include_update: bool,
    include_delete: bool,
) -> list[str]:
    """Every message class the use case module has to import."""
    names: list[str] = []
    if include_get:
        names += [f"Get{entity}Request", f"Get{entity}Response"]
    if include_list:
        names += [f"List{plural_entity}Request", f"List{plural_entity}Response"]
    if include_create:
        names += [f"Create{entity}Request", f"Create{entity}Response"]
    if include_update:
        names += [f"Update{entity}Request", f"Update{entity}Response"]
    if include_delete:
        names += [f"Delete{entity}Request", f"Delete{entity}Response"]
    return names


def _write(directory: Path, name: str, sections: list[str]) -> Path:
    """Write one generated module, making its package if need be."""
    directory.mkdir(parents=True, exist_ok=True)
    init = directory / "__init__.py"
    if not init.exists():
        init.write_text(f'"""{directory.name.capitalize()}."""\n')
    path = directory / name
    path.write_text("\n\n".join(sections) + "\n")
    return path


def _tidy(*paths: Path) -> None:
    """Hand the generated files to ruff, and say so if it refuses.

    Both passes, not just the formatter. The emitted import block
    carries names a given entity may not use and is in the order the
    generator happened to build it, so without ``check --fix`` the
    output fails the lint every kit runs — which is why the committed
    files had tidier imports than the generator ever wrote. Generated
    code that needs a human to finish it is not generated.
    """
    for argv in (
        ["uv", "run", "ruff", "check", "--fix", "--quiet"],
        ["uv", "run", "ruff", "format", "--quiet"],
    ):
        result = subprocess.run(
            [*argv, *[str(path) for path in paths]], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(
                f"Warning: {argv[2]} {argv[3]} failed:\n{result.stderr}",
                file=sys.stderr,
            )


# ---------------------------------------------------------------------------
# Section generators
#
# Each comes in two halves. The messages are pydantic and land in dtos/;
# the use case speaks the domain and lands in usecases/, importing the
# messages by name and pydantic never.
# ---------------------------------------------------------------------------


def _get_messages(entity: str, snake: str, id_field: str) -> str:
    return f"""\
class Get{entity}Request(BaseModel):
    \"\"\"Request for getting a {entity} by {id_field}.\"\"\"

    {id_field}: str


class Get{entity}Response(BaseModel):
    \"\"\"Response for getting a {entity}.\"\"\"

    {snake}: {entity}
"""


def _get_usecase(entity: str, snake: str, id_field: str) -> str:
    return f"""\
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


def _list_messages(entity: str, plural_snake: str, plural_entity: str) -> str:
    return f"""\
class List{plural_entity}Request(BaseModel):
    \"\"\"Request for listing all {plural_entity}.\"\"\"


class List{plural_entity}Response(BaseModel):
    \"\"\"Response for listing all {plural_entity}.\"\"\"

    {plural_snake}: list[{entity}]
    total_count: int
"""


def _list_usecase(
    entity: str, snake: str, plural_snake: str, plural_entity: str
) -> str:
    return f"""\
class List{plural_entity}UseCase(ListUseCase[{entity}, {entity}Repository]):
    \"\"\"List all {plural_entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(
        self, request: List{plural_entity}Request
    ) -> List{plural_entity}Response:
        \"\"\"Execute the list {plural_snake} use case.\"\"\"
        entities = await self._list_all()
        return List{plural_entity}Response(
            {plural_snake}=entities, total_count=len(entities)
        )
"""


def _create_messages(
    entity: str, snake: str, create_fields: list[tuple[str, str]]
) -> str:
    field_lines = _field_lines(create_fields)
    return f"""\
class Create{entity}Request(BaseModel):
    \"\"\"Request for creating a {entity}.\"\"\"

{field_lines}


class Create{entity}Response(BaseModel):
    \"\"\"Response for creating a {entity}.\"\"\"

    {snake}: {entity}
"""


def _names_itself(id_field: str, create_fields: list[tuple[str, str]]) -> bool:
    """Whether the entity derives its own id when none is given.

    An id among the create fields carrying a default says the caller
    may leave it out, and something else settles it. c4's Relationship
    is named after its two ends and its DynamicStep after its sequence
    and number, so there is nothing to choose and nothing to mint.

    Args:
        id_field: The field the entity is identified by
        create_fields: The create request's fields, with any defaults

    Returns:
        True if the id is optional on the way in
    """
    return any(
        name == id_field and "=" in annotation for name, annotation in create_fields
    )


def _create_usecase(
    entity: str,
    snake: str,
    id_field: str,
    create_fields: list[tuple[str, str]],
) -> str:
    # An id among the create fields is a natural key the caller already knows,
    # so it is passed as the entity id rather than as another field; passing
    # it both ways would hand _build_entity the same keyword twice.
    caller_supplies_id = any(name == id_field for name, _ in create_fields)
    kwarg_names = [name for name, _ in create_fields if name != id_field]
    if caller_supplies_id:
        kwarg_names.insert(0, "entity_id")
    field_kwargs = "\n".join(
        f"            {name}=request.{id_field if name == 'entity_id' else name},"
        for name in kwarg_names
    )
    # An entity that names itself must not be handed the field empty:
    # a Slug refuses an empty string before any default_factory could
    # derive one, so the field is left out rather than passed blank.
    if _names_itself(id_field, create_fields):
        derives_its_own = f"""

        A request that names no {id_field} leaves the entity to work
        one out, so the field is left out rather than passed empty.
        \"\"\"
        if not entity_id:
            return {entity}(**kwargs)
"""
    else:
        derives_its_own = '"""'
    return f"""\
class Create{entity}UseCase(CreateUseCase[{entity}, {entity}Repository]):
    \"\"\"Create a new {entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    def _build_entity(self, entity_id: str, **kwargs: Any) -> {entity}:
        \"\"\"Construct a {entity} from a generated ID and request fields.{derives_its_own}
        return {entity}({id_field}=entity_id, **kwargs)

    async def execute(self, request: Create{entity}Request) -> Create{entity}Response:
        \"\"\"Execute the create {snake} use case.\"\"\"
        entity = await self._create(
{field_kwargs}
        )
        return Create{entity}Response({snake}=entity)
"""


def _update_messages(
    entity: str,
    snake: str,
    id_field: str,
    update_fields: list[tuple[str, str]],
) -> str:
    field_lines = _optional_field_lines(update_fields)
    return f"""\
class Update{entity}Request(BaseModel):
    \"\"\"Request for updating a {entity}.

    Every field but {id_field} is optional: name the ones to change and the
    rest are left as they are.
    \"\"\"

    {id_field}: str
{field_lines}

    def changes(self) -> dict[str, Any]:
        \"\"\"The fields the caller named, without the {id_field}.

        Which fields a caller named is a pydantic question — it is the
        difference between a field left out and one set to its default
        — so the message answers it. A use case asks for the changes
        and never learns how they were worked out.
        \"\"\"
        return self.model_dump(exclude={{"{id_field}"}}, exclude_unset=True)


class Update{entity}Response(BaseModel):
    \"\"\"Response for updating a {entity}.\"\"\"

    {snake}: {entity}
"""


def _update_usecase(entity: str, snake: str, id_field: str) -> str:
    return f"""\
class Update{entity}UseCase(UpdateUseCase[{entity}, {entity}Repository]):
    \"\"\"Update a {entity}.\"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(self, request: Update{entity}Request) -> Update{entity}Response:
        \"\"\"Execute the update {snake} use case.\"\"\"
        entity = await self._update_by_id(request.{id_field}, request.changes())
        return Update{entity}Response({snake}=entity)
"""


def _delete_messages(entity: str, id_field: str) -> str:
    return f"""\
class Delete{entity}Request(BaseModel):
    \"\"\"Request for deleting a {entity} by {id_field}.\"\"\"

    {id_field}: str


class Delete{entity}Response(BaseModel):
    \"\"\"Response for deleting a {entity}.\"\"\"

    deleted: bool
"""


def _delete_usecase(entity: str, snake: str, id_field: str) -> str:
    return f"""\
class Delete{entity}UseCase(DeleteUseCase[{entity}, {entity}Repository]):
    \"\"\"Delete a {entity} by {id_field}.

    Reports whether anything was deleted rather than raising, since
    \"it was already gone\" is the outcome the caller asked for.
    \"\"\"

    def __init__(self, repo: {entity}Repository) -> None:
        \"\"\"Initialise with the {snake} repository.\"\"\"
        super().__init__(repo)

    async def execute(self, request: Delete{entity}Request) -> Delete{entity}Response:
        \"\"\"Execute the delete {snake} use case.\"\"\"
        deleted = await self._delete_by_id(request.{id_field})
        return Delete{entity}Response(deleted=deleted)
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
    include_delete: bool = False,
    plural: str | None = None,
    out_dir: Path,
) -> Path:
    """Generate a bounded context's CRUD for one entity.

    Writes two files, because the rings they belong to are different:
    ``dtos/crud_{snake}.py`` holds the messages and is the only one
    that imports pydantic, and ``usecases/crud_{snake}.py`` holds the
    use cases and imports the messages by name.

    Args:
        out_dir: The bounded context package, not a layer inside it.
            Both directories are created beneath it.

    Returns:
        The use case file, which is what a caller usually wants to name
    """
    snake = _to_snake(entity)
    # inflect knows English, which is not always the same as knowing what
    # a domain calls several of something: it makes "personae" of a
    # persona, where everyone writing the documentation says "personas".
    # The generated names are a kit's public API, so the caller can say.
    plural_snake = _to_snake(plural) if plural else _pluralize(snake)
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
    if include_delete:
        base_classes.append("DeleteUseCase")
    base_imports = ", ".join(["EntityNotFoundError"] + base_classes)

    # The messages: pydantic, the entity they carry, and nothing else.
    message_imports = []
    typing_for_messages = set(typing_names)
    if include_update:
        typing_for_messages.add("Any")
    if typing_for_messages:
        message_imports.append(
            f"from typing import {', '.join(sorted(typing_for_messages))}"
        )
    message_imports.append("from pydantic import BaseModel")
    message_imports.append("")
    message_imports.append(f"from {entity_module} import {entity}")
    for extra in _extra_entity_imports(all_fields, entity_module, entity):
        message_imports.append(extra)

    messages = [
        f'"""Generated CRUD messages for {entity}.\n\nDo not edit — regenerate with generate-crud.sh.\n"""',
        "\n".join(message_imports),
    ]
    if include_get:
        messages.append(_get_messages(entity, snake, id_field))
    if include_list:
        messages.append(_list_messages(entity, plural_snake, plural_entity))
    if include_create:
        messages.append(_create_messages(entity, snake, create_fields))
    if include_update:
        messages.append(_update_messages(entity, snake, id_field, update_fields))
    if include_delete:
        messages.append(_delete_messages(entity, id_field))

    # The use cases: the domain, the ports, the messages by name.
    names = sorted(
        _message_names(
            entity,
            plural_entity,
            include_get,
            include_list,
            include_create,
            include_update,
            include_delete,
        )
    )
    imports = []
    if include_create:
        imports.append("from typing import Any")
        imports.append("")
    imports.append(f"from {entity_module} import {entity}")
    for extra in _extra_entity_imports(all_fields, entity_module, entity):
        imports.append(extra)
    imports.append(f"from {repo_module} import {repo}")
    # Relative, because the messages sit beside the use cases in the
    # same bounded context and the generator has no business working
    # out what that context is called.
    imports.append(
        f"from ..dtos.crud_{snake} import (\n    " + ",\n    ".join(names) + ",\n)"
    )
    imports.append(
        f"from julee.core.usecases.generic_crud import (\n    {base_imports},\n)"
    )

    # If the caller supplied a repo name that differs from {Entity}Repository,
    # create an alias so templates can always reference {entity}Repository.
    if repo != f"{entity}Repository":
        imports.append(f"\n{entity}Repository = {repo}")

    sections = [
        f'"""Generated CRUD use cases for {entity}.\n\nDo not edit — regenerate with generate-crud.sh.\n"""',
        "\n".join(imports),
    ]
    if include_get:
        sections.append(_get_usecase(entity, snake, id_field))
    if include_list:
        sections.append(_list_usecase(entity, snake, plural_snake, plural_entity))
    if include_create:
        sections.append(_create_usecase(entity, snake, id_field, create_fields))
    if include_update:
        sections.append(_update_usecase(entity, snake, id_field))
    if include_delete:
        sections.append(_delete_usecase(entity, snake, id_field))

    dtos_file = _write(out_dir / "dtos", f"crud_{snake}.py", messages)
    out_file = _write(out_dir / "usecases", f"crud_{snake}.py", sections)
    _tidy(dtos_file, out_file)
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
        help=(
            "Space-separated 'name:Type' pairs for CreateRequest fields. "
            "A default goes in the type, without spaces ('colour:str=\"\"'). "
            "Include the id-field to let the caller supply the key."
        ),
    )
    p.add_argument(
        "--update-fields",
        default=None,
        help=(
            "Space-separated 'name:Type' pairs for UpdateRequest fields "
            "(excluding id-field). Each is made optional, so an update names "
            "only what it changes."
        ),
    )
    p.add_argument(
        "--plural",
        default=None,
        help=(
            "Plural of the entity name, when inflect's guess is not what the "
            "domain says (e.g. Personas, not Personae)"
        ),
    )
    p.add_argument("--no-get", action="store_true", help="Skip GetUseCase")
    p.add_argument("--no-list", action="store_true", help="Skip ListUseCase")
    p.add_argument("--no-create", action="store_true", help="Skip CreateUseCase")
    p.add_argument("--no-update", action="store_true", help="Skip UpdateUseCase")
    # Opt in, where the other four are opt out. Two of the five kits must
    # never delete — ceap and polling keep the record of what was
    # processed — so emitting a destructive use case by default is the
    # wrong way for this to fail. The repository must also inherit
    # Deletable, or the generated file will not type-check.
    p.add_argument(
        "--delete",
        action="store_true",
        help="Emit DeleteUseCase (off by default; needs a Deletable repository)",
    )
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
        include_delete=args.delete,
        plural=args.plural,
        out_dir=args.out,
    )
    print(f"Generated: {out_file}")


if __name__ == "__main__":
    main()
