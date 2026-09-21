# julee-viewpoints

Code-outward documentation for julee solutions: the Sphinx directives that
project a solution's personas, journeys, epics, stories, applications,
integrations and bounded contexts into its documentation.

This is a julee kit. Install it and adopt it:

```toml
[tool.julee]
kits = ["viewpoints"]
```

then add the extension in `docs/conf.py`:

```python
extensions = ["julee_viewpoints.sphinx_hcd"]
```

The directives and their options are documented in
`src/julee_viewpoints/sphinx_hcd/README.md`.
