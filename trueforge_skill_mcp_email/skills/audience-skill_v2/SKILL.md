---
name: audience-skill
description: Finds and validates Resulticks audience/list selections for Email and persists canonical audience ID/count through MCP. Use when the user supplies an audience, asks for available audiences, changes the audience, or when audience is the remaining Email setup requirement.
---

# Audience Selection

- Treat audience/list as a backend catalogue value, never free-form state.
- Validate supplied names with `email_validate_audience`.
- On ambiguity, use only API-backed candidates or `email_list_audiences`.
- Do not re-ask an audience already validated in `email_get_state`.
