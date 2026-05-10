# GoHighLevel API Capability Matrix

Current source: official HighLevel public API docs/repo plus local validation notes. Public API base URL is `https://services.leadconnectorhq.com`. Most endpoints require `Authorization: Bearer <token>` and `Version: 2021-07-28`.

## Strong API-first lanes

| Asset | Public API capability | Use in agent framework |
|---|---|---|
| Locations | search, get, create, update | agency inventory, buyer sub-account creation when explicitly authorized |
| Tags | list/create/update/delete location tags; assign/remove contact tags | create workflow prerequisites before UI build |
| Custom values | list/create/update/delete | create merge-field URLs and constants before workflows |
| Custom fields | list/create/update/delete; V2 object-key/folder support | create fields before workflow actions reference them |
| Products/prices | product CRUD, price CRUD, inventory/collections | product/price setup and verification |
| Calendars/events | calendar/group/event/resource CRUD | appointment/booking infrastructure |
| Opportunities | search, get, create/upsert/update/delete/status/followers | pipeline state sync and workflow QA |
| Payments | orders/transactions/subscriptions/coupons/provider ops | purchase/order verification and fulfillment triggers |
| Forms/surveys | list and submissions; forms file upload | inventory/QA; body builder remains UI |
| Webhooks | events configured through Marketplace app/settings/scopes | event-driven middleware; verify `x-wh-signature` |

## UI/private lanes

| Asset | Public API gap | Required lane |
|---|---|---|
| Workflow body | official API exposes `GET /workflows/` only; no body read/create/update/publish | isolated browser UI macro or user-approved private adapter |
| Forms/surveys body builder | no public create/update builder surface in official docs | isolated browser UI macro or snapshot |
| Snapshot creation/refresh/import/push | public API is mostly list/share/status; content ops not exposed | isolated browser UI macro |
| GHL AI workflow builder | UI-only | isolated browser UI macro with compiled prompt |

## Risk policy for private/internal endpoints

Some community MCP repos reference internal/private workflow endpoints such as `https://backend.leadconnectorhq.com/workflow`. These may create/update/publish workflows but are unsupported and high-risk.

Default rule: do not use private workflow endpoints for live accounts.
Allowed only if all are true:
1. User explicitly authorizes private adapter use for this account.
2. Sandbox/test location is used first.
3. Existing workflow inventory is exported/screenshot-verified first.
4. Dry-run payload is reviewed.
5. Audit logs are written locally.
6. Publish remains disabled unless the user explicitly says publish.
