import json
import unittest
from io import StringIO
from unittest.mock import patch

from computer_flo.cli import main


class CliTest(unittest.TestCase):
    def test_observe_json_outputs_capabilities(self):
        out = StringIO()
        with patch("sys.stdout", out):
            code = main(["observe", "--json"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["operation"], "observe")
        self.assertIn("capabilities", payload)

    def test_click_requires_execute_to_run(self):
        out = StringIO()
        with patch("sys.stdout", out):
            code = main(["click", "10", "20", "--json"])

        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["result"]["status"], "planned")
        self.assertEqual(payload["result"]["argv"][:2], ["xdotool", "mousemove"])


if __name__ == "__main__":
    unittest.main()
