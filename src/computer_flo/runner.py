from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class CommandRunner:
    """Small shell boundary for detection and optional execution."""

    timeout: int = 30

    def which(self, name: str) -> str | None:
        return shutil.which(name)

    def run(self, argv: list[str], stdin: str | None = None, env: dict | None = None) -> dict:
        completed = subprocess.run(
            argv,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
            env=env,
        )
        return {
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
