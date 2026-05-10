# Computer Flo Backend Strategy

Computer Flo is backend-agnostic. Agent-facing tools should stay stable while desktop-control backends evolve.

## Starting backend: Linux visible runtime

Current implementation uses Linux command planning for:

- `xdotool` for click/type/hotkey/scroll/drag primitives
- `scrot` / `grim` / ImageMagick `import` for screenshots
- `wmctrl` planned for window list/focus
- `xclip` planned for clipboard
- AT-SPI planned for accessibility tree
- noVNC/RDP planned for human watchability

## External/repo inspiration to keep folding in

- Peekaboo: macOS-grade screen + accessibility + action primitives; future macOS backend should wrap Peekaboo directly.
- agent-browser / Playwright / CDP: web-specific DOM, console, screenshots, browser profile inspection.
- VNC/noVNC desktop stacks: visible operator supervision for each agent VM.
- Linux automation tools: xdotool, wmctrl, scrot/grim/import, AT-SPI, ydotool/wtype for X11/Wayland variants.

## Principle

Agents call `computer.*`; backends decide how to perform the action on the current machine.
