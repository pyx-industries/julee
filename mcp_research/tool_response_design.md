# Deep Dive: Response Design for MCP Tools

A comprehensive research report on designing high-quality tool responses for AI agents, with emphasis on high-signal content, token efficiency, and cognitive optimization.

---

## Executive Summary

Tool response design is one of the most impactful yet underappreciated aspects of MCP server development. Research from Anthropic demonstrates that response quality directly affects agent accuracy, with simple changes like replacing UUIDs with semantic identifiers reducing error rates from ~50% to under 5%.

This report explores the science and practice of designing tool responses that maximize agent effectiveness while minimizing token costs and cognitive overhead.

---

## 1. The High-Signal Content Principle

### 1.1 Core Definition

High-signal content prioritizes **contextual relevance over flexibility** and returns only information that directly informs agents' downstream actions. The goal is finding "the smallest set of high-signal tokens that maximize the likelihood of your desired outcome."

### 1.2 What Makes Content High-Signal?

| High-Signal | Low-Signal |
|-------------|------------|
| `name: "project-alpha"` | `uuid: "a3f8c2b1-..."` |
| `file_type: "python"` | `mime_type: "text/x-python"` |
| `image_url: "https://..."` | `256px_image_url`, `512px_image_url`, `1024px_image_url` |
| `status: "active"` | `status_code: 1` |
| `created: "2 days ago"` | `created_at: "2025-12-17T14:32:11.847Z"` |

### 1.3 The Signal-to-Noise Ratio

Every token in a tool response competes for attention in the agent's context window. Low-signal content:
- Consumes tokens without aiding decision-making
- Creates "attention deserts" that dilute focus on important data
- Increases probability of the agent missing critical information

**Principle**: If a field wouldn't help a human engineer make the next decision, it probably won't help an AI agent either.

---

## 2. The UUID Problem

### 2.1 Why UUIDs Fail in Agent Contexts

UUIDs represent one of the most common anti-patterns in tool response design. Research from BAML demonstrates the severity:

| Identifier Type | Tokens per ID | Error Rate (200 items) |
|-----------------|---------------|------------------------|
| UUID | 24 tokens | ~50% (29-68 errors) |
| Integer | 1 token | ~3% (5-7 errors) |
| Remapped UUID→Int | 1 token | ~2.5% (5-6 errors) |

### 2.2 Why This Happens

LLMs generate tokens probabilistically—they have no algorithmic mechanism to ensure uniqueness or accuracy when reproducing high-entropy strings. UUIDs cause:

- **Token bloat**: 24 tokens per UUID vs. 1 token for integers
- **Reproduction errors**: Typos, truncations, and dropped characters
- **Hallucination**: LLMs fabricate plausible-looking UUIDs that don't exist

### 2.3 Solutions

**Solution 1: Semantic Identifiers**

Replace UUIDs with human-readable names when possible:

```json
// Before (low-signal)
{
  "user_id": "a3f8c2b1-9d4e-4f5a-8b7c-1234567890ab",
  "project_id": "b2c9d8e7-6f5a-4b3c-2d1e-0987654321ba"
}

// After (high-signal)
{
  "user": "alice.chen",
  "project": "api-redesign"
}
```

**Solution 2: Index Remapping**

When UUIDs are required downstream, remap them to sequential integers:

```python
# Before sending to LLM
uuid_map = {uuid: idx for idx, uuid in enumerate(unique_uuids)}
data_for_llm = replace_uuids_with_indices(data, uuid_map)

# After receiving LLM response
response = replace_indices_with_uuids(llm_response, uuid_map)
```

**Solution 3: Dual Representation**

Provide both when downstream systems require UUIDs:

```json
{
  "id": 42,
  "uuid": "a3f8c2b1-...",
  "name": "Project Alpha"
}
```

The agent uses `id` or `name` for reasoning; your system uses `uuid` for database operations.

---

## 3. The "Lost in the Middle" Problem

### 3.1 The U-Shaped Attention Curve

Research by Liu et al. (2023) revealed a critical limitation: LLMs exhibit U-shaped retrieval accuracy. Performance is highest when relevant information appears at the **beginning or end** of context, with significant degradation for middle positions.

```
Performance
    |
100%|  *                                              *
    |   *                                            *
    |    **                                        **
    |      ***                                  ***
    |         *****                        *****
    |              ********          ******
 50%|                      **********
    |
    +------------------------------------------------→
      Start              Middle                  End
                   Document Position
```

### 3.2 Implications for Tool Responses

