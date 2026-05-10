import unittest

from computer_flo.adapters import AdapterRegistry


class AdapterRegistryTest(unittest.TestCase):
    def test_registry_contains_planned_backends_and_repo_notes(self):
        registry = AdapterRegistry.default()

        self.assertIn("linux-x11", registry.names())
        self.assertIn("macos-peekaboo", registry.names())
        self.assertIn("browser-cdp", registry.names())
        self.assertIn("vnc-novnc", registry.names())
        self.assertTrue(registry.get("macos-peekaboo").source_url)
