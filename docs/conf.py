# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path so Sphinx can find the modules
project_root = os.path.abspath('..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Julee'
copyright = '2025, Pyx Holdings Pty. Ltd.'
author = 'Chris Gough'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Core Sphinx extensions
    'sphinx.ext.autodoc',           # Auto-generate docs from docstrings
    'sphinx.ext.autosummary',       # Auto-generate API stub pages
    'sphinx.ext.napoleon',          # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',          # Add links to source code
    'sphinx.ext.coverage',          # Check documentation coverage

    # Third-party extensions
    'sphinx_autodoc_typehints',     # Better type hints rendering
    'sphinxcontrib.mermaid',        # Mermaid diagram support
    'sphinxcontrib.plantuml',       # PlantUML diagram support

    # Julee documentation extensions (self-documenting)
    'apps.sphinx.core',             # Core doctrine reflexive documentation
    'apps.sphinx.hcd',              # Human-Centered Design directives
    'apps.sphinx.c4',               # C4 model architecture directives
]

# Mock imports for heavy dependencies that may not be available during doc build
autodoc_mock_imports = [
    'temporalio',
    'minio',
    'anthropic',
    'mcp',
]

# Autosummary configuration
autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc configuration
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'show-inheritance': True,
}
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'
autodoc_class_signature = 'separated'

# PlantUML configuration
# Requires plantuml to be installed (apt install plantuml on Debian/Ubuntu)
plantuml_output_format = 'svg'

# sphinx_hcd configuration (Human-Centered Design documentation)
# Julee uses its own HCD extension for self-documentation
sphinx_hcd = {
    'docs_structure': {
        'applications': 'domain/applications',
        'personas': 'users/personas',
        'journeys': 'users/journeys',
        'epics': 'users/epics',
        'accelerators': 'domain/accelerators',
        'stories': 'users/stories',
    },
}

# Templates path - apps/sphinx/templates takes precedence for autosummary
templates_path = ['../apps/sphinx/templates', '_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']

# Suppress warnings for ambiguous cross-references caused by re-exports in __init__.py
suppress_warnings = [
    'ref.python',  # Suppress "more than one target found for cross-reference" warnings
    'docutils',    # Suppress docutils formatting warnings from AutoAPI-generated code examples
    'autodoc.duplicate_object',  # Suppress duplicate object warnings from __init__.py re-exports
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Use Furo theme (modern and clean)
html_theme = 'furo'

# If you prefer Read the Docs theme, uncomment this line:
# html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

# Theme options for Furo
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2563eb",  # Blue
        "color-brand-content": "#2563eb",
    },
    "dark_css_variables": {
        "color-brand-primary": "#3b82f6",  # Lighter blue for dark mode
        "color-brand-content": "#3b82f6",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

# Additional HTML options
html_title = f"{project} v{release}"
html_short_title = project
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# -- Options for other output formats ----------------------------------------

# LaTeX output
latex_documents = [
    ('index', 'julee.tex', 'Julee Documentation',
     'Chris Gough', 'manual'),
]

# man page output
man_pages = [
    ('index', 'julee', 'Julee Documentation',
     [author], 1)
]

# Texinfo output
texinfo_documents = [
    ('index', 'julee', 'Julee Documentation',
     author, 'julee', 'Capture, Extract, Assemble, Publish workflow system.',
     'Miscellaneous'),
]
