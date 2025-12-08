Releasing to PyPI
=================

Setup (one-time)
----------------

1. Create a PyPI account at https://pypi.org
2. Create an API token at https://pypi.org/manage/account/token/
3. Add the token to GitHub: Settings → Secrets and variables → Actions → New repository secret

   - Name: ``PYPI_API_TOKEN``
   - Value: your token (starts with ``pypi-``)

Publishing a release
--------------------

1. Update the version in both files:

   - ``pyproject.toml`` (version field)
   - ``src/julee/__init__.py`` (``__version__``)

2. Commit the version bump::

       git commit -am "Bump version to X.Y.Z"

3. Tag the release::

       git tag vX.Y.Z
       git push origin master --tags

4. The GitHub Action will automatically build and publish to PyPI.

Manual publishing
-----------------

If you need to publish manually::

    pip install build twine
    python -m build
    twine upload dist/*

Testing with TestPyPI
---------------------

Before publishing to the real PyPI, test with TestPyPI:

1. Create an account at https://test.pypi.org
2. Create an API token at https://test.pypi.org/manage/account/token/
3. Upload to TestPyPI::

       twine upload --repository testpypi dist/*

4. Test installing from TestPyPI::

       pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ julee

Version numbering
-----------------

This project follows `Semantic Versioning <https://semver.org/>`_:

- MAJOR: incompatible API changes
- MINOR: new functionality, backwards compatible
- PATCH: bug fixes, backwards compatible
