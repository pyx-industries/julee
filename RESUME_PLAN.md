# Resume Plan: Create HCD Journeys for Three Primary Personas

## Context
Creating HCD journey entities for the three primary personas identified in the julee framework.

## What Was Done
1. Identified three primary personas from `docs/journeys/`:
   - **Solutions Developer** - `build-production-solution`
   - **Business Process Analyst** - `define-business-workflow`
   - **Systems Architect** - `design-system-architecture`

2. Fixed import bug in `src/julee/docs/sphinx_hcd/domain/use_cases/suggestions.py`:
   - Changed `from ...hcd_api.suggestions import` to `from ....hcd_api.suggestions import`
   - The relative import was resolving to wrong path (3 dots went to `sphinx_hcd`, needed 4 dots to reach `docs`)

## What Remains After Restart
1. Verify MCP server can now call `create_journey` without import errors
2. Check if `list_journeys()` auto-loads from existing RST files in `docs/journeys/`
3. If not auto-loaded, create the three journeys via MCP:

```
Journey 1: build-production-solution
- persona: Solutions Developer
- intent: Create reliable, auditable business processes without reinventing infrastructure
- outcome: Deployed solution with complete audit trails and automatic retry handling
- goal: Build a production-ready workflow solution

Journey 2: define-business-workflow
- persona: Business Process Analyst
- intent: Capture business requirements in a way that translates directly to implementation
- outcome: Clear workflow specifications with policy validation and compliance requirements
- goal: Define and document business workflows

Journey 3: design-system-architecture
- persona: Systems Architect
- intent: Ensure system accountability, auditability, and clean separation of concerns
- outcome: Modular architecture with bounded contexts that can be composed and extended
- goal: Design multi-domain system architecture
```

## Quick Test After Restart
```bash
# Test the fix worked
.venv/bin/python -c "from julee.docs.sphinx_hcd.domain.use_cases.suggestions import compute_journey_suggestions; print('OK')"

# Then in Claude Code, run:
# mcp_list_journeys()
```
