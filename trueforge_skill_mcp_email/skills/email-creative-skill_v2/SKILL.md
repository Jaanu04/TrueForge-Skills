---
name: email-creative-skill-v2
description: Manages Resulticks Email creative operations including generated EDMs, uploaded EDMs, existing EDM selection, editing and reverting.
---

# Email Creative Skill

Use this skill when the user wants to create, generate, upload, select, edit, review or revert an Email EDM.

## Source of truth

The Email MCP tools and current Email session state are authoritative.

Never invent:
- EDM IDs
- draft IDs
- saved status
- generated HTML
- existing EDM names
- draft verification status

unless returned by the appropriate MCP tool.

## Before creative operations

Before performing a creative action:

1. Ensure an Email session exists.
2. Use `email_get_state` when the current state is required.
3. Ensure required communication setup has been completed/confirmed according to the MCP state.

If required information is missing, ask only for that missing information.

## Generate a new EDM

When the user asks to create/generate a new EDM:

1. Load this skill.
2. Check the current Email state using `email_get_state` if needed.
3. If prerequisites are satisfied, call `email_generate_edm`.
4. Return the actual MCP-generated result.
5. Do not stop after loading this skill.

Never respond with a manually invented EDM specification when `email_generate_edm` should be called.

## Uploaded EDM

When the user wants to use an uploaded EDM:

1. Use `email_use_uploaded_edm`.
2. Preserve the MCP-returned draft/state.
3. Reuse the uploaded EDM later instead of unnecessarily asking for another upload.

## Existing EDM

When the user wants to use an existing EDM:

1. Call `email_list_existing_edms`.
2. Show only returned EDMs.
3. When the user chooses one, call `email_select_existing_edm`.
4. Do not invent EDM names or IDs.

## Edit

When the user requests an edit:

1. Use `email_edit`.
2. Apply only the requested change.
3. Preserve the remaining draft state.
4. Return the tool result.

## Revert

When the user asks to undo/revert:

1. Call `email_revert`.
2. Use the returned canonical/reverted state.
3. Never simulate a revert in text only.

## Important execution rule

Loading this skill is NOT successful completion of a creative request.

A requested executable operation must result in the corresponding MCP tool call.

## Error handling

Never say:

"The email system is unavailable"
or
"I can provide a manual EDM instead"

unless an MCP call actually returned that failure.

If a tool fails:
- surface the actual failure
- do not fabricate a draft
- do not claim an EDM was saved/generated
