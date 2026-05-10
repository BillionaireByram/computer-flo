import unittest

from computer_flo.backends.macos import PeekabooBackend


class MacOSNativeFallbackTest(unittest.TestCase):
    def test_capabilities_include_native_screenshot_without_peekaboo(self):
        backend = PeekabooBackend(runner=FakeRunner({"screencapture"}))

        caps = backend.capabilities()

        self.assertFalse(caps["tools"]["peekaboo"]["available"])
        self.assertTrue(caps["tools"]["screencapture"]["available"])
        self.assertIn("screenshot", caps["operations"])

    def test_screenshot_falls_back_to_screencapture(self):
        backend = PeekabooBackend(runner=FakeRunner({"screencapture"}))

        result = backend.screenshot("/tmp/flo.png")

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["screencapture", "-x", "/tmp/flo.png"])


class FakeRunner:
    def __init__(self, available=None):
        self.available = set(available or [])

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.available else None

    def run(self, argv, stdin=None, env=None):
        return {"exit_code": 0, "stdout": "", "stderr": ""}


if __name__ == "__main__":
    unittest.main()
