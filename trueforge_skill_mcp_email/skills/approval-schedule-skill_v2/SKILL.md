---
name: approval-schedule-skill
description: Handles Resulticks Email Request for Approval and schedule or publish requests while enforcing the mandatory RFA path. Use when a user asks to send for approval, provides an approver, asks to schedule or publish or send later, or asks about approval or schedule status.
---

# Email Approval & Scheduling

Direct Email scheduling is not exposed in this POC. Every schedule, publish, blast, or send-later request must enter or continue the RFA workflow.

Before RFA:
- saved draft must exist;
- approver email must be valid;
- intended schedule datetime must be present.

Use `email_request_approval` for explicit RFA, `email_schedule_request` for schedule/publish requests, and `email_get_status` for current lifecycle status. Never claim RFA submission means already scheduled.
