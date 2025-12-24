# Best Practices for Tool Documentation in MCP Services

A research report on conventions, guidelines, and best practices for documenting tools in Model Context Protocol (MCP) servers.

---

## Executive Summary

Effective tool documentation is critical for MCP servers because tool descriptions directly influence how AI agents discover, understand, and invoke tools. Research shows that even small refinements to tool descriptions yield dramatic improvements in agent performance—Claude Sonnet 3.5 achieved state-of-the-art results on SWE-bench after precise refinements to its tool descriptions.

This report synthesizes guidelines from the official MCP specification, Anthropic's directory policy, and industry best practices.

---

## 1. Tool Definition Structure

Every MCP tool consists of the following core properties:

| Property | Required | Description |
|----------|----------|-------------|
| `name` | Yes | Unique identifier for the tool (max 64 characters) |
| `title` | No | Human-readable display name |
| `description` | Yes | Human-readable description of functionality |
| `inputSchema` | Yes | JSON Schema defining expected parameters |
| `outputSchema` | No | JSON Schema defining expected output structure |
| `annotations` | No | Behavioral hints (readOnlyHint, destructiveHint, etc.) |

### Example Tool Definition

```json
{
  "name": "get_weather",
  "title": "Weather Information Provider",
  "description": "Get current weather information for a location. Use this when the user asks about weather conditions, temperature, or forecasts for a specific city or region.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City name or zip code (e.g., 'New York' or '10001')"
      }
    },
    "required": ["location"]
  },
  "annotations": {
    "readOnlyHint": true
  }
}
```

---

## 2. Writing Effective Tool Descriptions

### 2.1 Core Principles

**Clarity and Explicitness**
- Write descriptions as if explaining to a new team member
- Make implicit context explicit—clearly define specialized query formats, terminology, and relationships between resources
- Avoid jargon unless your target audience expects it

**Precision Over Brevity**
- Descriptions must narrowly and unambiguously describe what each tool does
- State precisely *when* the tool should be invoked, not just *what* it does
- Avoid vague language that could apply to multiple tools

**Accuracy**
- Descriptions must precisely match actual functionality
- Never include unexpected functionality or promise undelivered features
- Update descriptions when tool behavior changes

### 2.2 Description Structure Template

A well-structured tool description answers three questions:

1. **What does this tool do?** (Primary function)
2. **When should it be used?** (Invocation criteria)
3. **What are its constraints?** (Limitations, edge cases)

**Example:**

```
Get current weather information for a location. Use this when the user
asks about current weather conditions, temperature, humidity, or immediate
forecasts. For historical weather data or long-range forecasts, use
get_weather_history or get_weather_forecast instead.
```

### 2.3 Common Mistakes to Avoid

| Mistake | Problem | Better Approach |
|---------|---------|-----------------|
| Wrapping APIs without consideration | Agents don't understand when to use the tool | Add invocation criteria and context |
| Contradictory or vague purposes | Agents confused about tool selection | Each tool gets one clear, well-defined purpose |
| Overly technical identifiers | Increased hallucination risk | Use natural language identifiers |
| Missing "when to use" guidance | Tool may never be invoked | Explicitly state invocation triggers |
| Conflicting with other tools | Agent selects wrong tool | Differentiate clearly from related tools |

---

## 3. Parameter Documentation

### 3.1 Input Schema Best Practices

**Use Semantic Names**
- Prefer `user_id` over generic `user` or `id`
- Use descriptive names that convey purpose: `search_query`, `max_results`, `include_archived`

