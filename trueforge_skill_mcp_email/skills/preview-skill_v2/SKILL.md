---
name: preview-skill
description: Handles viewing a saved Email EDM and sending Test Preview messages to a validated recipient. Use when a user asks to view or preview the creative, send or resend a test, or provides the pending Test Preview email address.
---

# Email Preview & Test Preview

- `email_preview` is read-only.
- Test Preview requires a saved draft and a valid recipient.
- Use `email_send_test_preview` and report delivery only from its result.
- After a successful test, ask whether the preview is satisfactory or needs edits; do not auto-submit RFA.
