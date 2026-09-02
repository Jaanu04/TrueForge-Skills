---
name: approval-schedule-skill-v2
description: Handles Resulticks Email Request for Approval, approval lifecycle, status checks and scheduling rules using MCP tools.
---

# Approval and Schedule Skill

Use this skill for Request for Approval, approval state, status and Email scheduling requests.

## Critical workflow rule

There is intentionally NO direct Email scheduling flow that bypasses approval.

Scheduling must follow the Resulticks RFA/approval lifecycle.

Never bypass this rule.

## Source of truth

MCP approval and status responses are authoritative.

Never invent:
- approver details
- approval status
- scheduled status
- approval timestamps
- campaign status

## Request for Approval

When the user asks to submit/request approval:

1. Ensure an Email session exists.
2. Check current workflow state using `email_get_state` if needed.
3. Ensure required setup and draft prerequisites are satisfied.
4. Collect required approval information if missing.
5. Call `email_request_approval`.
6. Return the actual MCP result.

Do not claim approval was requested unless the tool succeeds.

## Scheduling

When the user asks to schedule an Email:

1. Do not attempt direct scheduling.
2. Check the current state.
3. Follow the RFA/approval workflow.
4. Use `email_schedule_request`.
5. Allow MCP/policy logic to decide whether the request can proceed.

Never bypass approval simply because the user says "schedule it now".

## Status

When the user asks for current status:

1. Call `email_get_status`.
2. Return the actual MCP status.
3. Do not infer approval/scheduling state from conversation text alone.

## Important execution rule

Loading this skill is NOT completion.

Approval, scheduling and status requests must execute the corresponding MCP tool.

## Error handling

If approval/scheduling fails:
- provide the actual MCP result
- explain what prerequisite is missing when returned by the tool
- do not fabricate successful approval or scheduling
