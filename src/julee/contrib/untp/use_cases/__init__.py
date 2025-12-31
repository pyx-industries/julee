"""UNTP use cases.

Use cases for UNTP credential projection and management.

Primary use cases:
- ProjectExecutionUseCase: Project UseCaseExecution → list[DTE]
- ProjectOutputUseCase: Project PipelineOutput → DPP
- EmitCredentialUseCase: Sign and store credentials

CRUD use cases (Get/List only, credentials are projected not created):
- GetDigitalTraceabilityEventUseCase
- ListDigitalTraceabilityEventsUseCase
- GetDigitalProductPassportUseCase
- ListDigitalProductPassportsUseCase

Import from submodules directly:
    from julee.contrib.untp.use_cases.project_execution import ProjectExecutionUseCase
    from julee.contrib.untp.use_cases.crud import GetDigitalTraceabilityEventUseCase
"""
