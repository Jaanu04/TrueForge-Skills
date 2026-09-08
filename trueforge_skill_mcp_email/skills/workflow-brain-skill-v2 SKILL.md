---
name: workflow-brain-skill-v2
description: Mandatory first-entry orchestration Skill for every Resulticks Email business request. It checks MCP workflow state and policy before any specialised Skill is used, prevents step skipping, determines the next allowed milestone, and routes only permitted work to downstream Email Skills.
---

# Resulticks Email Workflow Brain Skill

Use this Skill as the governing orchestration Skill for every Resulticks Email business request.

The MCP policy/state is the canonical source of truth. This Skill guides the conversation; it must not invent or duplicate backend state.

## Core responsibility

For every Email request:

1. Ensure an Email session exists with `email_start_session`.
2. Reuse the returned `spaceid` on every later MCP call. Never ask the user for it.
3. Before any downstream/executable action, call `email_get_workflow_state` using that exact `spaceid`.
4. Identify the user's requested action and compare it with `allowed_actions` / `blocked_actions`.
5. If the action is blocked, do **not** call that downstream tool and do **not** automatically execute missing prerequisite actions just to reach the requested action.
6. Explain the prerequisite in user-facing language and continue with the required earlier milestone only when appropriate to the user's request.
7. Route the current milestone to the specialised Skill.
8. After a state-changing MCP call, use the returned state/status (or refresh with `email_get_workflow_state`) before deciding the next action.
## Mandatory entry point

All Resulticks Email business requests must first pass through this Brain Skill.

Do not directly delegate a user request to specialised Skills such as:

- `preview-skill-v4`
- `approval-schedule-skill-v4`
- `email-creative-skill-v4`
- `audience-skill-v4`
- `product-catalogue-skill-v4`

First:

1. Use this Brain Skill.
2. Check the current workflow state.
3. Check whether the requested action is allowed.
4. Only then delegate to the appropriate specialised Skill.

Specialised Skills are workers, not workflow entry points.

## Mandatory core sequence

The normal Email creation sequence is:

`Communication details -> Confirm details -> EDM -> Sender -> Create communication`

Post-create actions such as Test Preview and Request for Approval are allowed only after MCP policy reports that the communication is created.

The exact prerequisites and allowed actions are defined by MCP policy/config. If this Skill text and MCP policy ever disagree, MCP policy wins.

## No-shortcut rule

Never convert a downstream request into silent prerequisite execution.

Example:

User: "Send a test preview to user@example.com"

- First check `email_get_workflow_state`.
- If `send_test_preview` is blocked because `communication_created` is missing, do **not** call `email_send_test_preview`.
- Do **not** silently create/save the communication.
- Tell the user the Email communication must be created first and guide them to the current required milestone.

The same rule applies to RFA, scheduling, and any future guarded action.

## Routing

- Setup/session/review/create communication -> `email-core-skill-v4`
- Product/Sub Product/Communication Type -> `product-catalogue-skill-v4`
- Audience -> `audience-skill-v4`
- EDM/template/edit/revert -> `email-creative-skill-v4`
- View/Test Preview -> `preview-skill-v4`
- RFA/status/scheduling policy -> `approval-schedule-skill-v4`

Loading a Skill is not completion. Execute only MCP actions currently permitted by policy.

## Policy-blocked responses

If an MCP tool returns `policy_blocked`, `approval_required`, or another policy denial:

- Do not retry the same blocked tool.
- Read `missing`, `missing_milestones`, `next_action`, and `message`.
- Explain the required earlier step clearly.
- Never report the blocked action as completed.

## State safety

Never call business tools without the explicit current `spaceid`. Never use or infer an older/latest session.
