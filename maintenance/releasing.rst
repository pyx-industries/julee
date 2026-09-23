Releasing to PyPI
=================

Setup (one-time, per distribution)
----------------------------------

Publishing uses PyPI's trusted publishing, so there is no token to hold or
rotate. PyPI is told to trust a particular repository and workflow, and the
workflow proves who it is with an OIDC token GitHub mints for the run.

For each distribution, on PyPI under Your account → Publishing, add a
publisher:

====================  ==============================
Field                 Value
====================  ==============================
PyPI project name     ``julee``
Owner                 ``pyx-industries``
Repository name       ``julee``
Workflow name         ``publish.yml``
Environment name      *(leave empty)*
====================  ==============================

For a project that does not exist yet, add it as a *pending* publisher;
PyPI creates the project on the first upload.

For manual uploads, configure ``~/.pypirc`` with an API token. Never commit
that file — it contains secrets.

This repository publishes ``julee``, and only ``julee``. The kits release
from `julee-kits <https://github.com/pyx-industries/julee-kits>`_, each on
its own tag. The workflow checks the tag against the version it finds, and
refuses to publish a mismatch.

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
