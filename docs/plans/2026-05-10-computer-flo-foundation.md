# Computer Flo Foundation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement future plan tasks task-by-task.

**Goal:** Build the first Linux visible-computer runtime foundation for DigitalFlo agents.

**Architecture:** Computer Flo exposes a stable agent-facing command surface (`observe`, `screenshot`, `click`, `type`, `hotkey`, `scroll`, windows later) while hiding backend-specific implementations. The first backend targets Linux X11 using standard tools (`xdotool`, `wmctrl`, `scrot`, `import`) with dry-run-by-default safety. Future macOS/Peekaboo and browser backends can plug into the same interface.

**Tech Stack:** Python 3.12, stdlib unittest, CLI JSON output, shell command planning through a small executor abstraction.

---

## Task 1: Scaffold package
- Create `pyproject.toml`, `README.md`, package under `src/computer_flo/`.
- Verification: `python3 -m unittest discover -s tests` runs.

## Task 2: Backend capability detection
- Test first: backend reports available commands based on injected command lookup.
- Implement `LinuxBackend.capabilities()`.

## Task 3: Safe command planning
- Test first: click/type/hotkey/screenshot produce explicit shell argv and do not execute by default.
- Implement typed operation results.

## Task 4: CLI JSON interface
- Test first: `computer-flo observe --json` returns structured JSON.
- Implement argparse CLI.

## Task 5: Future integrations
- Add backend registry and TODO adapter notes for Peekaboo/macOS, agent-browser/Playwright, noVNC/RDP.