This phenomenon affects multi-document or multi-result tool responses:

| Position | Agent Accuracy |
|----------|----------------|
| First 10% | Highest |
| Middle 50% | Significantly degraded |
| Last 10% | High |

### 3.3 Design Recommendations

**1. Front-Load Critical Information**

Structure responses with the most important data first:

```json
{
  "summary": "3 critical errors found in auth module",
  "top_priority": {
    "file": "auth/login.py",
    "issue": "SQL injection vulnerability",
    "severity": "critical"
  },
  "additional_findings": [...]
}
```

**2. Use Explicit Summaries**

Begin long responses with a summary the agent can use for immediate decision-making:

```json
{
  "result_count": 47,
  "recommendation": "Refine search - too many results for effective analysis",
  "top_3_matches": [...],
  "remaining_matches": [...]
}
```

**3. Limit Result Count**

Research shows optimal performance with fewer, more relevant items:

- Fewer than 10 items: Near-optimal performance
- 10-20 items: Moderate degradation
- 20+ items: Significant accuracy loss

**4. Recency Anchoring**

Place "reminder" summaries at the end of long responses:

```json
{
  "results": [...],
  "context_reminder": {
    "query": "authentication errors in production",
    "total_matches": 47,
    "showing": 10,
    "action_suggested": "Review top_3_matches first"
  }
}
```

---

## 4. Token Efficiency Strategies

### 4.1 The Cost of Context

Token usage directly impacts cost and latency. With Claude Sonnet:
- Uncached tokens: $3.00 / million tokens
- Cached tokens: $0.30 / million tokens (10x cheaper)

Every unnecessary token in tool responses compounds across agent iterations.

### 4.2 Compression Techniques

**Response Format Enum**

Allow agents to request verbosity level:

```json
{
  "name": "search_documents",
  "inputSchema": {
    "properties": {
      "query": { "type": "string" },
      "response_format": {
        "type": "string",
        "enum": ["concise", "detailed"],
        "description": "concise: IDs and titles only (72 tokens). detailed: full metadata (206 tokens)"
      }
    }
  }
}
```

Anthropic found this reduced token usage by 65% for equivalent functionality.

**Progressive Disclosure**

Return lightweight metadata first; let agents request full content:

```json
// Initial response
{
  "documents": [
    { "id": 1, "title": "API Design Guide", "relevance": 0.95 },
    { "id": 2, "title": "Auth Patterns", "relevance": 0.87 }
  ],
  "hint": "Use get_document_content(id) for full text"
}

// Only when needed
{
  "id": 1,
  "content": "... full document text ..."
}
```

**Pagination with Guidance**

For large result sets, paginate and guide efficient usage:

```json
{
  "results": [...first 10...],
  "pagination": {
    "total": 1523,
    "page": 1,
    "per_page": 10,
    "next_cursor": "abc123"
  },
  "efficiency_hint": "1523 results is too many. Add filters (date_range, author, status) or use more specific search terms."
}
```

### 4.3 Restorable Compression

Anthropic advocates for compression that preserves recovery paths:

| Content Type | Can Drop | Must Preserve |
|--------------|----------|---------------|
| Web page content | Yes | URL |
| File contents | Yes | File path |
| API response body | Yes | Endpoint + params |
| Query results | Yes | Query + filters |

This allows context reduction without permanent information loss.

---

## 5. Structured vs. Unstructured Responses

### 5.1 The Case for Structure

MCP supports both unstructured (`content` field) and structured (`structuredContent` field) responses. Industry consensus strongly favors structured data:

**Problems with Unstructured Text:**
- Forces brittle text parsing
- Prone to extraction errors
- Inconsistent across invocations
- Difficult for agents to reliably process

**Benefits of Structured Data:**
- Machine-readable and parseable
- Schema-validated consistency
- Type-safe integration with code
- Enables automated workflows

### 5.2 MCP Dual-Format Pattern

