---
name: workflow-brain-skill-v2
description: Mandatory first-entry orchestration Skill for every Resulticks Email business request. It checks MCP workflow state and policy before any specialised Skill is used, prevents step skipping, requires explicit user confirmation before starting missing prerequisite flows, determines the next allowed milestone, and routes only permitted work to downstream Email Skills.
---

# Resulticks Email Workflow Brain Skill

This is the mandatory orchestration Skill for every Resulticks Email business request.

The MCP policy/state is the canonical source of truth. This Skill guides the conversation and routing; it must never invent, assume, or duplicate backend workflow state.

## Shared-state / no-repeat rule

MCP state is the only authoritative memory for workflow fields across Brain and worker Skills.

- On the first Resulticks Email business request of a brand-new TrueForge chat, call `email_start_session(force_new=true)` exactly once.
- After that, never create another session for the same chat. Reuse the current `spaceid`.
- If a worker Skill does not receive the parent `spaceid`, it must call `email_start_session(force_new=false)` to resume the active MCP session, then reuse the returned `spaceid`.
- Never display `spaceid` to the user.
- Before asking for Product, Communication Type, Audience, Communication Name, EDM, Sender, or other workflow data, call `email_get_workflow_state`.
- Read `collected_fields`, `missing_fields`, and `next_required_field`.
- Never ask again for any non-empty value in `collected_fields`.
- Ask only for values in `missing_fields`, one logical checkpoint at a time.
- If the user supplies one or more setup values in a message, immediately call `email_capture_setup_values` with every supplied value. Do not keep those values only in conversational text.
- After capturing values, use the returned `workflow_state` before asking the next question.

## Mandatory first-entry rule

For every Resulticks Email business request, use this Brain Skill before specialised Email Skills whenever TrueForge routing permits it.

Specialised Skills are workers, not workflow authorities. Even if TrueForge directly selects a specialised Skill, that Skill must still check MCP policy and obey the same stop-and-ask rules.

Required orchestration:

`User request -> workflow-brain-skill-v2 -> MCP state/policy -> allowed action -> specialised Skill`

## Core responsibility

For every Email request:

1. Ensure one Email session exists. Use `email_start_session(force_new=true)` only once for the first business request of a new TrueForge chat; otherwise resume/reuse with `force_new=false` or the existing `spaceid`.
2. Reuse the returned `spaceid` on every later MCP call. Never ask the user for it and never display it.
3. Identify the user's requested action.
4. Call `email_get_workflow_state` with that exact `spaceid` and the explicit `requested_action` whenever the request maps to a guarded workflow action.
5. Read `requested_action_decision`, `allowed_actions`, `blocked_actions`, `missing_milestones`, `next_action`, `requires_user_confirmation`, and `auto_execute_prerequisites`.
6. If the action is allowed, route only that allowed work to the specialised Skill.
7. If the action is blocked, do not call the blocked downstream tool.
8. If `requires_user_confirmation=true`, do not automatically execute any missing prerequisite flow. Ask the user whether they want to start the prerequisite flow and STOP.
9. Only after the user explicitly confirms may you call `email_confirm_prerequisite_flow(confirmed=true, spaceid=...)` and then begin the prerequisite workflow.
10. If the user declines, call `email_confirm_prerequisite_flow(confirmed=false, spaceid=...)` and stop.
11. After any state-changing MCP call, use the returned state/status or refresh with `email_get_workflow_state` before deciding the next action.

## Mandatory core sequence

The normal Email creation sequence is:

`Communication details -> Confirm details -> EDM -> Sender -> Create communication`

Post-create actions such as Test Preview and Request for Approval are allowed only after MCP policy reports that the communication is created.

The exact prerequisites and allowed actions are defined by MCP policy/config. If this Skill and MCP policy ever disagree, MCP policy wins.

## Explicit prerequisite confirmation rule

When a user requests a downstream action that is blocked because an earlier workflow milestone is incomplete:

1. Do not automatically execute the prerequisite workflow.
2. Do not collect Product, Communication Type, Audience, EDM, Sender, approver, recipient, or other prerequisite inputs yet.
3. Do not invoke specialised prerequisite Skills yet.
4. Explain which prerequisite is required.
5. Ask the user whether they want to start that prerequisite flow.
6. STOP and wait for an explicit answer.

Only explicit user confirmation such as `Yes`, `Proceed`, `Continue`, or `Create the communication` permits prerequisite work to start.

After explicit confirmation, call:

`email_confirm_prerequisite_flow(confirmed=true, spaceid=<current spaceid>)`

before invoking Product/Audience/Creative/Sender/Create Communication tools.

Do not infer confirmation from the original downstream request.

### Example: Test Preview

User: `Send a test preview to user@example.com`

Correct:

1. Start/reuse session.
2. Call `email_get_workflow_state(spaceid=..., requested_action="send_test_preview")`.
3. If communication is not created and the response requires confirmation, say:
   `The Email communication must be created before a Test Preview can be sent. Would you like me to start the communication creation flow?`
4. STOP.
5. If the user says yes, call `email_confirm_prerequisite_flow(confirmed=true, ...)`.
6. Only then start the current prerequisite milestone.

Incorrect:

`Send Test Preview -> Product -> Audience -> EDM -> Sender -> Create Communication`

without an explicit user confirmation between the blocked Test Preview request and the creation flow.

## No-shortcut rule

Never convert a downstream request into silent prerequisite execution.

If `send_test_preview`, `request_approval`, `schedule_request`, or another guarded action is blocked:

- do not call the blocked tool
- do not silently create/save the communication
- do not auto-fill or auto-collect missing setup
- do not invent catalogue values
- do not treat the user's downstream request as consent to execute prerequisite business actions

The MCP confirmation gate is authoritative. If prerequisite tools return `user_confirmation_required`, stop and ask the user; never retry/bypass.

## Routing

- Setup/session/review/create communication -> `email-core-skill-v4`
- Product/Sub Product/Communication Type -> `product-catalogue-skill-v4`
- Audience -> `audience-skill-v4`
- EDM/template/edit/revert -> `email-creative-skill-v4`
- View/Test Preview -> `preview-skill-v4`
- RFA/status/scheduling policy -> `approval-schedule-skill-v4`

Loading a Skill is not completion. Execute only MCP actions currently permitted by policy.

## Backend-data safety

Never invent or assume Resulticks catalogue/backend values including Products, Sub Products, Communication Types, Audiences, Senders, templates, EDMs, approvers, Communication IDs, or Campaign IDs.

If an MCP/API call fails, report the actual failure and stop at that milestone. Do not provide model-generated fallback catalogue values unless the user explicitly asks only for examples.

## Policy-blocked responses

If MCP returns `policy_blocked`, `approval_required`, `user_confirmation_required`, or another policy denial:

- do not retry the blocked tool
- read `missing`, `missing_milestones`, `next_action`, `message`, and `requires_user_confirmation`
- explain the required earlier step clearly
- if confirmation is required, ask once and STOP
- never report the blocked action as completed

## State safety

Never call business tools without the explicit current `spaceid`. Never use or infer an older/latest session.

## Final rule

Brain guides. MCP policy enforces. Specialised Skills execute only permitted work.
