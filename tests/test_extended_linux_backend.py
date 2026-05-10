import os
import tempfile
import unittest
from unittest.mock import patch

from computer_flo.backends.linux import LinuxBackend


class FakeRunner:
    def __init__(self, available=None, outputs=None):
        self.available = set(available or [])
        self.outputs = outputs or {}
        self.calls = []

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.available else None

    def run(self, argv):
        self.calls.append(argv)
        return self.outputs.get(tuple(argv), {"exit_code": 0, "stdout": "", "stderr": ""})


class ExtendedLinuxBackendTest(unittest.TestCase):
    def test_screenshot_execute_returns_proof_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "shot.png")
            runner = FakeRunner({"scrot"}, {("scrot", path): {"exit_code": 0, "stdout": "", "stderr": ""}})
            backend = LinuxBackend(runner=runner)
            with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.stat") as stat_mock:
                stat_mock.return_value.st_size = 123
                result = backend.screenshot(path, execute=True)

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["proof"]["path"], path)
        self.assertEqual(result["proof"]["bytes"], 123)

    def test_window_list_parses_wmctrl_lines(self):
        stdout = "0x001  0 host Chrome\n0x002  1 host Slack\n"
        runner = FakeRunner({"wmctrl"}, {("wmctrl", "-l"): {"exit_code": 0, "stdout": stdout, "stderr": ""}})
        backend = LinuxBackend(runner=runner)

        result = backend.window_list(execute=True)

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["windows"][0]["id"], "0x001")
        self.assertEqual(result["windows"][0]["title"], "Chrome")

    def test_window_focus_plans_wmctrl_activation(self):
        backend = LinuxBackend(runner=FakeRunner({"wmctrl"}))

        result = backend.window_focus("0x001")

        self.assertEqual(result["argv"], ["wmctrl", "-ia", "0x001"])
        self.assertEqual(result["status"], "planned")

    def test_clipboard_set_and_get_use_xclip(self):
        runner = FakeRunner({"xclip"}, {("xclip", "-selection", "clipboard", "-out"): {"exit_code": 0, "stdout": "hello", "stderr": ""}})
        backend = LinuxBackend(runner=runner)

        set_result = backend.clipboard_set("hello")
        get_result = backend.clipboard_get(execute=True)

        self.assertEqual(set_result["argv"], ["xclip", "-selection", "clipboard"])
        self.assertEqual(set_result["stdin"], "hello")
        self.assertEqual(get_result["text"], "hello")

    def test_browser_profiles_detect_common_chrome_profile_paths(self):
        backend = LinuxBackend(runner=FakeRunner())
        with patch.dict(os.environ, {"HOME": "/home/agent"}, clear=False), patch("pathlib.Path.exists", return_value=True):
            result = backend.browser_state()

        self.assertIn("profiles", result)
        self.assertTrue(any(p["browser"] == "chrome" for p in result["profiles"]))