For backwards compatibility, provide both:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"temperature\": 22.5, \"conditions\": \"Partly cloudy\"}"
    }
  ],
  "structuredContent": {
    "temperature": 22.5,
    "conditions": "Partly cloudy",
    "humidity": 65,
    "wind_speed_kmh": 12
  }
}
```

### 5.3 Output Schema Benefits

Defining an `outputSchema` provides:

1. **Validation**: Servers must conform; clients can validate
2. **Documentation**: Schema serves as response specification
3. **Type Safety**: Enables typed language integration
4. **Predictability**: Agents know exactly what to expect

```json
{
  "name": "get_user_profile",
  "outputSchema": {
    "type": "object",
    "properties": {
      "username": { "type": "string" },
      "email": { "type": "string", "format": "email" },
      "role": { "type": "string", "enum": ["admin", "user", "guest"] },
      "active": { "type": "boolean" }
    },
    "required": ["username", "email", "role", "active"]
  }
}
```

---

## 6. Audience-Aware Content Routing

### 6.1 The Audience Annotation

MCP supports content annotations specifying intended audience:

```json
{
  "type": "resource",
  "resource": {
    "uri": "file:///logs/error.log",
    "text": "... log content ...",
    "annotations": {
      "audience": ["assistant"],
      "priority": 0.9
    }
  }
}
```

### 6.2 Audience Types

| Audience | Purpose | Example |
|----------|---------|---------|
| `["assistant"]` | Technical data for model reasoning | Raw API responses, debug info |
| `["user"]` | Display content for human consumption | Formatted summaries, visualizations |
| `["user", "assistant"]` | Relevant to both parties | Search results, file contents |

### 6.3 Priority Weighting

The `priority` annotation (0.0-1.0) indicates relative importance:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Critical: Authentication service is down",
      "annotations": { "priority": 1.0, "audience": ["user", "assistant"] }
    },
    {
      "type": "text",
      "text": "Debug trace: connection timeout at 14:32:11...",
      "annotations": { "priority": 0.3, "audience": ["assistant"] }
    }
  ]
}
```

Clients can use these hints for sorting, filtering, and presentation.

---

## 7. Error Response Design

### 7.1 Actionable Over Opaque

Error responses should enable agents to self-correct:

**Poor Design:**
```json
{
  "error": "E_INVALID_PARAM",
  "code": 400
}
```

**Better Design:**
```json
{
  "error": true,
  "message": "Invalid date format in 'start_date' parameter",
  "expected": "ISO 8601 format (YYYY-MM-DD)",
  "received": "12/25/2024",
  "example": "2024-12-25",
  "suggestion": "Convert date to ISO 8601 format before retrying"
}
```

### 7.2 Error Response Structure

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "..."
    }
  ],
  "structuredContent": {
    "error_type": "validation_error",
    "field": "email",
    "constraint": "format",
    "message": "Invalid email format",
    "valid_examples": ["user@example.com", "name.surname@company.org"],
    "recovery_action": "Verify email contains @ symbol and valid domain"
  }
}
```

### 7.3 MCP Error Reporting Principle

Tool errors should be reported within the result object (with `isError: true`), not as MCP protocol-level errors. This allows the LLM to see and potentially handle the error gracefully.

---

## 8. Multi-Content Responses

### 8.1 Content Type Selection

MCP supports multiple content types in a single response:

| Type | Use Case |
|------|----------|
| `text` | Primary response content, explanations |
| `image` | Visualizations, screenshots, charts |
| `audio` | Voice responses, audio data |
| `resource` | Embedded file/document content |
| `resource_link` | Reference to fetchable resource |

### 8.2 Combining Content Types

```json
{
  "content": [
    {
      "type": "text",
      "text": "Analysis complete. Found 3 performance bottlenecks."
    },
    {
      "type": "image",
      "data": "base64-encoded-flame-graph...",
      "mimeType": "image/png",
      "annotations": { "audience": ["user"] }
    },
    {
      "type": "resource_link",
      "uri": "file:///reports/perf-analysis.json",
      "name": "Detailed Analysis",
      "description": "Full performance metrics in JSON format",
      "annotations": { "audience": ["assistant"] }
    }
  ]
}
```

### 8.3 When to Use Each Type

- **Text**: Always include for LLM reasoning
- **Images**: User-facing visualizations (charts, diagrams)
- **Resource Links**: When full content isn't needed immediately
- **Embedded Resources**: When content is essential for reasoning

---

## 9. Response Design Patterns

### 9.1 The Summary-Detail Pattern

```json
{
  "summary": {
    "status": "success",
    "items_processed": 47,
    "items_failed": 2,
    "action_required": true
  },
  "failures": [
    { "id": 12, "reason": "Invalid format", "fix": "Convert to UTF-8" },
    { "id": 31, "reason": "Missing field", "fix": "Add 'email' field" }
  ],
  "successes_sample": [
    { "id": 1, "result": "imported" },
    { "id": 2, "result": "imported" }
  ],
  "full_results_path": "/tmp/import-results-20251219.json"
}
```

### 9.2 The Guidance Pattern

Include explicit guidance for efficient agent behavior:

```json
{
  "results": [...],
  "agent_guidance": {
    "result_quality": "low",
    "reason": "Query too broad - 1523 matches",
    "suggested_refinements": [
      "Add date filter: created_after='2025-01-01'",
      "Add status filter: status='active'",
      "Use more specific terms: 'authentication error' instead of 'error'"
    ],
    "alternative_approach": "Try search_by_category('auth') for targeted results"
  }
}
```

### 9.3 The Contextual Reminder Pattern

Combat "lost in the middle" with context anchoring:

```json
{
  "original_query": "Find all users with failed login attempts",
  "results": [... long list ...],
  "context_anchor": {
    "query_restated": "Users with failed logins",
    "result_count": 47,
    "recommended_action": "Review first 5 results which have highest failure counts",
    "next_step": "Use lock_user_account(user_id) for accounts exceeding threshold"
  }
}
```

---

## 10. Testing Response Quality

### 10.1 Metrics to Track

| Metric | What It Measures |
|--------|------------------|
| Token count | Response efficiency |
| Agent accuracy | Correct tool usage |
| Retry rate | Error recovery |
| Time to completion | End-to-end efficiency |
| Hallucination rate | Identifier accuracy |

### 10.2 A/B Testing Responses

Compare response formats empirically:

```python
# Test configuration
variants = {
    "uuid_raw": {"id_format": "uuid"},
    "uuid_mapped": {"id_format": "integer", "uuid_in_metadata": True},
    "semantic": {"id_format": "name"}
}

