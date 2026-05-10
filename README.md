# Computer Flo

Computer Flo is a visible-computer control runtime for AI agents.

It gives agents one stable `computer.*` interface for observing and operating desktops while hiding backend details like Linux X11 tools, VNC/noVNC sessions, macOS Peekaboo, browser profiles, and future remote-desktop backends.

Computer Flo is safe by default: action commands only return a plan unless `--execute` is explicitly passed.

## Why this exists

Most agents need the same handful of computer-use primitives:

- observe the current desktop/session
- capture screenshots
- move, click, type, drag, scroll, and press hotkeys
- list/focus windows
- read/write the clipboard
- inspect browser profile state

Without a stable runtime, every agent and every VM ends up with its own one-off shell commands. Computer Flo turns those commands into a reusable control layer that can be installed once and exposed to many agents through CLI or MCP-style tools.

## Core features

- Stable `computer.*` action surface
- Dry-run planning by default
- `--execute` gate for real side effects
- Linux X11 backend using `xdotool`, `wmctrl`, `scrot`/`import`, and `xclip`
- Visible desktop wrapper that auto-discovers VNC/X11 display settings
- macOS backend through Peekaboo, with `screencapture` fallback for screenshots
- MCP-style JSON-RPC stdio server for agent integration
- Browser profile detection for Chrome, Chromium, Brave, and Firefox
- OpenHuman-inspired human mouse paths: smooth `computer.move`, optional human-like click/drag movement, coordinate validation, and MCP exposure
- Digital Flow workflow modules, starting with the GoHighLevel automation framework
- Unit-tested backend and command behavior

## Tool surface

Computer Flo exposes these operations through the CLI and MCP server:

- `computer.observe`
- `computer.screenshot`
- `computer.move`
- `computer.click`
- `computer.type`
- `computer.hotkey`
- `computer.scroll`
- `computer.drag`
- `computer.window_list`
- `computer.window_focus`
- `computer.clipboard_get`
- `computer.clipboard_set`
- `computer.browser_state`

## Workflow modules

Computer Flo also carries higher-level agent workflow modules that use the computer-use/runtime layer as part of Digital Flow automation.

Current modules:

- `workflows/gohighlevel-agent/` — Digital Flow's reusable GoHighLevel automation framework for API-first asset setup, isolated browser launch, workflow blueprint compilation, inventory, and UI-builder handoff.

Quick GHL checks:

```bash
cd workflows/gohighlevel-agent
python3 ghl_agent.py doctor
python3 ghl_agent.py --profile client-profiles/tax-mogul-os.json compile --workflow-name "TTM - OS Purchase Fulfillment" --out /tmp/ghl-plan.json
```

Never commit `env.local` or live GHL credentials. Use `env.example` as the template.

## Requirements

Python:

- Python 3.12+

Linux desktop packages:

```bash
sudo apt-get update
sudo apt-get install -y \
  xdotool \
  scrot \
  imagemagick \
  x11-utils \
  wmctrl \
  xclip
```

Optional visible-supervision packages for VNC/noVNC desktops:

```bash
sudo apt-get install -y \
  tigervnc-standalone-server \
  novnc \
  websockify \
  xfce4
```

macOS optional backend:

```bash
npm install -g @steipete/peekaboo
```

Peekaboo requires macOS Screen Recording and Accessibility permissions.

## Install

From source:

```bash
git clone https://github.com/BillionaireByram/computer-flo.git
cd computer-flo
python3 -m pip install -e .
```

On locked-down system Python installs, you may need:

```bash
python3 -m pip install -e . --break-system-packages
```

After install, these commands are available:

```bash
computer-flo
computer-flo-visible
computer-flo-mcp
```

## Quick start

Observe capabilities:

```bash
computer-flo --backend auto observe --json
```

Plan a human-like cursor move without executing it:

```bash
computer-flo --backend auto move 960 540 --human-like --json
```

Execute a human-like move with the optional on-demand electric-blue AI cursor overlay on macOS:

```bash
computer-flo --backend macos move 960 540 --human-like --execute --json
```

The glow overlay is intentionally not always-on. It appears only during executed `move`, `click`, and `drag` actions that pass `--human-like`, then shuts itself down. Build or refresh it with:

```bash
tools/build-cursor-glow.sh
```

Disable the visual effect for automation-only runs:

```bash
COMPUTER_FLO_CURSOR_GLOW_DISABLED=1 computer-flo --backend macos move 960 540 --human-like --execute --json
```

Plan a click without executing it:

```bash
computer-flo --backend auto click 960 540 --json
```

Execute a real click:

```bash
computer-flo --backend auto click 960 540 --execute --json
```

Type text:

```bash
computer-flo --backend auto type "Computer Flo online" --execute --json
```

Take a screenshot:

```bash
computer-flo --backend auto screenshot /tmp/computer-flo-proof.png --execute --json
```

List windows:

```bash
computer-flo --backend auto window-list --execute --json
```

