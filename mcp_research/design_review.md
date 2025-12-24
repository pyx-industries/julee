# MCP Service Interface Design Review

A critical assessment of the HCD and C4 MCP service implementations against best practices established in prior research.

---

## Executive Summary

The julee MCP services demonstrate **strong adherence to core best practices** in tool documentation, naming conventions, and clean architecture separation. However, there are **significant opportunities for improvement** in response design, tool annotations, and token efficiency that would better align with research findings from Anthropic and the broader MCP ecosystem.

**Overall Assessment: B+**

| Category | Grade | Key Finding |
|----------|-------|-------------|
| Tool Descriptions | A | Rich, contextual docstrings with examples |
| Parameter Documentation | A- | Good examples, could add more constraints |
| Response Design | C+ | Missing best practices for high-signal content |
| Tool Annotations | D | Completely absent |
| Naming Conventions | A | Consistent, semantic, within limits |
| Error Handling | B- | Basic structure, could be more actionable |
| Token Efficiency | C | No compression options, full entity dumps |

---

## 1. Strengths

### 1.1 Excellent Tool Descriptions

The docstrings follow the recommended three-part structure:

```python
"""Create a user story: 'As a <persona>, I want <action> so that <benefit>'.

Stories are the atomic unit of user requirements in Human-Centered Design.
They capture WHO needs something (persona), WHAT they need (i_want), and
WHY they need it (so_that). Stories belong to apps and can be grouped into epics.

The persona field automatically creates/references a derived Persona entity.
Use list_personas() to see all personas derived from existing stories.
```

**What works well:**
- First line states **what** the tool does
- Body explains domain context and **when** to use
- Cross-references related tools (`Use list_personas()...`)
- Includes semantic explanation of field purposes

### 1.2 Parameter Documentation with Examples

```python
Args:
    feature_title: Descriptive title (e.g., "Login with SSO", "Export Report")
    persona: Who needs this (e.g., "Staff Member", "External User", "Admin")
```

This aligns with best practice: "Add example values in descriptions."

### 1.3 Semantic Identifiers (No UUIDs)

All entities use human-readable slugs:
- `"authentication"` not `"a3f8c2b1-9d4e-4f5a-8b7c-..."`
- `"hr-portal"` not `"b2c9d8e7-6f5a-4b3c-2d1e-..."`

This directly addresses the UUID problem identified in research where UUIDs cause ~50% error rates vs ~3% for semantic identifiers.

### 1.4 Consistent Naming Convention

All tools follow `mcp_{verb}_{entity}` pattern:
- `mcp_create_story`
- `mcp_get_epic`
- `mcp_list_personas`
- `mcp_update_accelerator`
- `mcp_delete_app`

This aligns with best practice: "Start with verb" and "Use snake_case."

### 1.5 Clean Architecture Separation

The three-layer structure maintains proper boundaries:
```
server.py (MCP-facing docstrings)
    ↓
tools/*.py (Implementation logic)
    ↓
hcd_api/requests.py (DTOs with validation)
```

### 1.6 Contextual Suggestions in Responses

The `suggestions` array is an innovative addition:

```python
{
    "severity": "warning",
    "category": "incomplete",
    "message": f"{unknown_persona_count} stories have unknown personas",
    "action": "Review and update stories to specify personas",
    "tool": "update_story",
    "context": {"count": unknown_persona_count},
}
```

This implements the "Guidance Pattern" from response design research.

---

## 2. Areas for Improvement

### 2.1 Missing Tool Annotations (Critical)

**Current state:** No annotations are provided.

**Best practice:** All MCP tools should specify behavioral hints.

```python
# Current
@mcp.tool()
async def mcp_list_stories() -> dict:

# Recommended
@mcp.tool(annotations={
    "readOnlyHint": True,
    "title": "List User Stories"
})
async def mcp_list_stories() -> dict:
```

**Impact:**
- Clients cannot auto-approve safe operations
- No distinction between read-only and mutating tools
- Delete operations lack `destructiveHint` warning

**Recommended annotations by operation type:**

| Operation | readOnlyHint | destructiveHint | idempotentHint |
|-----------|--------------|-----------------|----------------|
| `list_*` | true | - | - |
| `get_*` | true | - | - |
| `create_*` | false | false | false |
| `update_*` | false | false | true |
| `delete_*` | false | true | true |

### 2.2 Response Structure Issues

