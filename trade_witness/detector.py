"""Session detection — figures out when a trading session starts and ends.

Triggers (any one fires -> session starts):
  - a watched process is running (broker app opened)
  - a watched export directory has a fresh file (broker export landed)

Session ends after `idle_seconds` of quiet (no trigger fresh).
"""
import os
import shutil
import subprocess
import time


def _process_running(name: str) -> bool:
    if shutil.which("pgrep"):
        try:
            return subprocess.run(["pgrep", "-f", name],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL).returncode == 0
        except Exception:
            pass
    return False


def _export_dir_fresh(path: str, window: float) -> bool:
    if not path or not os.path.isdir(path):
        return False
    cutoff = time.time() - window
    for entry in os.listdir(path):
        p = os.path.join(path, entry)
        try:
            if os.path.getmtime(p) >= cutoff:
                return True
        except OSError:
            continue
    return False


class Detector:
    def __init__(self, processes: list, export_dir: str, window_seconds: float = 30.0):
        self.processes = processes or []
        self.export_dir = export_dir or ""
        self.window = window_seconds

    def active(self) -> bool:
        """True if any trigger is currently fresh."""
        for name in self.processes:
            if _process_running(name):
                return True
        return _export_dir_fresh(self.export_dir, self.window)

    def triggers(self) -> dict:
        """Which triggers are firing right now (for the receipt payload)."""
        procs = [n for n in self.processes if _process_running(n)]
        export = _export_dir_fresh(self.export_dir, self.window)
        return {"processes": procs, "export_dir_fresh": export}