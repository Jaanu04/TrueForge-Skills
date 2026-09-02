---
name: audience-skill-v2
description: Retrieves, validates and manages Resulticks Audience selections for Email communications using MCP tools.
---

# Audience Skill

Use this skill only when the Email workflow requires Audience discovery, selection or validation.

## Source of truth

Resulticks MCP Audience responses are authoritative.

Never invent:
- Audience names
- Audience IDs
- list names
- recipient counts
- audience metadata

## Audience selection

When Audience is missing:

1. Call `email_list_audiences`.
2. Show only Audience values returned by MCP.
3. Allow the user to choose one of the returned values.
4. Validate the selected/provided value using `email_validate_audience`.
5. Preserve the validated Audience information for the current Email session.

## User-provided Audience

If the user already provides an Audience name:

1. Do not ask them to select from a generic list first.
2. Immediately call `email_validate_audience`.
3. If valid, continue.
4. If invalid, show only MCP-provided alternatives where available.

## Important restrictions

Never:
- create fake audience names
- infer an Audience from Product
- assume an Audience exists
- fabricate audience size/count
- treat free text as validated without MCP validation

## Execution rule

Loading this skill is NOT completion.

After loading this skill, execute `email_list_audiences` or `email_validate_audience` as appropriate.

## Error handling

If the Audience MCP tool fails:
- report the real tool failure
- do not fabricate Audience options
- do not claim validation succeeded
