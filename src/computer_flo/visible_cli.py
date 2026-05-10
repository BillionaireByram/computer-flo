from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from computer_flo.visible import build_visible_env, discover_visible_desktop


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="computer-flo-visible")
    parser.add_argument("--print-env", action="store_true", help="print discovered visible desktop env as JSON")
    parser.add_argument("--as-current-user", action="store_true", help="do not sudo to the discovered desktop owner")
    parser.add_argument("computer_flo_args", nargs=argparse.REMAINDER, help="arguments passed to computer-flo CLI")
    args = parser.parse_args(argv)

    desktop = discover_visible_desktop()
    env = build_visible_env(desktop)
    if args.print_env:
        print(json.dumps({"display": desktop.display, "user": desktop.user, "xauthority": desktop.xauthority}, sort_keys=True))
        return 0

    passthrough = list(args.computer_flo_args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    if not passthrough:
        passthrough = ["observe", "--json"]

    cmd = [sys.executable, "-m", "computer_flo.cli", *passthrough]
    current_user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if not args.as_current_user and desktop.user and desktop.user != current_user and current_user == "root":
        sudo_env = [f"DISPLAY={env['DISPLAY']}"]
        if env.get("XAUTHORITY"):
            sudo_env.append(f"XAUTHORITY={env['XAUTHORITY']}")
        sudo_env.append(f"PYTHONPATH={os.environ.get('PYTHONPATH', '/opt/computer-flo/src')}")
        cmd = ["sudo", "-u", desktop.user, "env", *sudo_env, *cmd]
        run_env = None
    else:
        run_env = env

    completed = subprocess.run(cmd, env=run_env, text=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
