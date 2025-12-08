Releasing to PyPI
=================

Setup (one-time)
----------------

1. Create a PyPI account at https://pypi.org
2. Create an API token at https://pypi.org/manage/account/token/
3. Add the token to GitHub: Settings → Secrets and variables → Actions → New repository secret

   - Name: ``PYPI_API_TOKEN``
   - Value: your token (starts with ``pypi-``)

4. (Optional) For manual uploads, configure ``~/.pypirc`` to avoid entering credentials each time::

       [pypi]
       username = __token__
       password = pypi-YOUR_TOKEN_HERE

       [testpypi]
       username = __token__
       password = pypi-YOUR_TESTPYPI_TOKEN_HERE

   **Warning**: Never commit ``.pypirc`` to the repository - it contains secrets.

Publishing a release
--------------------

1. Create a release branch::

       git checkout master
       git pull
       git checkout -b release/vX.Y.Z

2. Update the version in both files:

   - ``pyproject.toml`` (version field)
   - ``src/julee/__init__.py`` (``__version__``)

3. Commit the version bump::

       git commit -am "Bump version to X.Y.Z"

4. Push the branch and create a PR::

       git push -u origin release/vX.Y.Z

   Then create a PR to merge into ``master``.

5. After the PR is merged, tag the release from master::

       git checkout master
       git pull
       git tag vX.Y.Z
       git push origin vX.Y.Z

6. The GitHub Action will automatically build and publish to PyPI.

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
