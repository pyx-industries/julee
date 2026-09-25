# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path so Sphinx can find the modules
sys.path.insert(0, os.path.abspath('..'))

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
    'sphinx.ext.napoleon',          # Support for Google/NumPy style docstrings
    'sphinx.ext.viewcode',          # Add links to source code
    'sphinx.ext.coverage',          # Check documentation coverage

    # Third-party extensions
    'sphinx_autodoc_typehints',     # Better type hints rendering
    'autoapi.extension',            # Automatic API documentation
    'sphinxcontrib.mermaid',        # Mermaid diagram support
    'sphinxcontrib.plantuml',       # PlantUML diagram support
]

# AutoAPI configuration
autoapi_type = 'python'
autoapi_dirs = ['../src/julee']
autoapi_options = [
    'members',
    'undoc-members',
    'show-inheritance',
    'show-module-summary',
]
autoapi_ignore = [
    '*migrations*',
    '*tests*',
    '*test_*',
    '*/conftest.py',
]
autoapi_keep_files = True
autoapi_add_toctree_entry = True
autoapi_member_order = 'groupwise'

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
    'exclude-members': '__weakref__'
}
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

# PlantUML configuration
# Requires plantuml to be installed (apt install plantuml on Debian/Ubuntu)
plantuml_output_format = 'svg'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']

# Suppress warnings for ambiguous cross-references caused by re-exports in __init__.py
suppress_warnings = [
    'ref.python',  # Suppress "more than one target found for cross-reference" warnings
    'docutils',    # Suppress docutils formatting warnings from AutoAPI-generated code examples
]

# -- Cross-reference strictness ----------------------------------------------

# An unresolved cross-reference is an error, so that renaming or moving code
# cannot quietly leave the documentation pointing at nothing.
#
# Without this Sphinx says nothing at all: a :py:class: whose target does not
# exist renders as plain text and the build stays green. That is how dozens of
# references to julee.domain.* and julee.contrib.ceap.* survived ADR 012
# moving those packages out into julee-kits, in pages whose whole job is to
# teach the layout (#246).
#
# Note this is separate from suppress_warnings above: nitpick misses are
# reported as ref.class / ref.obj / ref.exc, not as ref.python, so the
# suppression there never hid them. Nothing was hiding them; nothing was
# looking.
nitpicky = True

nitpick_ignore = [
    # Module-level type aliases. AutoAPI emits each as py:data while the
    # annotations using it reference it as py:class, so it cannot resolve.
    # A new alias belongs here beside its siblings.
    ('py:class', 'Found'),                  # core.doctrine.rules.entity
    ('py:class', 'Published'),              # core.doctrine.rules.semantics

    # The literal `...` of a Protocol body, rendered as a default value.
    ('py:class', 'Ellipsis'),

    # Standard library. These would resolve if intersphinx were configured,
    # which is worth doing separately; until then they are noise, not defects.
    ('py:class', 'collections.abc.Callable'),
    ('py:class', 'collections.abc.Iterable'),
    ('py:class', 'collections.abc.Mapping'),
    ('py:class', 'io.IOBase'),
    ('py:class', 'pathlib.Path'),
    ('py:obj', 'enum.StrEnum'),

    # Third-party, likewise.
    ('py:class', 'pydantic.BaseModel'),
    ('py:obj', 'pydantic.BaseModel'),
    ('py:exc', 'S3Error'),
]

nitpick_ignore_regex = [
    # Third-party packages with no inventory available to this build.
    ('py:class', r'(minio|temporalio|urllib3)\..*'),
    ('py:obj', r'(minio|temporalio|urllib3)\..*'),
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Use Furo theme (modern and clean)
html_theme = 'furo'

# If you prefer Read the Docs theme, uncomment this line:
# html_theme = 'sphinx_rtd_theme'

html_static_path: list[str] = []

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
