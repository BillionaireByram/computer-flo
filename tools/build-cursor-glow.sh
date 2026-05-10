#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
swiftc tools/cursor_glow.swift -o "${1:-$HOME/.local/bin/computer-flo-cursor-glow}"
chmod +x "${1:-$HOME/.local/bin/computer-flo-cursor-glow}"
