# How MCP Tool Descriptions are Generated from Docstrings

This document explains how the julee architecture generates MCP tool metadata from Python docstrings and type annotations.

---

## Overview

The HCD and C4 MCP services use FastMCP, which automatically extracts tool metadata from:
- Function docstrings → Tool descriptions and parameter descriptions
- Type annotations → JSON Schema for input validation
- Default values → Optional parameters with defaults
- Function names → Tool identifiers

---

## Extraction Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  server.py: @mcp.tool() decorated functions                         │
│                                                                      │
│  @mcp.tool()                                                        │
│  async def mcp_create_story(                                        │
│      feature_title: str,    ─────────────────► JSON Schema type     │
│      persona: str,                                                   │
│      i_want: str = "do something",  ─────────► default value        │
│  ) -> dict:                                                          │
│      """Create a user story...  ────────────► Tool description      │
│                                                                      │
│      Args:                                                          │
│          feature_title: Descriptive title ──► Parameter description │
│          persona: Who needs this...                                 │
│      """                                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Metadata Mapping

| Python Source | MCP Schema Field | Example |
|---------------|------------------|---------|
| Function docstring (first paragraph) | `description` | "Create a user story: 'As a <persona>...'" |
| Function name | `name` | `mcp_create_story` |
| Type annotation | `inputSchema.properties.*.type` | `str` → `"type": "string"` |
| Default value | `inputSchema.properties.*.default` | `"do something"` |
| `Args:` docstring section | `inputSchema.properties.*.description` | "Descriptive title (e.g., ...)" |
| Parameters without defaults | `inputSchema.required` | `["feature_title", "persona", "app_slug"]` |
| `FastMCP(instructions=...)` | Server-level instructions | "MCP server for Human-Centered Design..." |

---

## Type Annotation Conversions

| Python Type | JSON Schema |
|-------------|-------------|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list[str]` | `{"type": "array", "items": {"type": "string"}}` |
| `str \| None` | `{"type": "string"}` (not in required) |
| `Literal["a", "b"]` | `{"type": "string", "enum": ["a", "b"]}` |

---

## Docstring Structure

The docstrings follow Google-style format with specific sections:

```python
@mcp.tool()
async def mcp_create_story(
    feature_title: str,
    persona: str,
    app_slug: str,
    i_want: str = "do something",
    so_that: str = "achieve a goal",
) -> dict:
    """Create a user story: 'As a <persona>, I want <action> so that <benefit>'.

    Stories are the atomic unit of user requirements in Human-Centered Design.
    They capture WHO needs something (persona), WHAT they need (i_want), and
    WHY they need it (so_that). Stories belong to apps and can be grouped into epics.

    The persona field automatically creates/references a derived Persona entity.
    Use list_personas() to see all personas derived from existing stories.

    Args:
        feature_title: Descriptive title (e.g., "Login with SSO", "Export Report")
        persona: Who needs this (e.g., "Staff Member", "External User", "Admin")
        app_slug: Which app this story belongs to (must exist - use list_apps())
        i_want: The action/capability needed (e.g., "log in using my company credentials")
        so_that: The benefit/value (e.g., "I don't need to remember another password")
    """
```

### Section Breakdown

1. **First Line**: Concise summary (becomes primary description)
2. **Body Paragraphs**: Extended explanation, domain context, examples
3. **Args Section**: Per-parameter descriptions with examples in parentheses

---

## Architecture Layers

```
┌────────────────────────────────────────────────────────────┐
│ hcd_mcp/server.py                                          │
│   - @mcp.tool() decorated wrapper functions                │
│   - Full docstrings with Args sections (MCP-facing)        │
│   - Type annotations for schema generation                 │
└────────────────────────┬───────────────────────────────────┘
                         │ delegates to
                         ▼
┌────────────────────────────────────────────────────────────┐
│ hcd_mcp/tools/stories.py (etc.)                            │
│   - Implementation functions                               │
│   - Simpler docstrings (developer-facing, not exposed)     │
│   - Creates Request DTOs, calls use cases                  │
└────────────────────────┬───────────────────────────────────┘
                         │ uses
                         ▼
┌────────────────────────────────────────────────────────────┐
│ hcd_api/requests.py                                        │
│   - Pydantic Request DTOs with validation                  │
│   - Domain model conversion methods                        │
└────────────────────────────────────────────────────────────┘
```

---

## Advanced FastMCP Features

### Explicit Description Override

```python
@mcp.tool(description="Custom description overriding docstring")
async def my_tool(): ...
```

### Parameter Metadata with Annotated

```python
from typing import Annotated
from pydantic import Field

async def my_tool(
    url: Annotated[str, Field(description="URL to process", pattern=r"https?://.*")]
): ...
```

### Tool Annotations

```python
@mcp.tool(annotations={"readOnlyHint": True})
async def list_items(): ...

@mcp.tool(annotations={"destructiveHint": True})
async def delete_item(id: str): ...
```

---

## Design Decisions in Julee

1. **Docstrings in server.py are AI-facing**: Written for AI agents with domain explanations and usage examples

2. **Docstrings in tools/*.py are developer-facing**: Document internal implementation but don't get exposed to MCP

3. **Rich parameter descriptions**: Include examples in parentheses to guide AI usage

4. **Server instructions**: Provide high-level context via `FastMCP(instructions=...)`

5. **Consistent naming**: All tools prefixed with `mcp_` to distinguish from internal functions

---

## Example: Generated MCP Tool Schema

For `mcp_create_story`, FastMCP generates:

```json
{
  "name": "mcp_create_story",
  "description": "Create a user story: 'As a <persona>, I want <action> so that <benefit>'.\n\nStories are the atomic unit of user requirements in Human-Centered Design...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "feature_title": {
        "type": "string",
        "description": "Descriptive title (e.g., \"Login with SSO\", \"Export Report\")"
      },
      "persona": {
        "type": "string",
        "description": "Who needs this (e.g., \"Staff Member\", \"External User\", \"Admin\")"
      },
      "app_slug": {
        "type": "string",
        "description": "Which app this story belongs to (must exist - use list_apps())"
      },
      "i_want": {
        "type": "string",
        "description": "The action/capability needed (e.g., \"log in using my company credentials\")",
        "default": "do something"
      },
      "so_that": {
        "type": "string",
        "description": "The benefit/value (e.g., \"I don't need to remember another password\")",
        "default": "achieve a goal"
      }
    },
    "required": ["feature_title", "persona", "app_slug"]
  }
}
```
