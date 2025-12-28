CLIs
====

CLI applications expose Julee :py:class:`use cases <julee.core.entities.use_case.UseCase>` via command-line interfaces.

CLI commands instantiate and execute use cases directly, or trigger :doc:`worker <worker>` :doc:`pipelines </architecture/solutions/pipelines>` for asynchronous operations. CLIs read configuration from environment variables or config files. Common uses include administrative tasks, development and debugging, batch operations, and system initialization.

Unlike :doc:`UIs <ui>`, CLIs invoke use cases directly rather than going through the :doc:`API <api>`. This makes them well-suited for operations that don't need HTTP overhead or for environments where only the CLI is deployed.
