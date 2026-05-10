# GHL AI Workflow Builder Prompt Template

Use this only inside the isolated GoHighLevel browser context.

Paste into GHL AI Builder when available, then inspect/adjust generated cards manually.

```text
Build a GoHighLevel workflow in Draft mode only.

Workflow name: {{WORKFLOW_NAME}}
Trigger: {{TRIGGER}}

Required ordered actions:
{{ORDERED_ACTIONS}}

Copy blocks:
{{COPY_BLOCKS}}

Rules:
- Leave this workflow as Draft.
- Do not publish.
- Use existing tags, custom fields, custom values, forms, calendars, products, and pipelines by exact name.
- If an asset is not found, create a placeholder card/note and keep going.
- Use HighLevel merge fields exactly as written.
- Add clear internal card names.
```

After AI Builder generates the workflow:
1. Verify trigger.
2. Verify each card order and settings.
3. Replace any placeholder asset with exact ID/name from API inventory.
4. Save after each correction.
5. Leave Draft unless user explicitly says publish.
