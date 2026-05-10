# Ship Computer Flo to Agent Desktops

Computer Flo v0.3 adds `computer-flo-visible`, which auto-discovers the visible desktop session and runs Computer Flo with the correct `DISPLAY`/`XAUTHORITY`.

## Install from this repo on each agent VM

```bash
sudo mkdir -p /opt
cd /opt
# replace this copy step with git clone/pull once the repo is remote
sudo rsync -a /opt/computer-flo/ /opt/computer-flo/
cd /opt/computer-flo
python3 -m pip install -e . --break-system-packages || python3 -m pip install -e .
```

## Required Linux packages

```bash
sudo apt-get update
sudo apt-get install -y xdotool scrot imagemagick x11-utils wmctrl xclip
```

For visible supervision:

```bash
sudo apt-get install -y tigervnc-standalone-server novnc websockify xfce4
```

## Verify visible desktop discovery

```bash
computer-flo-visible --print-env
computer-flo-visible observe --json
computer-flo-visible screenshot /tmp/computer-flo-proof.png --execute --json
file /tmp/computer-flo-proof.png
```

Expected:

- `--print-env` returns a display like `:1` or `:0`.
- `observe` shows `display` populated.
- screenshot returns `status: executed` with non-zero `proof.bytes`.

## Use

Dry-run planned action:

```bash
computer-flo-visible click 960 540 --json
```

Execute real visible action:

```bash
computer-flo-visible click 960 540 --execute --json
computer-flo-visible type "Computer Flo online" --execute --json
computer-flo-visible screenshot /tmp/agent-proof.png --execute --json
```

## MCP

List Computer Flo MCP-style tools:

```bash
computer-flo-mcp --list-tools
```

Call one:

```bash
computer-flo-mcp --call computer.click --arguments '{"x":960,"y":540}'
```

Visible-agent MCP stdio mode:

```bash
computer-flo-mcp --backend auto --visible --stdio
computer-flo-mcp --backend auto --print-visible-env
```

Hermes Agent profile config:

```yaml
mcp_servers:
  computer_flo:
    command: "/usr/local/bin/computer-flo-mcp"
    args: ["--backend", "auto", "--visible", "--stdio"]
    timeout: 120
    connect_timeout: 30
```
