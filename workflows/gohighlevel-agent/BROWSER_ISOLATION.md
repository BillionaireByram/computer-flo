# Browser Isolation Rule for GHL Agents

The agent must work in exactly one isolated browser context per GHL task.

## Default isolated context

Browser: Google Chrome, separate app instance/profile
Profile directory:

`/Users/puregeniushq/.hermes/browser-profiles/gohighlevel-isolated`

Open with:

```bash
cd /Users/puregeniushq/projects/businesses/digitalflo/automation/ghl-agent
python3 ghl_agent.py open
```

Or for a specific URL:

```bash
python3 ghl_agent.py open --url "https://app.gohighlevel.com/v2/location/TCtjYrl5wIdLwd4aCham/automation/workflows?listTab=all"
```

## Rules

1. Agent must not touch the user's normal Chrome tabs/windows while a GHL build task is active.
2. Agent must not switch browser/profile unless the user explicitly authorizes it or login/session is impossible in the isolated profile.
3. One task = one isolated tab/window. If multiple GHL pages are needed, open them inside the same isolated profile and name the active target in notes.
4. User can keep working in normal Chrome/Safari/Arc tabs; agent automation must remain scoped to the isolated profile/window.
5. Before clicking destructive or externally visible controls, agent must confirm scope and draft/publish state.
6. If a login, 2FA, password, payment, or permission dialog appears, agent stops and asks the user.

## Why

This prevents the agent from hijacking user browsing, clicking the wrong tab, or reading unrelated personal/client tabs while still allowing fast UI automation.