**Current response format:**
```python
return {
    "success": True,
    "entity": response.story.model_dump(),  # Full domain model
    "suggestions": suggestions,
}
```

**Problems identified:**

1. **Full entity dumps**: Returns all fields regardless of need
2. **No summary/count first**: Violates "front-load critical information"
3. **No pagination**: List operations return all entities
4. **No response format option**: Cannot request concise vs detailed

**Recommended improvements:**

```python
# Better response structure
return {
    # Summary first (front-loaded)
    "success": True,
    "count": 1,

    # Core data
    "entity": {
        "slug": story.slug,
        "feature_title": story.feature_title,
        "persona": story.persona,
        # Only essential fields
    },

    # Guidance last (recency anchoring)
    "suggestions": suggestions,
    "next_actions": ["Use get_story(slug) for full details"],
}
```

### 2.3 No Output Schema Defined

**Current state:** Tools return `-> dict` with no schema documentation.

**Best practice:** Define `outputSchema` for structured responses.

```python
@mcp.tool(
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "entity": {"$ref": "#/definitions/Story"},
            "suggestions": {"type": "array"}
        }
    }
)
```

**Impact:**
- Clients cannot validate responses
- Agents lack predictability about response structure
- No type safety for downstream processing

### 2.4 Missing Token Efficiency Features

**Research finding:** "Response format enums reduced token usage by 65%."

**Current state:** No verbosity control.

**Recommended addition:**

```python
async def mcp_get_story(
    slug: str,
    format: str = "full"  # "summary" | "full" | "with_relationships"
) -> dict:
    """Get a story by slug.

    Args:
        slug: Story identifier
        format: Response detail level
            - summary: slug, title, persona only (~50 tokens)
            - full: all story fields (~150 tokens)
            - with_relationships: includes epic/journey refs (~300 tokens)
    """
```

### 2.5 List Operations Lack Pagination

**Current state:** `list_stories()` returns all entities.

```python
return {
    "entities": [s.model_dump() for s in response.stories],
    "count": len(response.stories),
}
```

**Best practice:** Implement pagination with guidance.

```python
return {
    "entities": entities[:limit],
    "pagination": {
        "total": len(all_entities),
        "returned": len(entities),
        "limit": limit,
        "offset": offset,
        "has_more": len(all_entities) > offset + limit,
    },
    "efficiency_hint": f"{len(all_entities)} total. Use filters or increase offset." if len(all_entities) > 20 else None
}
```

### 2.6 Error Responses Could Be More Actionable

**Current not-found response:**
```python
return {
    "entity": None,
    "found": False,
    "suggestions": [],
}
```

**Better pattern:**
```python
return {
    "entity": None,
    "found": False,
    "error": {
        "type": "not_found",
        "message": f"Story '{slug}' not found",
        "suggestion": "Check spelling or use list_stories() to find valid slugs",
        "similar_slugs": find_similar_slugs(slug, all_stories),  # Fuzzy match
    },
    "suggestions": [],
}
```

### 2.7 No Filtering on List Operations

**Current state:** All list operations return everything.

**Best practice:** Support filtering to reduce result sets.

```python
async def mcp_list_stories(
    app_slug: str | None = None,
    persona: str | None = None,
    limit: int = 50,
) -> dict:
    """List user stories with optional filters.

    Args:
        app_slug: Filter by app (optional)
        persona: Filter by persona (optional)
        limit: Maximum results (default 50, max 200)
    """
```

### 2.8 Inconsistent Description Depth

**Strong (HCD):**
```python
"""Create a user story: 'As a <persona>, I want <action> so that <benefit>'.

Stories are the atomic unit of user requirements...
"""
```

**Weaker (C4):**
```python
"""List all containers in the C4 model."""
```

The C4 list operations have minimal descriptions without guidance on when to use them.

---

## 3. Detailed Recommendations

### 3.1 Add Annotations to All Tools

**Priority: High**

Create a helper or decorator pattern:

```python
# annotations.py
READ_ONLY = {"readOnlyHint": True}
CREATES = {"readOnlyHint": False, "destructiveHint": False}
UPDATES = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True}
DELETES = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True}

# server.py
@mcp.tool(annotations=READ_ONLY)
async def mcp_list_stories() -> dict: ...

@mcp.tool(annotations=DELETES)
async def mcp_delete_story(slug: str) -> dict: ...
```

### 3.2 Implement Response Compression

**Priority: High**

