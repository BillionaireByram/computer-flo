from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterSpec:
    name: str
    purpose: str
    source_url: str
    status: str


class AdapterRegistry:
    def __init__(self, specs: list[AdapterSpec]):
        self._specs = {spec.name: spec for spec in specs}

    @classmethod
    def default(cls) -> "AdapterRegistry":
        return cls([
            AdapterSpec("linux-x11", "Linux visible desktop via xdotool/wmctrl/scrot/AT-SPI", "https://github.com/jordansissel/xdotool", "active"),
            AdapterSpec("macos-peekaboo", "macOS native control through Peekaboo", "https://github.com/openclaw/Peekaboo", "adapter"),
            AdapterSpec("browser-cdp", "Browser DOM/console/profile automation via CDP/Playwright/agent-browser", "https://github.com/microsoft/playwright", "planned"),
            AdapterSpec("vnc-novnc", "Human-watchable remote desktop supervision", "https://github.com/novnc/noVNC", "planned"),
        ])

    def names(self) -> list[str]:
        return sorted(self._specs)

    def get(self, name: str) -> AdapterSpec:
        return self._specs[name]

    def as_dict(self) -> dict:
        return {name: spec.__dict__ for name, spec in self._specs.items()}
