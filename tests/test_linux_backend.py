import unittest
from computer_flo.backends.linux import LinuxBackend


class FakeRunner:
    def __init__(self, available=None):
        self.available = set(available or [])
        self.calls = []

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.available else None

    def run(self, argv):
        self.calls.append(argv)
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}


class LinuxBackendTest(unittest.TestCase):
    def test_capabilities_report_available_tools(self):
        backend = LinuxBackend(runner=FakeRunner({"xdotool", "scrot", "wmctrl"}))

        caps = backend.capabilities()

        self.assertEqual(caps["backend"], "linux")
        self.assertTrue(caps["tools"]["xdotool"]["available"])
        self.assertTrue(caps["tools"]["scrot"]["available"])
        self.assertFalse(caps["tools"]["grim"]["available"])
        self.assertIn("click", caps["operations"])
        self.assertIn("screenshot", caps["operations"])

    def test_click_is_dry_run_by_default(self):
        runner = FakeRunner({"xdotool"})
        backend = LinuxBackend(runner=runner)

        result = backend.click(12, 34)

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["xdotool", "mousemove", "12", "34", "click", "1"])
        self.assertEqual(runner.calls, [])

    def test_type_text_uses_xdotool_and_masks_command_shape(self):
        backend = LinuxBackend(runner=FakeRunner({"xdotool"}))

        result = backend.type_text("hello B")

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["xdotool", "type", "--delay", "15", "hello B"])

    def test_hotkey_splits_combo(self):
        backend = LinuxBackend(runner=FakeRunner({"xdotool"}))

        result = backend.hotkey("ctrl+shift+t")

        self.assertEqual(result["argv"], ["xdotool", "key", "ctrl+shift+t"])

    def test_screenshot_prefers_scrot(self):
        backend = LinuxBackend(runner=FakeRunner({"scrot", "import"}))

        result = backend.screenshot("/tmp/proof.png")

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["scrot", "/tmp/proof.png"])


if __name__ == "__main__":
    unittest.main()
