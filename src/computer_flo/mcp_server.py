from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from computer_flo.backends.linux import LinuxBackend
from computer_flo.backends.selector import select_backend
from computer_flo.visible import build_visible_env, discover_visible_desktop


def _schema(properties: dict[str, dict], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


class ComputerFloMCPServer:
    """Dependency-light Computer Flo tool registry with MCP-ready contracts.

    The registry stays usable without the external MCP SDK for tests and simple
    CLI calls. The stdio loop below speaks a small JSON-RPC/MCP-compatible
    subset (`tools/list` and `tools/call`) so agents can exercise the contract
    before a full SDK transport is attached.
    """

    def __init__(self, backend: Any | None = None):
        self.backend = backend or LinuxBackend()

    def list_tools(self) -> list[dict[str, Any]]:
        executable = {"execute": {"type": "boolean", "description": "actually execute; false plans only"}}
        return [
            {"name": "computer.observe", "description": "Observe desktop capabilities and browser profile state", "inputSchema": _schema({})},
            {"name": "computer.screenshot", "description": "Capture a desktop screenshot", "inputSchema": _schema({"path": {"type": "string"}, **executable}, ["path"])},
            {"name": "computer.click", "description": "Move mouse and click", "inputSchema": _schema({"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "integer", "default": 1}, **executable}, ["x", "y"])},
            {"name": "computer.type", "description": "Type text", "inputSchema": _schema({"text": {"type": "string"}, **executable}, ["text"])},
            {"name": "computer.hotkey", "description": "Press a key combination", "inputSchema": _schema({"combo": {"type": "string"}, **executable}, ["combo"])},
            {"name": "computer.scroll", "description": "Scroll wheel clicks", "inputSchema": _schema({"clicks": {"type": "integer"}, **executable}, ["clicks"])},
            {"name": "computer.drag", "description": "Drag from one coordinate to another", "inputSchema": _schema({"start_x": {"type": "integer"}, "start_y": {"type": "integer"}, "end_x": {"type": "integer"}, "end_y": {"type": "integer"}, "button": {"type": "integer", "default": 1}, **executable}, ["start_x", "start_y", "end_x", "end_y"])},
            {"name": "computer.window_list", "description": "List visible windows", "inputSchema": _schema({**executable})},
            {"name": "computer.window_focus", "description": "Focus a window id", "inputSchema": _schema({"window_id": {"type": "string"}, **executable}, ["window_id"])},
            {"name": "computer.clipboard_get", "description": "Read clipboard", "inputSchema": _schema({**executable})},
            {"name": "computer.clipboard_set", "description": "Set clipboard", "inputSchema": _schema({"text": {"type": "string"}, **executable}, ["text"])},
            {"name": "computer.browser_state", "description": "Detect local browser profile paths", "inputSchema": _schema({})},
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict:
        args = arguments or {}
        execute = bool(args.get("execute", False))
        if name == "computer.observe":
            return self.backend.observe()
        if name == "computer.screenshot":
            return self.backend.screenshot(str(args.get("path", "/tmp/computer-flo-screenshot.png")), execute=execute)
        if name == "computer.click":
            return self.backend.click(int(args["x"]), int(args["y"]), int(args.get("button", 1)), execute=execute)
        if name == "computer.type":
            return self.backend.type_text(str(args["text"]), execute=execute)
        if name == "computer.hotkey":
            return self.backend.hotkey(str(args["combo"]), execute=execute)
        if name == "computer.scroll":
            return self.backend.scroll(int(args["clicks"]), execute=execute)
        if name == "computer.drag":
            return self.backend.drag(int(args["start_x"]), int(args["start_y"]), int(args["end_x"]), int(args["end_y"]), int(args.get("button", 1)), execute=execute)
        if name == "computer.window_list":
            return self.backend.window_list(execute=execute)
        if name == "computer.window_focus":
            return self.backend.window_focus(str(args["window_id"]), execute=execute)
        if name == "computer.clipboard_get":
            return self.backend.clipboard_get(execute=execute)
        if name == "computer.clipboard_set":
            return self.backend.clipboard_set(str(args["text"]), execute=execute)
        if name == "computer.browser_state":
            return self.backend.browser_state()
        raise ValueError(f"unknown tool: {name}")

    async def handle_jsonrpc(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = request.get("id")
        method = request.get("method")
        try:
            if method in {"initialize", "ping"}:
                result = {"serverInfo": {"name": "computer-flo", "version": "0.4.0"}, "capabilities": {"tools": {}}}
            elif method == "tools/list":
                result = {"tools": self.list_tools()}
            elif method == "tools/call":
                params = request.get("params") or {}
                result = {"content": [{"type": "text", "text": json.dumps(await self.call_tool(params["name"], params.get("arguments") or {}), sort_keys=True)}]}
            else:
                raise ValueError(f"unsupported method: {method}")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:  # noqa: BLE001 - JSON-RPC boundary
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": str(exc)}}


async def run_stdio(server: ComputerFloMCPServer) -> int:
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            return 0
        line = line.strip()
        if not line:
            continue
        response = await server.handle_jsonrpc(json.loads(line))
        print(json.dumps(response, sort_keys=True), flush=True)


def _apply_visible_env() -> dict[str, Any]:
    desktop = discover_visible_desktop()
    visible_env = build_visible_env(desktop)
    os.environ.update({key: value for key, value in visible_env.items() if value is not None})
    return {"display": desktop.display, "user": desktop.user, "xauthority": desktop.xauthority}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="computer-flo-mcp")
    parser.add_argument("--backend", default="linux", choices=["auto", "linux", "x11", "macos", "mac", "darwin", "peekaboo"])
    parser.add_argument("--visible", action="store_true", help="auto-discover visible X/VNC desktop env before serving tools")
    parser.add_argument("--print-visible-env", action="store_true", help="print discovered visible desktop env as JSON and exit")
    parser.add_argument("--list-tools", action="store_true")
    parser.add_argument("--call")
    parser.add_argument("--arguments", default="{}")
    parser.add_argument("--stdio", action="store_true", help="run JSON-RPC stdio transport subset")
    args = parser.parse_args(argv)
    if args.visible or args.print_visible_env:
        visible = _apply_visible_env()
        if args.print_visible_env:
            print(json.dumps(visible, sort_keys=True))
            return 0
    server = ComputerFloMCPServer(backend=select_backend(args.backend))
    if args.stdio:
        return asyncio.run(run_stdio(server))
    if args.list_tools:
        print(json.dumps({"tools": server.list_tools()}, sort_keys=True))
        return 0
    if args.call:
        result = asyncio.run(server.call_tool(args.call, json.loads(args.arguments)))
        print(json.dumps(result, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
