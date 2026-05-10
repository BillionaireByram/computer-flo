from __future__ import annotations

import argparse
import json
import sys

from computer_flo.backends.selector import select_backend


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="computer-flo")
    parser.add_argument("--backend", default="linux", choices=["auto", "linux", "x11", "macos", "mac", "darwin", "peekaboo"], help="backend to use; default linux")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--json", action="store_true", help="emit JSON")
        p.add_argument("--execute", action="store_true", help="actually execute planned desktop action")

    p = sub.add_parser("observe")
    add_common(p)

    p = sub.add_parser("click")
    p.add_argument("x", type=int)
    p.add_argument("y", type=int)
    p.add_argument("--button", type=int, default=1)
    add_common(p)

    p = sub.add_parser("type")
    p.add_argument("text")
    add_common(p)

    p = sub.add_parser("hotkey")
    p.add_argument("combo")
    add_common(p)

    p = sub.add_parser("scroll")
    p.add_argument("clicks", type=int)
    add_common(p)

    p = sub.add_parser("drag")
    p.add_argument("start_x", type=int)
    p.add_argument("start_y", type=int)
    p.add_argument("end_x", type=int)
    p.add_argument("end_y", type=int)
    p.add_argument("--button", type=int, default=1)
    add_common(p)

    p = sub.add_parser("screenshot")
    p.add_argument("path")
    add_common(p)

    p = sub.add_parser("window-list")
    add_common(p)

    p = sub.add_parser("window-focus")
    p.add_argument("window_id")
    add_common(p)

    p = sub.add_parser("clipboard-get")
    add_common(p)

    p = sub.add_parser("clipboard-set")
    p.add_argument("text")
    add_common(p)

    p = sub.add_parser("browser-state")
    add_common(p)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        backend = select_backend(args.backend)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2

    if args.command == "observe":
        payload = {"ok": True, "operation": "observe", **backend.observe()}
    elif args.command == "click":
        payload = {"ok": True, "operation": "click", "result": backend.click(args.x, args.y, args.button, execute=args.execute)}
    elif args.command == "type":
        payload = {"ok": True, "operation": "type", "result": backend.type_text(args.text, execute=args.execute)}
    elif args.command == "hotkey":
        payload = {"ok": True, "operation": "hotkey", "result": backend.hotkey(args.combo, execute=args.execute)}
    elif args.command == "scroll":
        payload = {"ok": True, "operation": "scroll", "result": backend.scroll(args.clicks, execute=args.execute)}
    elif args.command == "drag":
        payload = {"ok": True, "operation": "drag", "result": backend.drag(args.start_x, args.start_y, args.end_x, args.end_y, args.button, execute=args.execute)}
    elif args.command == "screenshot":
        payload = {"ok": True, "operation": "screenshot", "result": backend.screenshot(args.path, execute=args.execute)}
    elif args.command == "window-list":
        payload = {"ok": True, "operation": "window_list", "result": backend.window_list(execute=args.execute)}
    elif args.command == "window-focus":
        payload = {"ok": True, "operation": "window_focus", "result": backend.window_focus(args.window_id, execute=args.execute)}
    elif args.command == "clipboard-get":
        payload = {"ok": True, "operation": "clipboard_get", "result": backend.clipboard_get(execute=args.execute)}
    elif args.command == "clipboard-set":
        payload = {"ok": True, "operation": "clipboard_set", "result": backend.clipboard_set(args.text, execute=args.execute)}
    elif args.command == "browser-state":
        payload = {"ok": True, "operation": "browser_state", "result": backend.browser_state()}
    else:
        payload = {"ok": False, "error": f"unknown command {args.command}"}

    if getattr(args, "json", False):
        print(json.dumps(payload, sort_keys=True))
    else:
        print(payload)
    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
