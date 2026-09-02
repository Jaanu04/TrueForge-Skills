---
name: email-creative-skill
description: Manages the Resulticks Email creative lifecycle after setup is validated- Communication Details confirmation, Generate New EDM, Uploaded EDM HTML, Existing EDM templates, preview, edit, and revert. Use when an Email user confirms setup or asks to create, change, view, or select creative content.
---

# Email Creative

Do not start creative generation until Product, Communication Type, and Audience are validated and `email_review_setup` has been shown.

After explicit setup confirmation, allow one source:
- Generate New EDM -> `email_generate_edm`
- Upload EDM -> `email_use_uploaded_edm`
- Existing EDM -> `email_list_existing_edms` then `email_select_existing_edm`

For a saved creative:
- View -> `email_preview`
- Edit -> `email_edit`
- Revert -> `email_revert`

Never invent template IDs or HTML.
