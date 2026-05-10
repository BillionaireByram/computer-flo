# Computer Flo Visible Desktop Supervision

Computer Flo is designed for agent desktops that humans can watch and interrupt.

## Linux reference target

Use a controlled Linux desktop image:

- Ubuntu Desktop or minimal XFCE
- Prefer X11 for v0.x automation reliability
- Chrome/Chromium with persistent profile
- `xdotool`, `wmctrl`, `scrot`, `xclip`
- noVNC or RDP for human viewing
- Tailscale/SSH for ops access

## noVNC pattern

1. Start the agent desktop session under X11.
2. Start VNC bound to localhost/private network only.
3. Expose noVNC behind Tailscale or an authenticated internal reverse proxy.
4. Use Computer Flo for action control and noVNC for human observation.

Example package baseline:

```bash
sudo apt-get update
sudo apt-get install -y xdotool wmctrl scrot xclip x11vnc novnc websockify
```

Example supervised session:

```bash
x11vnc -display :0 -localhost -forever -shared
websockify --web=/usr/share/novnc 6080 localhost:5900
```

## RDP pattern

RDP is acceptable for desktops that already run GNOME Remote Desktop or xrdp. Computer Flo remains the control plane; RDP remains the viewing/control emergency lane.

## Safety rules

- Computer Flo dry-runs by default. Use `--execute` only for intended side effects.
- Keep destructive/client-visible actions behind agent policy approval.
- Keep a visible kill switch: stop agent process, disable MCP server, or close the desktop session.
- Log planned/executed actions with timestamps in the agent runner layer.
- Never expose noVNC/RDP publicly without auth + network allowlisting.

## Verification checklist per agent VM

```bash
hostname; date
printf 'DISPLAY=%s\n' "$DISPLAY"
command -v xdotool wmctrl scrot xclip
PYTHONPATH=/opt/computer-flo/src python3 -m computer_flo.cli observe --json
PYTHONPATH=/opt/computer-flo/src python3 -m computer_flo.cli screenshot /tmp/computer-flo-proof.png --execute --json
```

Expected: `DISPLAY` set, tools present, observe JSON returns capabilities, screenshot proof path exists and has non-zero bytes.
