---
name: email-core-skill
description: Coordinates Resulticks Email setup, state and lifecycle through the Skill+MCP POC without LangGraph orchestration. Use when a user starts, continues, reviews, or asks the current state of an Email communication; delegate catalogue, creative, preview, and approval details to the matching installed skills.
---

# Resulticks Email Core

## Purpose
Use this skill as the top-level operating guide for the Email Skill+MCP POC. TrueForge owns the conversational agent loop; MCP tools own trusted data/actions; the existing LangGraph graph is not part of this POC path.

## Non-negotiable rules
1. Work only on the `EMAIL` channel in this POC.
2. Start with `email_start_session` and keep the returned `spaceid` unchanged for the whole communication.
3. Before asking for a value, call `email_get_state` when the current state is uncertain. Never re-ask a value already present and validated.
4. Never invent Product, Sub-product, Communication Type, Audience, Template, Campaign ID, Channel Detail ID, Approval Status, or backend success.
5. Use catalogue validation tools before persisting catalogue-backed user values.
6. Ask one focused missing question at a time, but accept several values when the user provides them together.
7. Keep normal conversational responses concise and natural. Do not expose MCP tool names unless the user asks for technical details.
8. The MCP result is authoritative. If a tool reports failure or ambiguity, explain that result and ask only for the required correction.
9. A schedule/publish/send-later request must enter the Email RFA/approval flow. Do not claim direct scheduling.

## Setup sequence
The minimum validated Email setup is Audience, Product, and Communication Type. Sub-product is optional unless explicitly supplied/selected. Other defaults such as goal, benchmark, start date, and end date can come from the existing setup-default layer and remain editable.

When the required setup values are valid:
1. Call `email_review_setup` to show Communication Details.
2. Wait for explicit confirmation or a concrete edit.
3. After confirmation, follow the Email creative skill to choose Generate, Upload, or Existing EDM.
