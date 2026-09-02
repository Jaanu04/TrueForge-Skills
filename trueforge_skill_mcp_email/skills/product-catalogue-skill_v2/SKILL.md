---
name: product-catalogue-skill-v2
description: Handles Resulticks Email product, sub-product and communication-type discovery and validation using MCP catalogue tools.
---

# Product Catalogue Skill

Use this skill whenever the user needs to select, provide, validate, or change Product, Sub Product, or Communication Type for an Email communication.

## Product rules

- Never invent, assume, or generate Product names.
- Never use generic categories such as Electronics, Clothing, Home & Garden, Sports, etc.
- For Product selection, always call `email_list_products`.
- Show only the Product values returned by `email_list_products`.
- If the user provides a Product name directly, call `email_validate_product`.
- Treat the MCP response as authoritative.
- Do not continue with an unvalidated Product.
- Preserve the validated Product ID/value returned by MCP for later steps.

## Sub Product rules

- Never invent Sub Product values.
- After Product is validated, use `email_list_sub_products` when Sub Product selection is required.
- Show only values returned by MCP.
- Do not infer Sub Products from the Product name.

## Communication Type rules

- Never invent Communication Type values.
- Use `email_list_communication_types` to retrieve valid options.
- If the user provides a Communication Type directly, validate it using `email_validate_communication_type`.
- Show and accept only values returned or validated by MCP.

## Execution behavior

When Product information is missing:

1. Call `email_list_products`.
2. Present the returned Product options to the user.
3. When the user selects/provides one, call `email_validate_product`.
4. Store and reuse the validated Product details.
5. Continue to Sub Product or Communication Type only when required.

When the user already provides a Product in their message:

1. Do not ask them to choose from a generic list.
2. Immediately call `email_validate_product`.
3. If valid, continue.
4. If invalid, use the MCP-returned candidates/options to help the user choose.

## Important

MCP catalogue data is the source of truth.

Never create selectable Resulticks business values from model knowledge.
Never fabricate IDs, names, options, or catalogue entries.
