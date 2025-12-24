"""PipelineRouter for routing responses to downstream pipelines.

A PipelineRouter contains a list of PipelineRoutes and matches responses against them.
Multiple routes can match the same response (multiplex routing).

See: docs/architecture/proposals/pipeline_router_design.md
"""

from pydantic import BaseModel

from julee.core.entities.pipeline_route import PipelineRoute


class PipelineRouter(BaseModel):
    """Routes responses to downstream pipelines.

    A PipelineRouter is declarative and can be:
    - Configured in code
    - Serialized to/from JSON/YAML
    - Visualized as PlantUML
    """

    name: str
    description: str = ""
    routes: list[PipelineRoute] = []

    def route(self, response: BaseModel) -> list[PipelineRoute]:
        """Return all routes that match this response.

        This is multiplex routing - multiple routes can match the same response.
        Returns an empty list if no routes match.
        """
        return [r for r in self.routes if r.matches(response)]

    def add_route(self, route: PipelineRoute) -> "PipelineRouter":
        """Add a route (fluent API)."""
        self.routes.append(route)
        return self

    def to_plantuml(self) -> str:
        """Generate PlantUML activity diagram for visualization."""
        lines = [
            "@startuml",
            f"title {self.name}",
            "",
            "start",
        ]

        # Group routes by response type
        routes_by_response: dict[str, list[PipelineRoute]] = {}
        for route in self.routes:
            response_name = route.response_type.split(".")[-1]
            if response_name not in routes_by_response:
                routes_by_response[response_name] = []
            routes_by_response[response_name].append(route)

        for response_name, response_routes in routes_by_response.items():
            lines.append(f":{response_name}|")
            lines.append("")

            for route in response_routes:
                condition_str = str(route.condition)
                pipeline_name = route.pipeline.split(".")[-1]

                lines.append(f"if ({condition_str}?) then (yes)")
                lines.append(f"  :{pipeline_name};")

                if route.description:
                    # Escape newlines for PlantUML note
                    desc = route.description.replace("\n", "\\n")
                    lines.append(f"  note right: {desc}")

                lines.append("endif")
                lines.append("")

        lines.extend(
            [
                "stop",
                "@enduml",
            ]
        )

        return "\n".join(lines)
