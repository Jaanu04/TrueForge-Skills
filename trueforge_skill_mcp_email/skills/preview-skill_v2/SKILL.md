---
name: preview-skill-v2
description: Handles Resulticks Email preview generation and sending test previews using the verified Email draft and MCP tools.
---

# Email Preview Skill

Use this skill when the user asks to preview an Email or send a test preview.

## Source of truth

Current Email MCP state and preview tool responses are authoritative.

Never invent:
- preview content
- test-send status
- recipient delivery status
- draft verification status

## Preview

When the user asks to preview the Email:

1. Ensure an Email session exists.
2. Check current state using `email_get_state` when needed.
3. Ensure a valid Email draft exists.
4. Call `email_preview`.
5. Return the actual preview result.

Do not pretend a preview was generated without the MCP tool.

## Send test preview

When the user requests a test preview:

1. Check that a valid/canonical Email draft exists.
2. Obtain the intended test recipient if not already available.
3. Call `email_send_test_preview`.
4. Return the MCP tool result.

Do not ask for scheduling time for a test preview.

A test preview should be sent once the required test-preview information is available.

## Recipient handling

Do not invent recipients.

Do not silently change recipient values.

Use the recipient supplied by the user/current state.

Do not assume every recipient is an Email address unless the Email MCP flow specifically requires that format.

## Execution rule

Loading this skill is NOT completion.

For an actual preview request, call `email_preview`.

For an actual test-send request, call `email_send_test_preview`.

## Error handling

If preview/test-send fails:
- show the actual MCP/tool failure
- do not claim that it was sent
- do not fabricate delivery confirmation
