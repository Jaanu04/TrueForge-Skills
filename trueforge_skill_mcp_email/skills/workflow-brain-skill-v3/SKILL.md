---
name: workflow-brain-skill-v3
description: Mandatory first-entry orchestration Skill for every Resulticks Email business request. It must be invoked before any specialised Email Skill. It checks MCP workflow state and policy, prevents step skipping, determines the next allowed milestone, and delegates only permitted work to downstream Skills.
---

# Resulticks Email Workflow Brain Skill

This is the mandatory orchestration Skill for every Resulticks Email business request.

This Skill must always be used before any specialised Email Skill.

The MCP policy/state is the canonical source of truth.

This Skill guides the conversation and routing, but it must never invent, assume, or duplicate backend workflow state.

---

## Mandatory first-entry rule

For every Resulticks Email business request:

**Always invoke this Brain Skill first.**

Do not directly invoke specialised Skills such as:

- `preview-skill-v4`
- `approval-schedule-skill-v4`
- `email-creative-skill-v4`
- `email-core-skill-v4`
- `audience-skill-v4`
- `product-catalogue-skill-v4`

The specialised Skills are worker Skills only.

They must never be treated as workflow entry points.

Required routing:

`User Request -> workflow-brain-skill-v2 -> MCP workflow state check -> policy decision -> specialised Skill`

Incorrect routing:

`User Request -> specialised Skill`

---

## Core responsibility

For every Resulticks Email business request:

1. Understand the user's requested action.
2. Ensure an Email workflow session exists.
3. If no session exists, call `email_start_session`.
4. Store and reuse the returned `spaceid`.
5. Never ask the user for `spaceid`.
6. Before any downstream or executable action, call `email_get_workflow_state` using the current `spaceid`.
7. Read:
   - `current_step`
   - `completed_steps`
   - `allowed_actions`
   - `blocked_actions`
   - `missing`
   - `missing_milestones`
   - `next_action`
8. Compare the user's requested action with MCP policy.
9. If the requested action is allowed, route to the appropriate specialised Skill.
10. If the requested action is blocked, stop the downstream action.
11. Explain what prerequisite must be completed first.
12. Do not automatically execute missing prerequisites simply to reach the user's requested action.
13. After any state-changing MCP call, use the returned state or call `email_get_workflow_state` again before continuing.

---

## Mandatory workflow-state check

Before delegating to any specialised Skill that may perform a business action, always perform:

`email_get_workflow_state`

using the active `spaceid`.

Examples of actions requiring workflow-state validation:

- generate EDM
- select sender
- create communication
- view communication
- send test preview
- request approval
- schedule communication
- edit communication
- revert communication

Never assume that an action is allowed based only on the user's words.

---

## Mandatory core sequence

The normal Email communication creation flow is:

`Start Session`

-> `Communication Details`

-> `Confirm Details`

-> `EDM`

-> `Sender`

-> `Create Communication`

Only after the MCP policy reports that the communication is successfully created can post-create actions be considered.

Post-create actions include:

- View
- Test Preview
- Request for Approval
- Scheduling

The exact prerequisites and allowed actions are controlled by MCP policy/config.

If this Skill and MCP policy ever disagree:

**MCP policy always wins.**

---

## No-shortcut rule

Never skip mandatory milestones.

Never automatically perform missing prerequisite actions merely because the user requested a later action.

Example:

User:

`Send a test preview to user@example.com`

Correct behavior:

1. Invoke this Brain Skill.
2. Ensure a session exists.
3. Call `email_get_workflow_state`.
4. Check whether `send_test_preview` is in `allowed_actions`.
5. If `send_test_preview` is blocked because `communication_created` is missing:
   - Do not call `preview-skill-v4`.
   - Do not call `email_send_test_preview`.
   - Do not create the communication automatically.
   - Tell the user that the Email communication must first be created.
   - Guide the user to the current required milestone.

Incorrect behavior:

`User -> preview-skill-v4 -> email_send_test_preview`

The same no-shortcut rule applies to:

- Request for Approval
- Scheduling
- View
- Edit
- Revert
- Future guarded actions

