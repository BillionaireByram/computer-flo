import asyncio
import json
import os
import unittest
from unittest.mock import patch

from computer_flo.backends.linux import LinuxBackend
from computer_flo.backends.selector import select_backend
from computer_flo.cli import main as cli_main
from computer_flo.mcp_server import ComputerFloMCPServer


class FakeRunner:
    def __init__(self, available=None):
        self.available = set(available or [])
        self.calls = []

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.available else None

    def run(self, argv, stdin=None, env=None):
        self.calls.append({"argv": argv, "stdin": stdin, "env": env})
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}


class V04UpgradeTest(unittest.TestCase):
    def test_linux_click_falls_back_to_ydotool_when_xdotool_missing(self):
        backend = LinuxBackend(runner=FakeRunner({"ydotool"}))

        result = backend.click(12, 34)

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["ydotool", "mousemove", "--absolute", "12", "34", "click", "0xC0"])

    def test_linux_type_falls_back_to_wtype_when_xdotool_missing(self):
        backend = LinuxBackend(runner=FakeRunner({"wtype"}))

        result = backend.type_text("hello")

        self.assertEqual(result["status"], "planned")
        self.assertEqual(result["argv"], ["wtype", "hello"])

    def test_linux_drag_plans_mouse_down_move_up(self):
        backend = LinuxBackend(runner=FakeRunner({"xdotool"}))

        result = backend.drag(1, 2, 3, 4)

        self.assertEqual(result["operation"], "drag")
        self.assertEqual(result["argv"], ["xdotool", "mousemove", "1", "2", "mousedown", "1", "mousemove", "3", "4", "mouseup", "1"])

    def test_backend_selector_auto_uses_macos_when_platform_is_darwin(self):
        with patch("sys.platform", "darwin"):
            backend = select_backend("auto")

        self.assertEqual(backend.capabilities()["backend"], "macos-peekaboo")

    def test_cli_accepts_backend_auto_and_drag(self):
        with patch("computer_flo.cli.select_backend") as selector, patch("builtins.print") as printer:
            selector.return_value = LinuxBackend(runner=FakeRunner({"xdotool"}))

            code = cli_main(["--backend", "auto", "drag", "1", "2", "3", "4", "--json"])

        self.assertEqual(code, 0)
        payload = json.loads(printer.call_args.args[0])
        self.assertEqual(payload["operation"], "drag")
        self.assertEqual(payload["result"]["status"], "planned")

    def test_mcp_schemas_mark_required_fields_and_include_drag(self):
        server = ComputerFloMCPServer()
        tools = {tool["name"]: tool for tool in server.list_tools()}

        self.assertIn("computer.drag", tools)
        self.assertEqual(tools["computer.click"]["inputSchema"]["required"], ["x", "y"])
        self.assertEqual(tools["computer.type"]["inputSchema"]["required"], ["text"])
        self.assertEqual(tools["computer.drag"]["inputSchema"]["required"], ["start_x", "start_y", "end_x", "end_y"])

    def test_mcp_drag_returns_planned_action(self):
        server = ComputerFloMCPServer(backend=LinuxBackend(runner=FakeRunner({"xdotool"})))

        result = asyncio.run(server.call_tool("computer.drag", {"start_x": 1, "start_y": 2, "end_x": 3, "end_y": 4}))

        self.assertEqual(result["operation"], "drag")
        self.assertEqual(result["status"], "planned")


if __name__ == "__main__":
    unittest.main()
