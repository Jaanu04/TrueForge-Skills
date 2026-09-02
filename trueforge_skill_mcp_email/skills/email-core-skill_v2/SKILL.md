---
name: email-core-skill-v2
description: Starts and manages the Resulticks Email communication lifecycle, session state, setup review and confirmation. Use this FIRST for any new Email communication request.
---

# Email Core Skill

Use this skill FIRST whenever the user wants to create, start, continue, review, or manage an Email communication.

## Source of truth

The Resulticks Email MCP tools and their responses are authoritative.

Never invent:
- session state
- IDs
- communication details
- catalogue values
- workflow status
- draft status
- approval status

## New Email communication

When the user asks to create/start an Email communication:

1. Call `email_start_session`.
2. Never ask the user for spaceid.If no spaceid exists, call email_start_session and use the returned spaceid internally.
   Reuse the same spaceid for all subsequent Email MCP calls in that communication lifecycle.
3. Call `email_get_state` when the current workflow state is required.
4. Determine which required setup information is missing.
5. Use the appropriate specialised skill/tool for that missing information.
6. Never create fake selectable values from model knowledge.

Loading this skill is NOT completion of the request.

After loading this skill, continue executing the necessary MCP tools.

## Existing session

If a session already exists:

- Do not unnecessarily create another session.
- Reuse the existing `spaceid`.
- Call `email_get_state` to understand the current state when necessary.
- Continue from the existing workflow state.


## Setup management

Use:

- `email_update_setup` to update collected setup information.
- `email_review_setup` to retrieve/review communication setup.
- `email_confirm_setup` only when the user confirms the setup.

Do not mark setup as confirmed unless the user has actually confirmed it.

## Workflow behaviour

Follow the MCP-returned state.

Do not:
- skip required stages
- assume that setup is complete
- assume that a draft exists
- assume that approval has happened
- schedule directly when approval is required
- invent successful tool results

If required information is missing, ask only for the relevant missing information.

## Error handling

Never tell the user there is a connectivity/system issue unless an MCP tool actually returns a connectivity/system error.

If an MCP tool fails:
- report the actual failure clearly
- do not invent a successful result
- do not fabricate alternative business data