**Provide Parameter Descriptions**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query using natural language. Supports quoted phrases for exact matches."
    },
    "limit": {
      "type": "integer",
      "description": "Maximum number of results to return (1-100). Defaults to 10.",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    }
  }
}
```

**Include Examples**
- Add example values in descriptions: `"City name (e.g., 'New York') or zip code (e.g., '10001')"`
- Show format patterns for structured input: `"Date in ISO 8601 format (YYYY-MM-DD)"`

**Mark Required Fields**
- Always specify the `required` array explicitly
- Document why fields are required if not obvious

### 3.2 Output Schema Best Practices

Providing output schemas offers several benefits:
- Enables strict schema validation of responses
- Provides type information for programming language integration
- Guides clients and LLMs to properly parse returned data
- Supports better documentation and developer experience

**Example:**
```json
{
  "outputSchema": {
    "type": "object",
    "properties": {
      "temperature": {
        "type": "number",
        "description": "Temperature in Celsius"
      },
      "conditions": {
        "type": "string",
        "description": "Human-readable weather conditions (e.g., 'Partly cloudy')"
      }
    },
    "required": ["temperature", "conditions"]
  }
}
```

---

## 4. Tool Annotations

Annotations communicate tool behavior to clients without consuming token context. MCP servers should provide all applicable annotations.

### 4.1 Standard Annotations

| Annotation | Type | Default | Purpose |
|------------|------|---------|---------|
| `title` | string | — | Human-readable display name |
| `readOnlyHint` | boolean | false | Tool only reads data, never modifies |
| `destructiveHint` | boolean | true | Tool may perform destructive/irreversible updates |
| `idempotentHint` | boolean | false | Repeated calls with same args have no additional effect |
| `openWorldHint` | boolean | false | Tool may interact with external entities |

### 4.2 Usage Guidelines

**Read-Only Tools**
```json
{
  "annotations": {
    "readOnlyHint": true
  }
}
```
- Allows clients to skip confirmation prompts for safe operations
- Appropriate for search, lookup, and data retrieval operations

**Destructive Tools**
```json
{
  "annotations": {
    "readOnlyHint": false,
    "destructiveHint": true
  }
}
```
- Signals operations that cannot be undone (delete, overwrite)
- Clients typically require user confirmation

**Idempotent Modifying Tools**
```json
{
  "annotations": {
    "readOnlyHint": false,
    "destructiveHint": false,
    "idempotentHint": true
  }
}
```
- Safe to retry without additional side effects
- Appropriate for "set" or "update" operations with defined end states

### 4.3 Important Caveats

- Annotations are **hints**, not guarantees—they are informational only
- Clients should not blindly trust annotations from untrusted servers
- The `destructiveHint` and `idempotentHint` are only meaningful when `readOnlyHint` is false

---

## 5. Naming Conventions

### 5.1 Tool Names

| Rule | Rationale |
|------|-----------|
| Maximum 64 characters | Enforced by Anthropic MCP Directory |
| Use snake_case | Common convention in MCP ecosystem |
| Start with verb | Indicates action: `get_`, `create_`, `update_`, `delete_`, `search_` |
| Be specific | `get_user_profile` not `get_user` |

### 5.2 Namespacing

For servers with many tools, use prefixes to group related functionality:

```
# By service
asana_search_tasks
jira_search_issues

