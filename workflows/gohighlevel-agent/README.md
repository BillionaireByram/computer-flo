# Digital Flow GHL Agent Framework

Computer Flo home for reusable GoHighLevel workflow automation:

`workflows/gohighlevel-agent/`

Local Digital Flow working copy may also exist at:

`/Users/puregeniushq/projects/businesses/digitalflo/automation/ghl-agent`

This is not a Sydne/client project. Client-specific accounts, blueprints, and docs are loaded through profiles under `client-profiles/` or explicit `--blueprint` paths.

## Core operating model

1. API-first setup/inventory.
2. One isolated browser profile/window/tab per GHL task.
3. Compile workflow blueprint before UI work.
4. Use GHL AI Builder or deterministic UI macros only for public-API gaps.
5. Leave workflows Draft unless explicitly told to publish.

## Quick commands

```bash
cd workflows/gohighlevel-agent
cp env.example env.local
chmod 600 env.local
# fill GHL_API_TOKEN or GHL_AGENCY_KEY locally

python3 ghl_agent.py doctor
python3 ghl_agent.py doctor --check-chrome-js
python3 ghl_agent.py open
python3 ghl_agent.py inventory
python3 ghl_agent.py compile --workflow-name "Example - Lead Opt In"
```

## Client profile example: Tax Mogul / Sydne

The reusable framework stays under Digital Flow, but this profile points to the existing Tax Mogul client docs:

`client-profiles/tax-mogul-os.json`

Use it with:

```bash
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json doctor
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json compile --workflow-name "TTM - OS Purchase Fulfillment" --out /tmp/ghl-plan.json
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json open
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json inventory --execute
```

## Browser isolation rule

Agents must open GoHighLevel in the isolated Chrome profile:

`/Users/puregeniushq/.hermes/browser-profiles/gohighlevel-isolated`

Use:

```bash
python3 ghl_agent.py open
```

or with a client profile:

```bash
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json open
```

The user can keep working in their normal browser tabs. The agent must stay in the isolated browser unless the user explicitly authorizes switching contexts.

## API lanes

Safe/API lane:
- locations inventory/create/update
- tags
- custom fields
- custom values
- products/prices
- calendars/events/resources
- opportunities
- forms/surveys inventory/submissions
- workflow inventory only
- snapshots inventory/share/status only

UI/macro lane required:
- workflow body create/edit/publish
- form/survey builder body edits
- snapshot creation/refresh/import/push flows
- GHL AI workflow builder prompting/adjustments

## Private endpoint policy

Some community tools mention hidden workflow endpoints. They are unsupported and high-risk. Do not use private/internal GHL endpoints on live accounts unless the user explicitly authorizes that adapter, a sandbox test passes, and publish remains disabled.

## Chrome JavaScript from Apple Events

Recheck with:

```bash
python3 ghl_agent.py doctor --check-chrome-js
```

If it fails:

```bash
python3 ghl_agent.py enable-chrome-js-pref
```

Security note: only trusted automation processes should have macOS Automation permission to control Chrome.
