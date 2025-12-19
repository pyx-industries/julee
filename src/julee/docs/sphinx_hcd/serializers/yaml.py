"""YAML manifest serializers.

Serializes App and Integration domain objects to YAML manifest format.
"""

import yaml

from ..domain.models.app import App
from ..domain.models.integration import Integration


def serialize_app(app: App) -> str:
    """Serialize an App to YAML manifest format.

    Produces YAML matching the app.yaml schema:
        name: <name>
        type: <app_type>
        status: <status>  # if present
        description: <description>
        accelerators:
          - <accelerator1>
          - <accelerator2>

    Args:
        app: App domain object to serialize

    Returns:
        YAML manifest content as string
    """
    data: dict = {
        "name": app.name,
        "type": app.app_type.value,
    }

    if app.status:
        data["status"] = app.status

    if app.description:
        data["description"] = app.description

    if app.accelerators:
        data["accelerators"] = app.accelerators

    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def serialize_integration(integration: Integration) -> str:
    """Serialize an Integration to YAML manifest format.

    Produces YAML matching the integration.yaml schema:
        slug: <slug>
        name: <name>
        description: <description>
        direction: <direction>
        depends_on:
          - name: <dep_name>
            url: <dep_url>
            description: <dep_description>

    Args:
        integration: Integration domain object to serialize

    Returns:
        YAML manifest content as string
    """
    data: dict = {
        "slug": integration.slug,
        "name": integration.name,
    }

    if integration.description:
        data["description"] = integration.description

    data["direction"] = integration.direction.value

    if integration.depends_on:
        depends_on_list = []
        for dep in integration.depends_on:
            dep_data: dict = {"name": dep.name}
            if dep.url:
                dep_data["url"] = dep.url
            if dep.description:
                dep_data["description"] = dep.description
            depends_on_list.append(dep_data)
        data["depends_on"] = depends_on_list

    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