# By resource
projects_list
projects_create
users_search
users_get
```

Namespacing helps agents:
- Select the right tools at the right time
- Understand tool relationships
- Navigate large tool sets efficiently

---

## 6. Response Design

### 6.1 High-Signal Content

- Return only high-signal information, prioritizing contextual relevance
- Replace low-level technical fields (`uuid`, `mime_type`) with semantically meaningful ones (`name`, `file_type`)
- Natural language identifiers significantly reduce agent hallucinations

### 6.2 Handling Large Results

Implement pagination, filtering, or truncation with sensible defaults:

```json
{
  "results": [...],
  "total_count": 1523,
  "next_cursor": "abc123",
  "message": "Showing first 20 of 1523 results. Use 'next_cursor' for more, or refine your search query for targeted results."
}
```

Include helpful guidance in truncated responses directing agents toward more efficient strategies.

### 6.3 Error Messages

Provide actionable error messages rather than opaque codes:

**Poor:**
```json
{
  "error": "E_INVALID_PARAM",
  "code": 400
}
```

**Better:**
```json
{
  "error": "Invalid date format. Expected ISO 8601 (YYYY-MM-DD), received '12/25/2024'. Example: '2024-12-25'",
  "field": "start_date",
  "suggestion": "Convert the date to ISO 8601 format"
}
```

---

## 7. Security Considerations

### 7.1 Documentation Security

- Never expose sensitive implementation details in descriptions
- Don't document internal endpoints or credentials handling in tool descriptions
- Use `Depends()` patterns to inject runtime credentials without exposing them in schemas

### 7.2 Server Requirements

- Validate all tool inputs against the declared schema
- Implement proper access controls
- Rate limit tool invocations
- Sanitize tool outputs

### 7.3 Human-in-the-Loop

MCP specification requires:
- UI showing which tools are exposed to the AI model
- Clear visual indicators when tools are invoked
- Confirmation prompts for sensitive operations
- Always maintain human ability to deny tool invocations

---

## 8. Testing and Validation

### 8.1 Description Effectiveness Testing

- Test that agents correctly select your tool over alternatives
- Verify agents use the tool at appropriate times (not over- or under-invoking)
- Measure error rates caused by parameter misunderstanding

### 8.2 Schema Validation

- Validate all inputs against declared JSON schemas
- Test edge cases in parameter constraints
- Verify output conforms to declared output schemas

### 8.3 Multi-Layer Testing Strategy

| Layer | Focus |
|-------|-------|
| Unit tests | Individual tool execution |
| Integration tests | Tool interaction with external systems |
| Contract tests | Protocol compliance |
| Load tests | Concurrent behavior |

---

## 9. Checklist for Tool Documentation

Before deploying an MCP tool, verify:

- [ ] Tool name is under 64 characters and follows naming conventions
- [ ] Description clearly states what the tool does
- [ ] Description explains when to invoke the tool
- [ ] Description differentiates from related tools
- [ ] All parameters have descriptions
- [ ] Required fields are marked in schema
- [ ] Examples provided for complex parameters
- [ ] Appropriate annotations set (readOnlyHint, destructiveHint, etc.)
- [ ] Output schema provided for structured responses
- [ ] Error responses are actionable and informative
- [ ] No sensitive information exposed in documentation

---

## References

### Official Specifications

1. [MCP Tools Specification (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) - Official protocol specification for tool definitions, schemas, and error handling.

2. [Model Context Protocol Documentation](https://modelcontextprotocol.info/docs/) - Community documentation hub with concepts and examples.

3. [MCP GitHub Repository](https://github.com/modelcontextprotocol/modelcontextprotocol) - Source of truth for TypeScript and JSON schemas.

### Anthropic Guidelines

4. [Anthropic MCP Directory Policy](https://support.claude.com/en/articles/11697096-anthropic-mcp-directory-policy) - Official requirements for MCP servers in Anthropic's directory.

5. [Writing Tools for Agents (Anthropic Engineering)](https://www.anthropic.com/engineering/writing-tools-for-agents) - Best practices from Anthropic's engineering team on tool description optimization.

### Implementation Guides

6. [MCP Best Practices: Architecture & Implementation Guide](https://modelcontextprotocol.info/docs/best-practices/) - Production-oriented guidance for MCP server development.

7. [FastMCP Tools Documentation](https://gofastmcp.com/servers/tools) - Practical guide to tool annotations and parameter documentation with Python examples.

8. [MCPcat: Adding Custom Tools Guide](https://mcpcat.io/guides/adding-custom-tools-mcp-server-python/) - Step-by-step tutorial with annotation examples.

### Additional Resources

9. [MCP Tool Schema Explained (Merge)](https://www.merge.dev/blog/mcp-tool-schema) - Deep dive into schema structure and design patterns.

10. [MCP Tool Annotations Introduction (Marc Nuri)](https://blog.marcnuri.com/mcp-tool-annotations-introduction) - Practical exploration of annotation usage and implications.

---

*Report compiled: December 2025*
