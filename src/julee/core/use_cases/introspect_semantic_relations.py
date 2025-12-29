"""Introspect semantic relations use case.

Discovers semantic relations declared on entities within a bounded context
or module, enabling documentation systems to understand how entities
relate across framework layers.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from julee.core.decorators import get_semantic_relations, use_case
from julee.core.entities.semantic_relation import RelationType, SemanticRelation


class IntrospectSemanticRelationsRequest(BaseModel):
    """Request to introspect semantic relations in a module or BC."""

    module_path: str = Field(
        description="Dotted module path to introspect (e.g., 'julee.hcd.entities')"
    )
    relation_type: RelationType | None = Field(
        default=None,
        description="Filter to specific relation type",
    )
    target_type: type | None = Field(
        default=None,
        description="Filter to relations targeting this type",
    )

    model_config = {"arbitrary_types_allowed": True}


class IntrospectSemanticRelationsResponse(BaseModel):
    """Response containing discovered semantic relations."""

    relations: list[SemanticRelation] = Field(default_factory=list)
    count: int = 0
    source_classes: list[str] = Field(
        default_factory=list,
        description="Fully qualified names of classes with relations",
    )

    model_config = {"arbitrary_types_allowed": True}


@use_case
class IntrospectSemanticRelationsUseCase:
    """Discover semantic relations declared in a module.

    Inspects all classes in a module (and submodules) for the
    @semantic_relation decorator and returns the declared relationships.

    This enables documentation systems to understand:
    - Which solution entities map to framework viewpoint entities
    - Which viewpoint entities project onto core entities
    - The complete relationship graph for a bounded context
    """

    async def execute(
        self, request: IntrospectSemanticRelationsRequest
    ) -> IntrospectSemanticRelationsResponse:
        """Execute the use case.

        Args:
            request: Request with module path and optional filters

        Returns:
            Response containing discovered semantic relations
        """
        import importlib
        import inspect
        import pkgutil

        relations: list[SemanticRelation] = []
        source_classes: list[str] = []

        try:
            module = importlib.import_module(request.module_path)
        except ImportError:
            return IntrospectSemanticRelationsResponse(
                relations=[],
                count=0,
                source_classes=[],
            )

        # Collect all modules to inspect (including submodules)
        modules_to_inspect = [module]

        if hasattr(module, "__path__"):
            # It's a package, walk submodules
            for _importer, modname, _ispkg in pkgutil.walk_packages(
                module.__path__, prefix=module.__name__ + "."
            ):
                try:
                    submodule = importlib.import_module(modname)
                    modules_to_inspect.append(submodule)
                except ImportError:
                    continue

        # Inspect all classes in all modules
        for mod in modules_to_inspect:
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                # Only inspect classes defined in this module
                if obj.__module__ != mod.__name__:
                    continue

                class_relations = get_semantic_relations(obj)
                if not class_relations:
                    continue

                for rel in class_relations:
                    # Apply filters
                    if request.relation_type and rel.relation_type != request.relation_type:
                        continue
                    if request.target_type and rel.target_type != request.target_type:
                        continue

                    relations.append(rel)

                if class_relations:
                    source_classes.append(f"{obj.__module__}.{obj.__name__}")

        return IntrospectSemanticRelationsResponse(
            relations=relations,
            count=len(relations),
            source_classes=sorted(set(source_classes)),
        )


class FindEntitiesWithRelationRequest(BaseModel):
    """Request to find entities with a specific relation to a target type."""

    module_path: str = Field(
        description="Dotted module path to search (e.g., 'solution.entities')"
    )
    target_type: type = Field(description="The target type to find relations to")
    relation_type: RelationType = Field(description="The relation type to match")

    model_config = {"arbitrary_types_allowed": True}


class FindEntitiesWithRelationResponse(BaseModel):
    """Response containing entities with the specified relation."""

    entity_types: list[type] = Field(
        default_factory=list,
        description="Entity types that have the specified relation",
    )
    count: int = 0

    model_config = {"arbitrary_types_allowed": True}


@use_case
class FindEntitiesWithRelationUseCase:
    """Find all entities that have a specific relation to a target type.

    Useful for answering questions like:
    - "Which solution entities are Personas?" (is_a Persona)
    - "Which viewpoint entities project BoundedContext?" (projects BC)
    """

    async def execute(
        self, request: FindEntitiesWithRelationRequest
    ) -> FindEntitiesWithRelationResponse:
        """Execute the use case.

        Args:
            request: Request with module path, target type, and relation type

        Returns:
            Response containing matching entity types
        """
        # Use the introspection use case with filters
        introspect_uc = IntrospectSemanticRelationsUseCase()
        introspect_response = await introspect_uc.execute(
            IntrospectSemanticRelationsRequest(
                module_path=request.module_path,
                relation_type=request.relation_type,
                target_type=request.target_type,
            )
        )

        entity_types = [rel.source_type for rel in introspect_response.relations]

        return FindEntitiesWithRelationResponse(
            entity_types=entity_types,
            count=len(entity_types),
        )
