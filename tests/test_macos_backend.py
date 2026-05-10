import unittest

from computer_flo.backends.macos import PeekabooBackend


class FakeRunner:
    def __init__(self, available=None):
        self.available = set(available or [])

    def which(self, name):
        return f"/usr/local/bin/{name}" if name in self.available else None


class PeekabooBackendTest(unittest.TestCase):
    def test_capabilities_report_peekaboo_wrapper(self):
        backend = PeekabooBackend(runner=FakeRunner({"peekaboo"}))

        caps = backend.capabilities()

        self.assertEqual(caps["backend"], "macos-peekaboo")
        self.assertTrue(caps["tools"]["peekaboo"]["available"])
        self.assertIn("screenshot", caps["operations"])

    def test_click_maps_to_peekaboo_cli(self):
        backend = PeekabooBackend(runner=FakeRunner({"peekaboo"}))

        result = backend.click(10, 20)

        self.assertEqual(result["argv"], ["peekaboo", "click", "--coords", "10,20"])
        self.assertEqual(result["status"], "planned")
