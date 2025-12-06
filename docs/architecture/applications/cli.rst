CLI Applications
================

.. note::
   This page is a stub. Content to be developed.

CLI applications expose Julee use cases via command-line interfaces.

Overview
--------

CLI applications:

- Execute use cases from command line
- Trigger workflows via Temporal client
- Perform administrative and operational tasks
- Support scripting and automation

Julee's CLI applications typically use Typer or Click.

Key Concepts
------------

**Direct Use Case Execution**
    CLI commands instantiate and execute use cases directly.

**Workflow Triggering**
    For async operations, CLIs can start Temporal workflows and optionally wait for results.

**Configuration**
    CLI apps read configuration from environment variables or config files.

Example
-------

::

    import typer
    import asyncio
    from julee.domain.use_cases import ExtractAssembleUseCase
    from infrastructure.dependencies import create_use_case

    app = typer.Typer()

    @app.command()
    def extract(
        doc_id: str,
        spec_id: str,
        async_mode: bool = False
    ):
        """Extract and assemble document data."""
        if async_mode:
            # Trigger workflow
            workflow_id = trigger_workflow(doc_id, spec_id)
            typer.echo(f"Started workflow: {workflow_id}")
        else:
            # Direct execution
            use_case = create_use_case()
            result = asyncio.run(use_case.execute(doc_id, spec_id))
            typer.echo(f"Result: {result}")

    @app.command()
    def init():
        """Initialize system with seed data."""
        use_case = create_init_use_case()
        asyncio.run(use_case.execute())
        typer.echo("System initialized")

    if __name__ == "__main__":
        app()

Use Cases
---------

**Development**
    Test use cases locally without running full stack.

**Administration**
    System initialization, data migration, cleanup tasks.

**Automation**
    CI/CD pipelines, scheduled jobs, batch processing.

**Debugging**
    Inspect system state, replay workflows, test configurations.

See Also
--------

- :doc:`/architecture/clean_architecture/protocols` for dependency injection
- :doc:`worker` for workflow execution
- :doc:`api` for REST API patterns
