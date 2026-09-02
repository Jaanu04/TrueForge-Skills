---
name: product-catalogue-skill
description: Validates Product, optional Sub-product, and Communication Type against live Resulticks catalogues. Use when an Email user supplies, asks to list, changes, or needs help selecting Product, Sub-product, or Communication Type; never infer backend IDs from text.
---

# Product & Communication Type Catalogue

- Validate Product with `email_validate_product`; use `email_list_products` on ambiguity.
- Sub-product is optional unless explicitly supplied or selected. Never auto-select the first child.
- Use `email_list_sub_products` to present API-backed child choices.
- Validate Communication Type with `email_validate_communication_type`; list choices with `email_list_communication_types`.
- Never invent IDs or persist unvalidated catalogue values.
