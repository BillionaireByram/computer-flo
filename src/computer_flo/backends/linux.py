from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from computer_flo.runner import CommandRunner


LINUX_TOOLS = ["xdotool", "wmctrl", "scrot", "import", "grim", "wtype", "ydotool", "xclip"]


@dataclass
class LinuxBackend:
    """Linux visible-desktop backend.

    The backend is safe by default: operations return a command plan unless
    `execute=True` is passed. This lets agents and humans inspect intended
    actions before side effects.
    """

    runner: object | None = None

    def __post_init__(self) -> None:
        if self.runner is None:
            self.runner = CommandRunner()

    def capabilities(self) -> dict:
        tools = {name: {"available": self.runner.which(name) is not None, "path": self.runner.which(name)} for name in LINUX_TOOLS}
        operations = ["observe", "browser_state"]
        if tools["xdotool"]["available"] or tools["ydotool"]["available"]:
            operations.extend(["click", "type", "hotkey", "scroll", "drag"])
        if tools["scrot"]["available"] or tools["import"]["available"] or tools["grim"]["available"]:
            operations.append("screenshot")
        if tools["wmctrl"]["available"]:
            operations.extend(["window_list", "window_focus"] )
        if tools["xclip"]["available"]:
            operations.extend(["clipboard_get", "clipboard_set"] )
        return {"backend": "linux", "session": self._session_hint(), "tools": tools, "operations": sorted(set(operations))}

    def observe(self) -> dict:
        return {"capabilities": self.capabilities(), "browser_state": self.browser_state()}

    def click(self, x: int, y: int, button: int = 1, *, execute: bool = False) -> dict:
        if self.runner.which("xdotool") or not self.runner.which("ydotool"):
            argv = ["xdotool", "mousemove", str(x), str(y), "click", str(button)]
        else:
            ydotool_button = "0xC0" if button == 1 else str(button)
            argv = ["ydotool", "mousemove", "--absolute", str(x), str(y), "click", ydotool_button]
        return self._plan_or_run("click", argv, execute)

    def type_text(self, text: str, delay_ms: int = 15, *, execute: bool = False) -> dict:
        if self.runner.which("xdotool") or not self.runner.which("wtype"):
            argv = ["xdotool", "type", "--delay", str(delay_ms), text]
        else:
            argv = ["wtype", text]
        return self._plan_or_run("type", argv, execute)

    def hotkey(self, combo: str, *, execute: bool = False) -> dict:
        argv = ["xdotool", "key", combo]
        return self._plan_or_run("hotkey", argv, execute)

    def scroll(self, clicks: int, *, execute: bool = False) -> dict:
        button = "4" if clicks > 0 else "5"
        argv = ["xdotool", "click", "--repeat", str(abs(clicks)), button]
        return self._plan_or_run("scroll", argv, execute)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, button: int = 1, *, execute: bool = False) -> dict:
        argv = [
            "xdotool",
            "mousemove", str(start_x), str(start_y),
            "mousedown", str(button),
            "mousemove", str(end_x), str(end_y),
            "mouseup", str(button),
        ]
        return self._plan_or_run("drag", argv, execute)

    def screenshot(self, output_path: str, *, execute: bool = False) -> dict:
        path = str(Path(output_path).expanduser())
        if self.runner.which("scrot"):
            argv = ["scrot", path]
        elif self.runner.which("grim"):
            argv = ["grim", path]
        else:
            argv = ["import", "-window", "root", path]
        result = self._plan_or_run("screenshot", argv, execute, extra={"path": path})
        if execute and result["status"] == "executed":
            proof_path = Path(path)
            result["proof"] = {
                "path": path,
                "exists": proof_path.exists(),
                "bytes": proof_path.stat().st_size if proof_path.exists() else 0,
            }
        return result

    def window_list(self, *, execute: bool = False) -> dict:
        result = self._plan_or_run("window_list", ["wmctrl", "-l"], execute)
        if execute and result.get("execution"):
            result["windows"] = self._parse_wmctrl(result["execution"].get("stdout", ""))
        return result

    def window_focus(self, window_id: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("window_focus", ["wmctrl", "-ia", window_id], execute)

    def clipboard_get(self, *, execute: bool = False) -> dict:
        result = self._plan_or_run("clipboard_get", ["xclip", "-selection", "clipboard", "-out"], execute)
        if execute and result.get("execution"):
            result["text"] = result["execution"].get("stdout", "")
        return result

    def clipboard_set(self, text: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("clipboard_set", ["xclip", "-selection", "clipboard"], execute, extra={"stdin": text})

    def browser_state(self) -> dict:
        import os

        home = Path(os.environ.get("HOME", "~")).expanduser()
        candidates = [
            ("chrome", home / ".config" / "google-chrome"),
            ("chromium", home / ".config" / "chromium"),
            ("brave", home / ".config" / "BraveSoftware" / "Brave-Browser"),
            ("firefox", home / ".mozilla" / "firefox"),
        ]
        profiles = []
        for browser, path in candidates:
            if path.exists():
                profiles.append({"browser": browser, "path": str(path), "exists": True})
        return {"profiles": profiles, "profile_count": len(profiles)}

    def _plan_or_run(self, operation: str, argv: list[str], execute: bool, extra: dict | None = None) -> dict:
        payload = {"operation": operation, "status": "planned", "argv": argv}
        if extra:
            payload.update(extra)
        if not execute:
            return payload
        stdin = payload.get("stdin") if isinstance(payload.get("stdin"), str) else None
        try:
            run = self.runner.run(argv, stdin=stdin)
        except TypeError:
            run = self.runner.run(argv)
        payload["status"] = "executed" if run["exit_code"] == 0 else "failed"
        payload["execution"] = run
        return payload

    def _parse_wmctrl(self, stdout: str) -> list[dict]:
        windows = []
        for line in stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) >= 4:
                windows.append({"id": parts[0], "desktop": parts[1], "host": parts[2], "title": parts[3]})
        return windows

    def _session_hint(self) -> dict:
        import os

        return {
            "display": os.environ.get("DISPLAY"),
            "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
            "desktop_session": os.environ.get("XDG_SESSION_TYPE"),
        }
