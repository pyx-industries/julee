"""DependencyRule model for Clean Architecture layer constraints."""

from pydantic import BaseModel, Field


class DependencyRule(BaseModel):
    """The one rule that makes everything else possible.

    Source code dependencies must point inward. Always. No exceptions.

    An entity cannot import a use case. A use case cannot import a
    controller. A repository protocol cannot import its SQLAlchemy
    implementation. The inner circles must be blissfully ignorant of
    the outer circles. This is not a guideline - it's the law.

    Why? Because the inner circles are your business. They represent
    concepts that exist independent of any technology choice. When you
    let a database import leak into an entity, that entity now changes
    when your database changes. Your business is now coupled to MySQL.

    The layers form concentric circles: entities at the center (pure
    business), then use cases (application logic), then interface
    adapters (controllers, presenters), then frameworks (the outer
    shell). Each layer can only know about layers inside it.

    Violations are architectural debt. Every forbidden import is a
    crack in your foundation. Today it's convenient. Tomorrow it's a
    rewrite when you need to change your ORM.
    """

    source_layer: str = Field(description="The layer containing the import")
    target_layer: str = Field(description="The layer being imported from")
    source_file: str = Field(description="File containing the violation")
    import_path: str = Field(description="The forbidden import path")

    @property
    def is_violation(self) -> bool:
        """Check if this import violates the dependency rule."""
        from julee.shared.doctrine_constants import LAYER_FORBIDDEN_IMPORTS

        forbidden = LAYER_FORBIDDEN_IMPORTS.get(self.source_layer, frozenset())
        return self.target_layer in forbidden
