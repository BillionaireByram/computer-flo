from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import time

from computer_flo.runner import CommandRunner


@dataclass
class PeekabooBackend:
    """macOS backend wrapper around the Peekaboo CLI.

    This adapter keeps the Computer Flo API stable while delegating native
    macOS screen/accessibility/input work to Peekaboo when installed.
    """

    runner: object | None = None

    def __post_init__(self) -> None:
        if self.runner is None:
            self.runner = CommandRunner()

    def capabilities(self) -> dict:
        peekaboo_path = self.runner.which("peekaboo")
        screencapture_path = self.runner.which("screencapture")
        peekaboo_available = peekaboo_path is not None
        screencapture_available = screencapture_path is not None
        operations = ["observe"]
        if peekaboo_available:
            operations.extend(["move", "screenshot", "click", "type", "hotkey", "scroll", "drag", "window_list", "window_focus"])
        elif screencapture_available:
            operations.append("screenshot")
        return {
            "backend": "macos-peekaboo",
            "tools": {
                "peekaboo": {"available": peekaboo_available, "path": peekaboo_path},
                "screencapture": {"available": screencapture_available, "path": screencapture_path},
                "pbcopy": {"available": self.runner.which("pbcopy") is not None, "path": self.runner.which("pbcopy")},
                "pbpaste": {"available": self.runner.which("pbpaste") is not None, "path": self.runner.which("pbpaste")},
            },
            "operations": sorted(set(operations)),
        }

    def observe(self) -> dict:
        return {"capabilities": self.capabilities(), "browser_state": self.browser_state()}

    def move(self, x: int, y: int, *, execute: bool = False, human_like: bool = False, duration_ms: int = 450, steps: int = 25, start_x: int | None = None, start_y: int | None = None) -> dict:
        argv = ["peekaboo", "move", f"{x},{y}"]
        if human_like:
            argv.extend(["--profile", "human", "--duration", str(duration_ms), "--steps", str(steps)])
        return self._plan_or_run("move", argv, execute, extra={"human_like": human_like})

    def click(self, x: int, y: int, button: int = 1, *, execute: bool = False, human_like: bool = False, start_x: int | None = None, start_y: int | None = None) -> dict:
        argv = ["peekaboo", "click", "--coords", f"{x},{y}"]
        if button == 2:
            argv.append("--right")
        if human_like:
            argv.extend(["--input-strategy", "synthFirst"])
        return self._plan_or_run("click", argv, execute, extra={"human_like": human_like})

    def type_text(self, text: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("type", ["peekaboo", "type", text], execute)

    def hotkey(self, combo: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("hotkey", ["peekaboo", "hotkey", combo], execute)

    def scroll(self, clicks: int, *, execute: bool = False) -> dict:
        direction = "up" if clicks > 0 else "down"
        return self._plan_or_run("scroll", ["peekaboo", "scroll", "--direction", direction, "--amount", str(abs(clicks))], execute)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, button: int = 1, *, execute: bool = False, human_like: bool = False) -> dict:
        argv = ["peekaboo", "drag", "--from-coords", f"{start_x},{start_y}", "--to-coords", f"{end_x},{end_y}"]
        if human_like:
            argv.extend(["--profile", "human", "--duration", "700", "--steps", "25"])
        if button != 1:
            argv.extend(["--modifiers", f"button{button}"])
        return self._plan_or_run("drag", argv, execute, extra={"human_like": human_like})

    def screenshot(self, path: str, *, execute: bool = False) -> dict:
        if self.runner.which("peekaboo"):
            argv = ["peekaboo", "image", "--path", path]
        else:
            argv = ["screencapture", "-x", path]
        result = self._plan_or_run("screenshot", argv, execute, extra={"path": path})
        if execute and result["status"] == "executed":
            from pathlib import Path
            proof_path = Path(path)
            result["proof"] = {
                "path": path,
                "exists": proof_path.exists(),
                "bytes": proof_path.stat().st_size if proof_path.exists() else 0,
            }
        return result

    def window_list(self, *, execute: bool = False) -> dict:
        return self._plan_or_run("window_list", ["peekaboo", "list", "windows"], execute)

    def window_focus(self, window_id: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("window_focus", ["peekaboo", "focus", window_id], execute)

    def clipboard_get(self, *, execute: bool = False) -> dict:
        return self._plan_or_run("clipboard_get", ["pbpaste"], execute)

    def clipboard_set(self, text: str, *, execute: bool = False) -> dict:
        return self._plan_or_run("clipboard_set", ["pbcopy"], execute, extra={"stdin": text})

    def browser_state(self) -> dict:
        from pathlib import Path
        import os

        home = Path(os.environ.get("HOME", "~")).expanduser()
        candidates = [
            ("chrome", home / "Library" / "Application Support" / "Google" / "Chrome"),
            ("chromium", home / "Library" / "Application Support" / "Chromium"),
            ("brave", home / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser"),
            ("firefox", home / "Library" / "Application Support" / "Firefox"),
        ]
        profiles = [{"browser": browser, "path": str(path), "exists": True} for browser, path in candidates if path.exists()]
        return {"profiles": profiles, "profile_count": len(profiles)}

    def _plan_or_run(self, operation: str, argv: list[str], execute: bool, extra: dict | None = None) -> dict:
        payload = {"operation": operation, "status": "planned", "argv": argv}
        if extra:
            payload.update(extra)
        if not execute:
            return payload
        stdin = payload.get("stdin") if isinstance(payload.get("stdin"), str) else None
        glow = self._start_cursor_glow(operation, payload)
        try:
            try:
                run = self.runner.run(argv, stdin=stdin)
            except TypeError:
                run = self.runner.run(argv)
        finally:
            self._stop_cursor_glow(glow)
        payload["status"] = "executed" if run["exit_code"] == 0 else "failed"
        payload["execution"] = run
        if glow is not None:
            payload["cursor_overlay"] = "electric-blue-futuristic-on-demand"
        return payload

    def _cursor_glow_path(self) -> str | None:
        return os.environ.get("COMPUTER_FLO_CURSOR_GLOW") or self.runner.which("computer-flo-cursor-glow")

    def _start_cursor_glow(self, operation: str, payload: dict) -> subprocess.Popen | None:
        if operation not in {"move", "click", "drag"} or not payload.get("human_like"):
            return None
        if os.environ.get("COMPUTER_FLO_CURSOR_GLOW_DISABLED") in {"1", "true", "yes"}:
            return None
        path = self._cursor_glow_path()
        if not path:
            return None
        try:
            proc = subprocess.Popen(
                [path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            time.sleep(0.08)
            return proc
        except OSError:
            return None

    def _stop_cursor_glow(self, proc: subprocess.Popen | None) -> None:
        if proc is None:
            return
        if proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1.0)