---

## Specialised Skill routing

Only route to a specialised Skill after MCP policy says that the current action is allowed.

### Email Core

Use:

`email-core-skill-v4`

For:

- session setup
- communication setup
- communication details
- confirmation
- review
- create communication

---

### Product Catalogue

Use:

`product-catalogue-skill-v4`

For:

- Product
- Sub Product
- Communication Type

---

### Audience

Use:

`audience-skill-v4`

For:

- audience lookup
- audience selection
- audience validation

---

### Email Creative

Use:

`email-creative-skill-v4`

For:

- EDM
- existing templates
- generated EDM
- upload EDM
- edit EDM
- revert EDM

---

### Preview

Use:

`preview-skill-v4`

For:

- View
- Test Preview

Important:

Do not route directly to `preview-skill-v4` until MCP policy confirms that the requested preview action is allowed.

---

### Approval and Scheduling

Use:

`approval-schedule-skill-v4`

For:

- Request for Approval
- approval status
- scheduling

Do not route to this Skill until MCP policy confirms that the requested action is allowed.

---

## Policy-blocked behavior

If MCP returns:

- `policy_blocked`
- `approval_required`
- `prerequisite_required`
- `action_not_allowed`
- or another policy denial

then:

1. Do not retry the same blocked action.
2. Do not delegate to the specialised Skill for that blocked action.
3. Read:
   - `missing`
   - `missing_milestones`
   - `next_action`
   - `message`
4. Explain the prerequisite clearly to the user.
5. Continue only with the required earlier milestone when appropriate.
6. Never claim that the blocked action was completed.

---

## Backend-data safety

Never invent Resulticks catalogue or backend values.

This applies to:

- Products
- Sub Products
- Communication Types
- Audiences
- Sender domains
- Sender addresses
- Templates
- EDMs
- Approvers
- Communication IDs
- Campaign IDs

If an MCP/API call fails:

- report the actual failure
- do not generate fake fallback values
- do not provide assumed catalogue entries
- do not claim the backend returned values that were not returned

Example:

If sender retrieval returns an authentication error:

Correct:

`I could not retrieve the sender list because the Resulticks API returned an authentication error.`

Incorrect:

Inventing sender categories or sender addresses.

---

## Error handling

If an MCP/API call fails:

1. Do not fabricate a successful result.
2. Do not silently switch to guessed data.
3. Do not skip the failed milestone.
4. Report the real error in user-friendly language.
5. Keep the workflow at the same required milestone unless MCP state says otherwise.
6. Retry only when appropriate or when the user requests it.

---

## Session safety

Every MCP business call must use the explicit active `spaceid`.

Never:

- infer an old `spaceid`
- use the latest historical session
- reuse a session from another communication
- fabricate a `spaceid`
- ask the user to manually provide a `spaceid`

If no valid session exists:

call:

`email_start_session`

and use the newly returned `spaceid`.

---

## State-changing action rule

After any action that can modify workflow state, such as:

- confirm setup
- generate/select EDM
- select sender
- create communication
- request approval
- schedule communication
- edit communication

use the returned workflow state if available.

Otherwise immediately call:

`email_get_workflow_state`

before deciding what happens next.

---

## Conversation behavior

Keep the conversation natural and concise.

Do not expose internal policy-engine terminology unless useful.

Instead of saying:

`send_test_preview is blocked because communication_created=false`

say:

`The Email communication needs to be created before a test preview can be sent.`

The Brain Skill should explain what the user needs to do next without exposing unnecessary internal implementation details.

---

## Final orchestration rule

Always follow:

`Understand request`

-> `Brain Skill`

-> `Check MCP workflow state`

-> `Check allowed/blocked actions`

-> `Determine next valid milestone`

-> `Delegate to specialised Skill`

-> `Execute permitted MCP action`

-> `Refresh workflow state`

Never allow:

`User request -> specialised Skill directly`

for Resulticks Email business workflow actions.

The Brain Skill guides.

The MCP policy enforces.

The specialised Skills execute only permitted work.