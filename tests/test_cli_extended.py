import json
import unittest
from io import StringIO
from unittest.mock import patch

from computer_flo.cli import main


class ExtendedCliTest(unittest.TestCase):
    def test_browser_state_command_outputs_profiles_key(self):
        out = StringIO()
        with patch("sys.stdout", out):
            code = main(["browser-state", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["operation"], "browser_state")
        self.assertIn("profiles", payload["result"])

    def test_window_focus_command_is_planned(self):
        out = StringIO()
        with patch("sys.stdout", out):
            code = main(["window-focus", "0xabc", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["result"]["argv"], ["wmctrl", "-ia", "0xabc"])

    def test_clipboard_set_command_is_planned(self):
        out = StringIO()
        with patch("sys.stdout", out):
            code = main(["clipboard-set", "hello", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["result"]["stdin"], "hello")
