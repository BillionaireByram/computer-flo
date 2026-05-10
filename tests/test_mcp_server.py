import asyncio
import os
import unittest
from unittest import mock

from computer_flo.mcp_server import ComputerFloMCPServer, _apply_visible_env
from computer_flo.visible import VisibleDesktop


class ComputerFloMCPServerTest(unittest.TestCase):
    def test_lists_core_computer_tools(self):
        server = ComputerFloMCPServer()

        names = [tool["name"] for tool in server.list_tools()]

        self.assertIn("computer.observe", names)
        self.assertIn("computer.screenshot", names)
        self.assertIn("computer.click", names)
        self.assertIn("computer.type", names)
        self.assertIn("computer.hotkey", names)
        self.assertIn("computer.scroll", names)

    def test_call_click_returns_planned_action(self):
        server = ComputerFloMCPServer()

        result = asyncio.run(server.call_tool("computer.click", {"x": 5, "y": 6}))

        self.assertEqual(result["operation"], "click")
        self.assertEqual(result["status"], "planned")

    def test_apply_visible_env_exports_discovered_display(self):
        with mock.patch(
            "computer_flo.mcp_server.discover_visible_desktop",
            return_value=VisibleDesktop(display=":1", user="hermes", xauthority="/home/hermes/.Xauthority"),
        ):
            with mock.patch.dict(os.environ, {}, clear=True):
                result = _apply_visible_env()

                self.assertEqual(result["display"], ":1")
                self.assertEqual(os.environ["DISPLAY"], ":1")
                self.assertEqual(os.environ["XAUTHORITY"], "/home/hermes/.Xauthority")
