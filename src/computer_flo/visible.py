from __future__ import annotations

import os
import re
from dataclasses import dataclass

from computer_flo.runner import CommandRunner


@dataclass(frozen=True)
class VisibleDesktop:
    display: str
    user: str
    xauthority: str | None = None


def build_visible_env(desktop: VisibleDesktop, base_env: dict | None = None) -> dict:
    env = dict(base_env or os.environ)
    env["DISPLAY"] = desktop.display
    if desktop.xauthority:
        env["XAUTHORITY"] = desktop.xauthority
    return env


def discover_visible_desktop(runner: object | None = None) -> VisibleDesktop:
    """Discover the best visible X desktop for Computer Flo actions.

    Order:
    1. Current DISPLAY if valid.
    2. Xtigervnc/Xorg process lines with display tokens and auth hints.
    3. Common fallback displays (:1, :0, :2) if valid.
    """

    runner = runner or CommandRunner()
    current = os.environ.get("DISPLAY")
    if current and _display_works(runner, current, os.environ.get("XAUTHORITY")):
        user = os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"
        home = os.environ.get("HOME", f"/home/{user}")
        return VisibleDesktop(display=current, user=user, xauthority=os.environ.get("XAUTHORITY") or f"{home}/.Xauthority")

    ps = runner.run(["ps", "-ef"])
    for line in ps.get("stdout", "").splitlines():
        if not any(marker in line for marker in ("Xtigervnc", "Xorg", "Xvnc", "Xwayland")):
            continue
        desktop = _desktop_from_process_line(line)
        if desktop and _display_works(runner, desktop.display, desktop.xauthority):
            return desktop

    for display in (":1", ":0", ":2"):
        if _display_works(runner, display, os.environ.get("XAUTHORITY")):
            user = os.environ.get("USER") or "unknown"
            home = os.environ.get("HOME", f"/home/{user}")
            return VisibleDesktop(display=display, user=user, xauthority=os.environ.get("XAUTHORITY") or f"{home}/.Xauthority")

    raise RuntimeError("No usable visible desktop found. Set DISPLAY/XAUTHORITY or start VNC/X11 desktop.")


def _display_works(runner: object, display: str, xauthority: str | None = None) -> bool:
    env = dict(os.environ)
    env["DISPLAY"] = display
    if xauthority:
        env["XAUTHORITY"] = xauthority
    try:
        result = runner.run(["xdpyinfo"], env=env)
    except TypeError:
        return False
    return result.get("exit_code") == 0


def _desktop_from_process_line(line: str) -> VisibleDesktop | None:
    parts = line.split()
    if not parts:
        return None
    user = parts[0]
    display = None
    for part in parts:
        if re.fullmatch(r":\d+(?:\.\d+)?", part):
            display = part
            break
    if not display:
        return None
    xauthority = None
    if "-auth" in parts:
        idx = parts.index("-auth")
        if idx + 1 < len(parts):
            xauthority = parts[idx + 1]
    if not xauthority:
        xauthority = f"/home/{user}/.Xauthority"
    return VisibleDesktop(display=display, user=user, xauthority=xauthority)
