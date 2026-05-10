from __future__ import annotations

import sys

from computer_flo.backends.linux import LinuxBackend
from computer_flo.backends.macos import PeekabooBackend


def select_backend(name: str = "auto"):
    """Return the requested Computer Flo backend.

    `auto` uses the native macOS Peekaboo adapter on Darwin and the Linux
    visible-desktop backend everywhere else. The backend objects intentionally
    share the stable Computer Flo method surface used by CLI/MCP callers.
    """
    normalized = (name or "auto").lower()
    if normalized == "auto":
        return PeekabooBackend() if sys.platform == "darwin" else LinuxBackend()
    if normalized in {"linux", "x11"}:
        return LinuxBackend()
    if normalized in {"macos", "mac", "darwin", "peekaboo"}:
        return PeekabooBackend()
    raise ValueError(f"unknown backend: {name}")
