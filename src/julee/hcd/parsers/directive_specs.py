"""Directive specifications for HCD RST directives.

Defines the option specifications for each directive type, used by both
docutils parsing and directive registration.
"""


def unchanged_optional(argument: str | None) -> str:
    """Accept any value or None."""
    if argument is None:
        return ""
    return argument.strip()


def unchanged_required(argument: str | None) -> str:
    """Accept any non-empty value."""
    if argument is None or not argument.strip():
        raise ValueError("Argument is required")
    return argument.strip()


# Directive specifications: option_name -> validator
DIRECTIVE_SPECS = {
    "define-story": {
        "options": {
            "app": unchanged_required,
            "persona": unchanged_required,
            "name": unchanged_optional,
        }
    },
    "define-journey": {
        "options": {
            "persona": unchanged_required,
            "intent": unchanged_optional,
            "outcome": unchanged_optional,
            "depends-on": unchanged_optional,
            "preconditions": unchanged_optional,
            "postconditions": unchanged_optional,
            "name": unchanged_optional,
        }
    },
    "define-epic": {
        "options": {
            "name": unchanged_optional,
        }
    },
    "define-accelerator": {
        "options": {
            "name": unchanged_optional,
            "status": unchanged_optional,
            "milestone": unchanged_optional,
            "acceptance": unchanged_optional,
            "sources-from": unchanged_optional,
            "publishes-to": unchanged_optional,
            "depends-on": unchanged_optional,
            "feeds-into": unchanged_optional,
        }
    },
    "define-persona": {
        "options": {
            "name": unchanged_optional,
            "goals": unchanged_optional,
            "frustrations": unchanged_optional,
            "jobs-to-be-done": unchanged_optional,
        }
    },
    "define-app": {
        "options": {
            "name": unchanged_optional,
            "type": unchanged_optional,
            "status": unchanged_optional,
            "accelerators": unchanged_optional,
        }
    },
    "define-integration": {
        "options": {
            "name": unchanged_optional,
            "type": unchanged_optional,
            "direction": unchanged_optional,
        }
    },
    # Step directives (nested within journey)
    "step-story": {"options": {}},
    "step-epic": {"options": {}},
    "step-phase": {"options": {}},
    # Epic child directive
    "epic-story": {"options": {}},
}


def get_option_spec(directive_name: str) -> dict:
    """Get the option specification for a directive.

    Args:
        directive_name: Name of the directive (e.g., 'define-journey')

    Returns:
        Dict mapping option names to validator functions
    """
    spec = DIRECTIVE_SPECS.get(directive_name)
    if spec is None:
        return {}
    return spec.get("options", {})
