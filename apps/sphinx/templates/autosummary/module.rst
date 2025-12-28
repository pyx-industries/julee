{# Dispatcher template - selects bespoke template based on module path #}
{% if "entities" in fullname and "core" in fullname %}
{% include "autosummary/core_entity.rst" %}
{% elif "entities" in fullname and "hcd" in fullname %}
{% include "autosummary/hcd_entity.rst" %}
{% elif "entities" in fullname and "c4" in fullname %}
{% include "autosummary/c4_entity.rst" %}
{% elif "use_cases" in fullname %}
{% include "autosummary/usecase.rst" %}
{% elif "repositories" in fullname and "infrastructure" not in fullname %}
{% include "autosummary/repository.rst" %}
{% else %}
{% include "autosummary/default.rst" %}
{% endif %}
