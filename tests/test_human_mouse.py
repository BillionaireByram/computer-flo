import random
import unittest
from unittest.mock import patch

from computer_flo.human_mouse import HumanPathOptions, human_path, validate_coord, MAX_COORD
from computer_flo.backends.linux import LinuxBackend
from computer_flo.backends.macos import PeekabooBackend
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


class HumanMouseTest(unittest.TestCase):
    def test_human_path_has_intermediate_points_and_clamped_bounds(self):
        rng = random.Random(7)
        path = human_path((0, 0), (100, 50), HumanPathOptions(steps=8), rng)
        self.assertGreater(len(path), 2)
        self.assertEqual((path[0][0], path[0][1]), (0, 0))
        self.assertEqual((path[-1][0], path[-1][1]), (100, 50))
        for x, y, dwell in path:
            self.assertTrue(0 <= x <= MAX_COORD)
            self.assertTrue(0 <= y <= MAX_COORD)
            self.assertGreaterEqual(dwell, 1)

    def test_validate_coord_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_coord("x", -1)
        with self.assertRaises(ValueError):
            validate_coord("y", MAX_COORD + 1)

    def test_linux_move_human_like_plans_sequence(self):
        backend = LinuxBackend(runner=FakeRunner({"xdotool"}))
        result = backend.move(100, 40, human_like=True, start_x=0, start_y=0)
        self.assertEqual(result["operation"], "move")
        self.assertEqual(result["status"], "planned")
        self.assertTrue(result["human_like"])
        self.assertIn("commands", result)
        self.assertGreater(len(result["commands"]), 2)

    def test_macos_move_human_like_uses_peekaboo_human_profile(self):
        backend = PeekabooBackend(runner=FakeRunner({"peekaboo"}))
        result = backend.move(100, 40, human_like=True)
        self.assertEqual(result["argv"], ["peekaboo", "move", "100,40", "--profile", "human", "--duration", "450", "--steps", "25"])

    def test_cli_accepts_move_human_like(self):
        with patch("computer_flo.cli.select_backend") as selector, patch("builtins.print"):
            selector.return_value = LinuxBackend(runner=FakeRunner({"xdotool"}))
            code = cli_main(["move", "100", "200", "--human-like", "--start-x", "0", "--start-y", "0", "--json"])
        self.assertEqual(code, 0)

    def test_mcp_lists_computer_move(self):
        server = ComputerFloMCPServer(backend=LinuxBackend(runner=FakeRunner({"xdotool"})))
        tools = {tool["name"]: tool for tool in server.list_tools()}
        self.assertIn("computer.move", tools)
        self.assertEqual(tools["computer.move"]["inputSchema"]["required"], ["x", "y"])


if __name__ == "__main__":
    unittest.main()