Set clipboard:

```bash
computer-flo --backend auto clipboard-set "hello from Computer Flo" --execute --json
```

Read clipboard:

```bash
computer-flo --backend auto clipboard-get --execute --json
```

## Visible desktop wrapper

On agent VMs, the active desktop is often a VNC/X11 session running on `:1` with an Xauthority file owned by another user. Use `computer-flo-visible` to discover that session automatically.

Print detected desktop environment:

```bash
computer-flo-visible --print-env
```

Observe visible desktop:

```bash
computer-flo-visible observe --json
```

Execute against visible desktop:

```bash
computer-flo-visible click 960 540 --execute --json
computer-flo-visible type "Computer Flo visible mode" --execute --json
computer-flo-visible screenshot /tmp/visible-proof.png --execute --json
```

Expected `--print-env` output looks like:

```json
{"display": ":1", "user": "hermes", "xauthority": "/home/hermes/.Xauthority"}
```

## MCP / agent integration

Computer Flo includes a dependency-light MCP-style JSON-RPC stdio server.

List tools:

```bash
computer-flo-mcp --list-tools
```

Call one tool directly:

```bash
computer-flo-mcp --call computer.click --arguments '{"x":960,"y":540}'
```

Run stdio mode:

```bash
computer-flo-mcp --backend auto --stdio
```

Run stdio mode with visible desktop discovery:

```bash
computer-flo-mcp --backend auto --visible --stdio
```

Print visible env through the MCP binary:

```bash
computer-flo-mcp --backend auto --print-visible-env
```

### Hermes Agent config

Add this to a Hermes Agent profile config:

```yaml
mcp_servers:
  computer_flo:
    command: "/usr/local/bin/computer-flo-mcp"
    args: ["--backend", "auto", "--visible", "--stdio"]
    timeout: 120
    connect_timeout: 30
```

Restart the agent after adding the MCP server. Discovered tools will be registered with a server prefix by the host agent.

## Backend behavior

### Linux

The Linux backend uses standard desktop automation tools:

- `xdotool` for click/type/hotkey/scroll/drag
- `wmctrl` for window list/focus
- `scrot`, `import`, or `grim` for screenshots
- `xclip` for clipboard

Every side-effecting operation returns a planned command unless `--execute` is passed.

### macOS

The macOS backend wraps Peekaboo:

```bash
computer-flo --backend macos observe --json
computer-flo --backend macos screenshot /tmp/shot.png --execute --json
computer-flo --backend macos click 100 200 --execute --json
```

If Peekaboo is not installed, screenshots can fall back to the native `screencapture` command.

### Auto backend

Use `--backend auto` for portable commands:

- macOS/Darwin selects the macOS Peekaboo backend
- Linux selects the Linux backend

## Safety model

Computer Flo separates intent from execution.

This plans only:

```bash
computer-flo click 100 200 --json
```

This executes:

```bash
computer-flo click 100 200 --execute --json
```

This is important when agents use Computer Flo autonomously. You can log, review, approve, replay, or block plans before real desktop side effects happen.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run from source without installing:

```bash
PYTHONPATH=src python3 -m computer_flo.cli --backend auto observe --json
PYTHONPATH=src python3 -m computer_flo.visible_cli --print-env
PYTHONPATH=src python3 -m computer_flo.mcp_server --list-tools
```

Project layout:

```text
src/computer_flo/
  cli.py              main CLI
  visible_cli.py      visible desktop wrapper
  mcp_server.py       MCP-style stdio server
  visible.py          VNC/X11 desktop discovery
  runner.py           command runner abstraction
  backends/
    linux.py          Linux/X11 backend
    macos.py          macOS/Peekaboo backend
    selector.py       backend selection

tests/                unit tests

docs/
  backends.md         backend strategy
  supervision.md      VNC/noVNC supervision pattern
  ship-to-agents.md   deployment notes for agent VMs
```

## Deployment to agent VMs

A typical Linux desktop agent deployment looks like:

```bash
sudo mkdir -p /opt/computer-flo
sudo rsync -a ./ /opt/computer-flo/
cd /opt/computer-flo
sudo apt-get update
sudo apt-get install -y xdotool scrot imagemagick x11-utils wmctrl xclip python3-pip python3-venv
sudo python3 -m pip install -e . --break-system-packages || sudo python3 -m pip install -e .
computer-flo-visible --print-env
computer-flo-visible observe --json
```

For DigitalFlo-style Hermes profiles, configure `mcp_servers.computer_flo` as shown above, then restart the agent service.

## Status

Current version: `0.4.0`

Computer Flo is early infrastructure. The current foundation is stable enough for visible Linux desktops, VNC/noVNC agent VMs, macOS Peekaboo experiments, and MCP-style integration. Planned extensions include browser/CDP backends, richer screenshot observation, remote supervision adapters, action auditing, and approval policies.

## License

MIT License. See `LICENSE`.
