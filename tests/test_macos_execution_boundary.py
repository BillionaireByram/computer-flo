import unittest

from computer_flo.backends.macos import PeekabooBackend


class MacOSExecutionBoundaryTest(unittest.TestCase):
    def test_clipboard_set_passes_stdin_to_runner(self):
        runner = RecordingRunner({"pbcopy"})
        backend = PeekabooBackend(runner=runner)

        result = backend.clipboard_set("proof-token", execute=True)

        self.assertEqual(result["status"], "executed")
        self.assertEqual(runner.calls[0]["argv"], ["pbcopy"])
        self.assertEqual(runner.calls[0]["stdin"], "proof-token")


class RecordingRunner:
    def __init__(self, available=None):
        self.available = set(available or [])
        self.calls = []

    def which(self, name):
        return f"/usr/bin/{name}" if name in self.available else None

    def run(self, argv, stdin=None, env=None):
        self.calls.append({"argv": argv, "stdin": stdin, "env": env})
        return {"exit_code": 0, "stdout": "", "stderr": ""}


if __name__ == "__main__":
    unittest.main()
