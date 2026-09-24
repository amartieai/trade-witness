"""Configuration for Trade Witness.

Kept in one JSON file so the harness stays stdlib-only (no yaml dependency).
Path: ~/.config/trade-witness/config.json
"""
import json
import os
from dataclasses import dataclass, field, asdict


CONFIG_PATH = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "trade-witness", "config.json",
)


@dataclass
class Config:
    # which broker connector to use ("tradovate" or "csv"); "csv" is the
    # universal fallback that watches a download/export directory.
    broker: str = "csv"

    # screen capture: "full" or "region" (x11grab / gdigrab style args)
    capture: str = "full"

    # fps + codec for the recording
    fps: int = 5
    codec: str = "libx264"

    # where sessions (recordings, receipts, exports) are stored
    session_dir: str = os.path.expanduser("~/.local/share/trade-witness/sessions")

    # detector triggers — process names AND an export directory to watch.
    # session starts when any trigger fires; ends after `idle_seconds` quiet.
    watch_processes: list = field(default_factory=lambda: ["tradovate", "tws", "ibkr"])
    watch_export_dir: str = ""

    idle_seconds: int = 120

    # triage layer. "local" = built-in heuristic (always works).
    # "jev" = JEV decision layer (optional; only used if the user configures it).
    triage: str = "local"

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                data = json.load(f)
            cfg = cls()
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
            return cfg
        return cls()