Add a `format` parameter to all get/list operations:

```python
class ResponseFormat(str, Enum):
    SUMMARY = "summary"    # Essential fields only
    FULL = "full"          # All fields
    EXTENDED = "extended"  # With relationships

def format_entity(entity, format: ResponseFormat) -> dict:
    if format == ResponseFormat.SUMMARY:
        return {
            "slug": entity.slug,
            "name": getattr(entity, 'name', entity.slug),
        }
    elif format == ResponseFormat.FULL:
        return entity.model_dump()
    else:
        return entity.model_dump() | {"relationships": get_relationships(entity)}
```

### 3.3 Add Pagination to List Operations

**Priority: Medium**

```python
async def mcp_list_stories(
    limit: int = 20,
    offset: int = 0,
    app_slug: str | None = None,
) -> dict:
    """List user stories with pagination.

    Args:
        limit: Max results per page (1-100, default 20)
        offset: Skip first N results (default 0)
        app_slug: Filter by app (optional)
    """
```

### 3.4 Define Output Schemas

**Priority: Medium**

Use Pydantic models to generate output schemas:

```python
class StoryResponse(BaseModel):
    success: bool
    entity: Story | None
    suggestions: list[Suggestion]

@mcp.tool(output_schema=StoryResponse.model_json_schema())
async def mcp_get_story(slug: str) -> dict: ...
```

### 3.5 Enhance Error Responses

**Priority: Medium**

Create a standardized error response builder:

```python
def not_found_response(entity_type: str, identifier: str, similar: list[str] = None):
    return {
        "success": False,
        "entity": None,
        "error": {
            "type": "not_found",
            "entity_type": entity_type,
            "identifier": identifier,
            "message": f"{entity_type} '{identifier}' not found",
            "similar": similar[:5] if similar else [],
            "recovery": f"Use list_{entity_type.lower()}s() to see available {entity_type.lower()}s",
        }
    }
```

### 3.6 Add Cross-Reference Guidance to C4 Tools

**Priority: Low**

Enhance C4 list operations:

```python
"""List all containers in the C4 model.

Use this to find containers when creating components or relationships.
Filter results mentally by system_slug if looking for a specific system's containers.

Related tools:
- get_container(slug) for full container details
- list_software_systems() to find parent systems
- create_component() to add components to a container
"""
```

---

## 4. Implementation Priority Matrix

| Recommendation | Impact | Effort | Priority |
|---------------|--------|--------|----------|
| Add tool annotations | High | Low | P0 |
| Add response format parameter | High | Medium | P1 |
| Implement pagination | Medium | Medium | P1 |
| Define output schemas | Medium | Medium | P2 |
| Enhance error responses | Medium | Low | P2 |
| Add list filters | Medium | Medium | P2 |
| Improve C4 descriptions | Low | Low | P3 |

---

## 5. Checklist: Current Compliance

Based on the research best practices checklist:

| Requirement | HCD | C4 | Notes |
|-------------|-----|-----|-------|
| Tool name under 64 chars | ✅ | ✅ | All comply |
| Description states what tool does | ✅ | ✅ | Good |
| Description explains when to use | ✅ | ⚠️ | C4 list ops weak |
| Description differentiates from related | ✅ | ⚠️ | Could improve |
| All parameters have descriptions | ✅ | ✅ | With examples |
| Required fields marked | ✅ | ✅ | Via type hints |
| Examples in parameter descriptions | ✅ | ✅ | Good |
| Annotations set | ❌ | ❌ | **Missing entirely** |
| Output schema provided | ❌ | ❌ | **Missing entirely** |
| Errors are actionable | ⚠️ | ⚠️ | Basic, could improve |
| No sensitive info exposed | ✅ | ✅ | Clean |

---

## 6. Conclusion

The julee MCP services have a **solid foundation** with excellent tool descriptions, semantic identifiers, and clean architecture. The innovative suggestions system adds domain-specific guidance that goes beyond standard MCP patterns.

However, the **complete absence of tool annotations** is a significant gap that should be addressed immediately. Additionally, implementing **response compression** and **pagination** would significantly improve token efficiency and agent performance.

The recommended changes are incremental and can be implemented without restructuring the existing architecture. Priority should be given to:

1. Adding annotations (immediate, low effort, high impact)
2. Response format options (near-term, enables agent-controlled verbosity)
3. Pagination (medium-term, essential for scalability)

---

*Design review conducted: December 2025*
