"""The harness daemon — the state machine that makes witnessing automatic.

States: idle -> witnessing -> (idle_seconds quiet) -> sealing -> idle.

The daemon only RECORDS. Triage runs at seal time as an optional read, so a
broken or missing triage backend never stops a session from being witnessed.
"""
import os
import time
from datetime import datetime, timezone

from .config import Config
from .detector import Detector
from .receipts import Chain, sha256
from .recorder import Recorder
from .triage import classify


def _file_sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Daemon:
    def __init__(self, config: Config):
        self.config = config
        self.detector = Detector(
            config.watch_processes, config.watch_export_dir,
            window_seconds=30.0,
        )
        self.recorder = Recorder(config.capture, config.fps, config.codec)
        self.state = "idle"
        self.session_dir = None
        self.chain = None
        self.last_trigger = 0.0

    def _start_session(self):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.session_dir = os.path.join(self.config.session_dir, ts)
        os.makedirs(self.session_dir, exist_ok=True)
        self.chain = Chain(os.path.join(self.session_dir, "receipts.jsonl"))
        self.chain.append("session_start", {
            "session_id": ts,
            "config": {
                "broker": self.config.broker,
                "capture": self.config.capture,
                "fps": self.config.fps,
            },
            "triggers": self.detector.triggers(),
        })
        self.recorder.start(os.path.join(self.session_dir, "screen.mp4"))
        self.state = "witnessing"
        self.last_trigger = time.time()

    def _seal_session(self):
        self.recorder.stop()
        artifacts = []
        for name in ("screen.mp4",):
            p = os.path.join(self.session_dir, name)
            if os.path.exists(p):
                artifacts.append({"file": name, "sha256": _file_sha256(p)})
        payload = {
            "session_id": os.path.basename(self.session_dir),
            "artifacts": artifacts,
            "duration_seconds": round(time.time() - self.last_trigger, 1),
        }
        # optional triage read — never blocks sealing
        try:
            payload["triage"] = classify({}, self.config.triage)
        except Exception:
            pass
        self.chain.append("session_seal", payload)
        self.state = "idle"
        self.session_dir = None
        self.chain = None

    def tick(self):
        active = self.detector.active()
        now = time.time()
        if self.state == "idle":
            if active:
                self._start_session()
        elif self.state == "witnessing":
            if active:
                self.last_trigger = now
            elif now - self.last_trigger >= self.config.idle_seconds:
                self._seal_session()

    def run(self, poll_seconds: float = 5.0):
        while True:
            self.tick()
            time.sleep(poll_seconds)