# Measure per variant
metrics = ["accuracy", "tokens_used", "retries", "completion_time"]
```

### 10.3 Common Issues Checklist

- [ ] UUIDs replaced with semantic or indexed identifiers
- [ ] Critical information appears at start of response
- [ ] Token count reasonable for task (<1000 for simple operations)
- [ ] Errors include actionable recovery guidance
- [ ] Pagination implemented for large result sets
- [ ] Response format enum available for verbosity control
- [ ] Output schema defined for structured responses
- [ ] Audience annotations set appropriately

---

## 11. Summary: Response Design Principles

1. **Maximize Signal**: Return only information that aids decision-making
2. **Avoid UUIDs**: Use semantic identifiers or index remapping
3. **Front-Load**: Put critical information at the start
4. **Limit Results**: Fewer, more relevant items outperform exhaustive lists
5. **Enable Compression**: Support response format toggles
6. **Structure Data**: Prefer JSON over free-text
7. **Guide Recovery**: Make errors actionable
8. **Annotate Audience**: Route content appropriately
9. **Anchor Context**: Include reminders in long responses
10. **Measure Impact**: A/B test response formats

---

## References

### Anthropic Engineering

1. [Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents) - Authoritative guide on high-signal responses, response format enums, and token efficiency.

2. [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) - Context compression, just-in-time retrieval, and tool output design principles.

### Academic Research

3. [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) - Liu et al. (2023). Foundational research on U-shaped attention patterns.

4. [Arize AI: Lost in the Middle Paper Reading](https://arize.com/blog/lost-in-the-middle-how-language-models-use-long-contexts-paper-reading/) - Practical analysis with performance charts and statistics.

### Technical Implementation

5. [Using UUIDs in Prompts is Bad (BAML)](https://boundaryml.com/blog/uuid-swap) - Quantitative research on UUID error rates and remapping solutions.

6. [Context Engineering for AI Agents: Lessons from Building Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) - Production lessons on KV-cache optimization and response design.

### MCP Specification

7. [MCP Tools Specification (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) - Official protocol for content types, annotations, and structured responses.

8. [MCP Response Formatting Best Practices](https://www.byteplus.com/en/topic/541423) - Structured vs. unstructured response patterns.

### Additional Resources

9. [The Context Window Paradox (Voiceflow)](https://www.voiceflow.com/pathways/the-context-window-paradox-why-bigger-might-not-be-better) - Why larger context windows don't automatically improve performance.

10. [LLMs as Unreliable Narrators: Dealing with UUID Hallucination](https://dev.to/nikhilverma/llms-as-unreliable-narrators-dealing-with-uuid-hallucination-151e) - Practical strategies for identifier management.

11. [Reducing LLM Hallucinations (Zep)](https://www.getzep.com/ai-agents/reducing-llm-hallucinations/) - Broader context on hallucination mitigation strategies.

---

*Report compiled: December 2025*
