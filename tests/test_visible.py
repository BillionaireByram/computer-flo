import os
import unittest
from unittest.mock import patch

from computer_flo.visible import VisibleDesktop, build_visible_env, discover_visible_desktop


class FakeRunner:
    def __init__(self, processes="", display_ok=None):
        self.processes = processes
        self.display_ok = display_ok or {}
        self.calls = []

    def run(self, argv, stdin=None, env=None):
        self.calls.append({"argv": argv, "stdin": stdin, "env": env})
        if argv == ["ps", "-ef"]:
            return {"exit_code": 0, "stdout": self.processes, "stderr": ""}
        if argv == ["xdpyinfo"]:
            display = (env or {}).get("DISPLAY")
            ok = self.display_ok.get(display, False)
            return {"exit_code": 0 if ok else 1, "stdout": "", "stderr": ""}
        return {"exit_code": 0, "stdout": "", "stderr": ""}

    def which(self, name):
        return f"/usr/bin/{name}"


class VisibleDesktopTest(unittest.TestCase):
    def test_discovers_xtigervnc_display_and_owner(self):
        processes = "hermes 59500 1 0 ? /usr/bin/Xtigervnc :1 -auth /home/hermes/.Xauthority -geometry 1920x1080\n"
        runner = FakeRunner(processes=processes, display_ok={":1": True})

        desktop = discover_visible_desktop(runner=runner)

        self.assertEqual(desktop.display, ":1")
        self.assertEqual(desktop.user, "hermes")
        self.assertEqual(desktop.xauthority, "/home/hermes/.Xauthority")

    def test_build_visible_env_sets_display_and_xauthority(self):
        desktop = VisibleDesktop(display=":1", user="hermes", xauthority="/home/hermes/.Xauthority")

        env = build_visible_env(desktop, base_env={"PATH": "/bin"})

        self.assertEqual(env["DISPLAY"], ":1")
        self.assertEqual(env["XAUTHORITY"], "/home/hermes/.Xauthority")
        self.assertEqual(env["PATH"], "/bin")

    def test_prefers_existing_valid_display(self):
        runner = FakeRunner(processes="", display_ok={":7": True})
        with patch.dict(os.environ, {"DISPLAY": ":7", "USER": "ava", "HOME": "/home/ava"}, clear=False):
            desktop = discover_visible_desktop(runner=runner)

        self.assertEqual(desktop.display, ":7")
        self.assertEqual(desktop.user, "ava")
        self.assertEqual(desktop.xauthority, "/home/ava/.Xauthority")


if __name__ == "__main__":
    unittest.main()
